"""
Proposal Application & Rollback Engine
======================================

Applies full-file replacements or unified diffs with backups and rollback.
"""

from pathlib import Path
from datetime import datetime
from typing import Tuple
import logging
import shutil
import subprocess
import tempfile

from tracing.proposal import ImprovementProposal, ProposalType
from tracing.history import ImprovementHistory, HistoryEvent, HistoryEventType

logger = logging.getLogger("ProposalApplicator")


class ProposalApplicator:
    def __init__(self, backup_dir: str = "logs/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.history = ImprovementHistory()

    def apply(self, proposal: ImprovementProposal, dry_run: bool = False) -> Tuple[bool, str]:
        if proposal.type not in [ProposalType.CODE_EDIT, ProposalType.PROMPT_CHANGE]:
            self.history.record(HistoryEvent(
                event_type=HistoryEventType.APPLIED,
                proposal_id=proposal.id,
                actor="applicator",
                details={"note": "Non-code proposal recorded"},
            ))
            return True, "Non-code proposal recorded"

        if not proposal.target_file or not proposal.diff:
            return False, "Missing target_file or diff"

        target = Path(proposal.target_file)
        if not target.exists():
            return False, f"Target file does not exist: {target}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = str(target).replace("/", "__")
        backup_path = self.backup_dir / f"{safe_name}.{timestamp}.bak"

        if dry_run:
            if self._looks_like_unified_diff(proposal.diff):
                return self._check_unified_diff(proposal.diff, cwd=target.parent)
            return True, "Dry run successful (full-file replacement)"

        shutil.copy2(target, backup_path)

        try:
            if self._looks_like_unified_diff(proposal.diff):
                ok, msg = self._apply_unified_diff(proposal.diff, cwd=target.parent)
            else:
                target.write_text(proposal.diff)
                ok, msg = True, f"Replaced full file: {target}"

            if ok:
                self.history.record(HistoryEvent(
                    event_type=HistoryEventType.APPLIED,
                    proposal_id=proposal.id,
                    actor="applicator",
                    details={"backup": str(backup_path), "target": str(target), "message": msg},
                ))
                return True, msg

            shutil.copy2(backup_path, target)
            return False, f"Failed to apply change; rolled back. {msg}"

        except Exception as e:
            shutil.copy2(backup_path, target)
            logger.exception("Error applying %s", proposal.id)
            return False, f"Error: {e}; rolled back"

    def _looks_like_unified_diff(self, diff: str) -> bool:
        stripped = diff.lstrip()
        return stripped.startswith("--- ") and "\n+++ " in stripped and "\n@@" in stripped

    def _check_unified_diff(self, diff: str, cwd: Path) -> Tuple[bool, str]:
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(diff)
            patch_path = f.name
        try:
            result = subprocess.run(
                ["git", "apply", "--check", "--unsafe-paths", patch_path],
                cwd=str(cwd),
                text=True,
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, "Unified diff dry-run successful"
            return False, (result.stderr or result.stdout or "git apply --check failed").strip()
        finally:
            Path(patch_path).unlink(missing_ok=True)

    def _apply_unified_diff(self, diff: str, cwd: Path) -> Tuple[bool, str]:
        ok, msg = self._check_unified_diff(diff, cwd=cwd)
        if not ok:
            return False, msg
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(diff)
            patch_path = f.name
        try:
            result = subprocess.run(
                ["git", "apply", "--unsafe-paths", patch_path],
                cwd=str(cwd),
                text=True,
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, "Unified diff applied"
            return False, (result.stderr or result.stdout or "git apply failed").strip()
        finally:
            Path(patch_path).unlink(missing_ok=True)

    def rollback(self, proposal_id: str, backup_path: str, target_path: str | None = None) -> bool:
        backup = Path(backup_path)
        if not backup.exists():
            return False

        if target_path is None:
            logger.error("rollback requires target_path for safe restoration")
            return False

        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)

        self.history.record(HistoryEvent(
            event_type=HistoryEventType.ROLLED_BACK,
            proposal_id=proposal_id,
            actor="applicator",
            details={"backup": str(backup), "target": str(target)},
        ))
        return True
