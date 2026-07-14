"""Tests for real, conservative agent behavior."""


from agents.auto_debug_agent import AutoDebugAgent
from agents.coder_agent import CoderAgent
from agents.advanced_coding_agent import AdvancedCodingAgent
from agents.comprehensive_debug_testing_agent import ComprehensiveDebugTestingAgent


def test_auto_debug_reports_real_log_findings(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("INFO ok\nERROR failed\nModuleNotFoundError: missing\n")

    result = AutoDebugAgent().analyze_logs(str(log))
    assert result["files_scanned"] == 1
    assert result["issues_found"] >= 2
    assert result["fixes_applied"] == 0
    assert result["fixes_proposed"]


def test_coder_agent_analysis_is_read_only():
    result = CoderAgent().analyze_request(
        "code",
        {"description": "inspect", "files": ["agents/coder_agent.py", "does_not_exist.py"]},
    )
    assert result["status"] == "analysis_only"
    assert result["files_modified"] == []
    assert result["code_generated"] is None
    assert result["files_inspected"]
    assert result["missing_files"]


def test_advanced_coding_agent_analysis_is_read_only():
    result = AdvancedCodingAgent().inspect({"type": "review", "files": ["agents/advanced_coding_agent.py"]})
    assert result["status"] == "analysis_only"
    assert result["files_modified"] == []
    assert result["tests_written"] == 0
    assert result["files_inspected"]


def test_comprehensive_debug_testing_agent_invokes_real_runner():
    result = ComprehensiveDebugTestingAgent().run_checks("unit")
    assert result["checks"]
    assert result["fixes_applied"] == 0
    assert result["tests_generated"] == 0
    assert result["status"] in {"completed", "failed"}
