#!/usr/bin/env python3
"""YouTube subscription digest cron script.

This version is safe for Hermes cron: if OAuth has not been completed it fails
quickly with an actionable message instead of opening a browser and hanging
until the cron script timeout. Secrets and OAuth tokens live outside git in the
runtime script directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
DEFAULT_MAX_VIDEOS_PER_CHANNEL = 5
DEFAULT_MAX_TOTAL_VIDEOS = 25


def _load_google_deps() -> tuple[Any, Any, Any, Any, Any]:
    """Import Google libraries lazily so project import checks still pass.

    The cron host owns these optional dependencies. A developer running the
    project test suite should not fail import-all simply because YouTube OAuth
    support is not installed in the project venv.
    """

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "YouTube digest dependencies are missing. Install google-auth, "
            "google-auth-oauthlib, and google-api-python-client in the cron "
            "environment."
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, HttpError


def is_noninteractive() -> bool:
    return not sys.stdin.isatty() or bool(os.environ.get("HERMES_CRON_JOB_ID"))


def get_last_scan_time(path: Path) -> datetime:
    if path.exists():
        try:
            return datetime.fromisoformat(path.read_text().strip())
        except Exception:
            pass
    return datetime.now(timezone.utc) - timedelta(days=1)


def update_last_scan_time(path: Path) -> str:
    now = datetime.now(timezone.utc).isoformat()
    path.write_text(now)
    return now


def get_youtube_service(script_dir: Path):
    credentials_file = script_dir / "credentials.json"
    token_file = script_dir / "token.json"
    if not token_file.exists():
        if not credentials_file.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {credentials_file}. "
                "Download it from Google Cloud Console and place it next to this script."
            )
        if is_noninteractive():
            raise RuntimeError(
                "YouTube OAuth token.json is missing or invalid. Run this script once "
                "from an interactive terminal to complete Google OAuth consent; cron "
                "can then refresh and run non-interactively."
            )

    Request, Credentials, InstalledAppFlow, build, _HttpError = _load_google_deps()
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_file}. "
                    "Download it from Google Cloud Console and place it next to this script."
                )
            if is_noninteractive():
                raise RuntimeError(
                    "YouTube OAuth token.json is missing or invalid. Run this script once "
                    "from an interactive terminal to complete Google OAuth consent; cron "
                    "can then refresh and run non-interactively."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def oauth_status(script_dir: Path) -> dict[str, Any]:
    """Return non-secret OAuth readiness state without opening a browser."""
    credentials_file = script_dir / "credentials.json"
    token_file = script_dir / "token.json"
    status: dict[str, Any] = {
        "ok": credentials_file.exists() and token_file.exists(),
        "credentials_path": str(credentials_file),
        "credentials_present": credentials_file.exists(),
        "token_path": str(token_file),
        "token_present": token_file.exists(),
        "action_required": None,
    }
    if not status["credentials_present"]:
        status["action_required"] = "Place Google OAuth credentials.json next to scripts/youtube_digest.py or pass --script-dir."
    elif not status["token_present"]:
        status["action_required"] = "Run scripts/youtube_digest.py once from an interactive terminal to complete browser consent."
    return status


def get_subscribed_channels(youtube) -> list[tuple[str, str]]:
    channels: list[tuple[str, str]] = []
    request = youtube.subscriptions().list(part="snippet", mine=True, maxResults=50)
    while request:
        response = request.execute()
        for item in response.get("items", []):
            snippet = item["snippet"]
            channels.append((snippet["resourceId"]["channelId"], snippet["title"]))
        request = youtube.subscriptions().list_next(request, response)
    return channels


def get_channel_uploads_playlist(youtube, channel_id: str) -> str | None:
    _Request, _Credentials, _InstalledAppFlow, _build, HttpError = _load_google_deps()
    try:
        response = youtube.channels().list(part="contentDetails", id=channel_id).execute()
        items = response.get("items", [])
        if items:
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except HttpError:
        return None
    return None


def get_new_videos_from_playlist(
    youtube,
    playlist_id: str,
    published_after: datetime,
    max_videos_per_channel: int,
) -> list[dict[str, str]]:
    _Request, _Credentials, _InstalledAppFlow, _build, HttpError = _load_google_deps()
    videos: list[dict[str, str]] = []
    request = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=10)
    while request and len(videos) < max_videos_per_channel:
        try:
            response = request.execute()
            for item in response.get("items", []):
                snippet = item["snippet"]
                published_str = snippet["publishedAt"]
                published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                if published > published_after:
                    video_id = snippet["resourceId"]["videoId"]
                    videos.append(
                        {
                            "video_id": video_id,
                            "title": snippet["title"],
                            "channel": snippet["channelTitle"],
                            "published": published_str,
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                        }
                    )
            request = youtube.playlistItems().list_next(request, response)
        except HttpError:
            break
    return videos


def build_summary(new_videos: list[dict[str, str]], last_scan: datetime, max_total_videos: int) -> str:
    if not new_videos:
        return (
            "YouTube Subscription Digest\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Last scan: {last_scan}\n\n"
            "No new videos found since the last scan.\n"
        )

    lines = [
        "YouTube Subscription Digest",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Last scan: {last_scan}",
        f"New videos found: {len(new_videos)}",
        "",
    ]
    for video in new_videos[:max_total_videos]:
        lines.extend(
            [
                f"• {video['title']}",
                f"  Channel: {video['channel']}",
                f"  Published: {video['published']}",
                f"  {video['url']}",
                "",
            ]
        )
    if len(new_videos) > max_total_videos:
        lines.append(f"... and {len(new_videos) - max_total_videos} more videos.")
    return "\n".join(lines)


def run_digest(script_dir: Path, max_videos_per_channel: int, max_total_videos: int) -> str:
    last_scan_file = script_dir / "last_scan.txt"
    output_file = script_dir / "youtube_digest_output.txt"
    last_scan = get_last_scan_time(last_scan_file)
    youtube = get_youtube_service(script_dir)
    subscriptions = get_subscribed_channels(youtube)

    all_new_videos: list[dict[str, str]] = []
    for channel_id, _channel_title in subscriptions:
        uploads_playlist = get_channel_uploads_playlist(youtube, channel_id)
        if not uploads_playlist:
            continue
        all_new_videos.extend(
            get_new_videos_from_playlist(youtube, uploads_playlist, last_scan, max_videos_per_channel)
        )

    all_new_videos.sort(key=lambda item: item["published"], reverse=True)
    summary = build_summary(all_new_videos, last_scan, max_total_videos)
    output_file.write_text(summary)
    update_last_scan_time(last_scan_file)
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a YouTube subscription digest")
    parser.add_argument(
        "--script-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing credentials.json/token.json and output files",
    )
    parser.add_argument("--max-videos-per-channel", type=int, default=DEFAULT_MAX_VIDEOS_PER_CHANNEL)
    parser.add_argument("--max-total-videos", type=int, default=DEFAULT_MAX_TOTAL_VIDEOS)
    parser.add_argument("--check-oauth", action="store_true", help="Check OAuth file readiness without opening a browser")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    script_dir = args.script_dir.expanduser().resolve()
    if args.check_oauth:
        status = oauth_status(script_dir)
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0 if status["ok"] else 1
    print("Starting YouTube Subscription Digest...")
    print(f"Script dir: {script_dir}")
    try:
        summary = run_digest(script_dir, args.max_videos_per_channel, args.max_total_videos)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    print("=== YOUTUBE DIGEST SUMMARY ===")
    print(summary)
    print("=== END SUMMARY ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
