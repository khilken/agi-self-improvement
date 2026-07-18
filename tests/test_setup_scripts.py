from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_setup_hermes_ollama_defaults_are_consistent():
    script = (PROJECT_ROOT / "setup_hermes.sh").read_text()

    assert 'OLLAMA_HOST="${OLLAMA_HOST:-http://192.168.1.111:11434}"' in script
    assert "os.environ.get('OLLAMA_HOST', 'http://192.168.1.111:11434')" in script
    assert 'HERMES_DEFAULT_MODEL="${HERMES_DEFAULT_MODEL:-qwen3.6:27b}"' in script
    localhost_ollama = "http://" + "127.0.0.1" + ":11434"
    assert localhost_ollama not in script


def test_launch_scripts_use_available_default_model():
    expected = 'HERMES_DEFAULT_MODEL="${HERMES_DEFAULT_MODEL:-qwen3.6:27b}"'
    stale_model = "qwen2" + ".5:32b"

    for script_name in ["start_hermes.sh", "soft_start_hermes.sh", "setup_hermes.sh"]:
        script = (PROJECT_ROOT / script_name).read_text()
        assert expected in script
        assert stale_model not in script
