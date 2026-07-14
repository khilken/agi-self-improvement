from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_setup_hermes_ollama_defaults_are_consistent():
    script = (PROJECT_ROOT / "setup_hermes.sh").read_text()

    assert 'OLLAMA_HOST="${OLLAMA_HOST:-http://192.168.1.111:11434}"' in script
    assert "os.environ.get('OLLAMA_HOST', 'http://192.168.1.111:11434')" in script
    localhost_ollama = "http://" + "127.0.0.1" + ":11434"
    assert localhost_ollama not in script
