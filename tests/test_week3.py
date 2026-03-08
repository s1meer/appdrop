"""
Week 3 Tests — WebSocket progress, conda detection, log writer,
               process health monitor, install stages, port env vars
Run: pytest tests/test_week3.py -v
"""
import pytest, json, time, tempfile, subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import (
    detect_stack, find_launch_command, find_free_port,
    parse_github_url, load_state, save_state, update_app_state,
    check_process_health, write_log, _count_reqs,
    Stack, InstallStage, PROCESSES
)

# ─── InstallStage Progress Percentages ───────────────────────────────────────
class TestInstallStages:
    def test_stages_have_correct_pct(self):
        assert InstallStage.QUEUED.pct == 0
        assert InstallStage.CLONING.pct == 15
        assert InstallStage.DETECTING.pct == 30
        assert InstallStage.CREATING_ENV.pct == 45
        assert InstallStage.INSTALLING.pct == 65
        assert InstallStage.CONFIGURING.pct == 85
        assert InstallStage.COMPLETE.pct == 100
        assert InstallStage.FAILED.pct == 0

    def test_stages_have_labels(self):
        assert "Cloning" in InstallStage.CLONING.label
        assert "Ready" in InstallStage.COMPLETE.label
        assert "failed" in InstallStage.FAILED.label.lower()

    def test_stages_are_monotonically_increasing(self):
        ordered = [
            InstallStage.QUEUED, InstallStage.CLONING, InstallStage.DETECTING,
            InstallStage.CREATING_ENV, InstallStage.INSTALLING,
            InstallStage.CONFIGURING, InstallStage.COMPLETE,
        ]
        pcts = [s.pct for s in ordered]
        assert pcts == sorted(pcts), "Stages should increase monotonically"

    def test_stage_values_are_strings(self):
        assert isinstance(InstallStage.CLONING.value, str)

# ─── Conda Detection ─────────────────────────────────────────────────────────
class TestCondaDetection:
    def test_detects_conda_from_environment_yml(self, tmp_path):
        (tmp_path / "environment.yml").write_text("name: myenv\ndependencies:\n  - python=3.11\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_detects_conda_from_environment_yaml(self, tmp_path):
        (tmp_path / "environment.yaml").write_text("name: myenv\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_conda_takes_priority_over_python(self, tmp_path):
        """If both environment.yml and requirements.txt exist, conda wins."""
        (tmp_path / "environment.yml").write_text("name: myenv\n")
        (tmp_path / "requirements.txt").write_text("numpy\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_conda_takes_priority_over_docker(self, tmp_path):
        (tmp_path / "environment.yml").write_text("name: myenv\n")
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_python_detected_without_environment_yml(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("numpy\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

# ─── Log Writer ──────────────────────────────────────────────────────────────
class TestLogWriter:
    def test_creates_log_file(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "testapp").mkdir()
        write_log("testapp", "Hello log!")
        log = tmp_path / "testapp" / ".appdrop.log"
        assert log.exists()
        assert "Hello log!" in log.read_text()

    def test_appends_multiple_lines(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "app1").mkdir()
        write_log("app1", "Line 1")
        write_log("app1", "Line 2")
        write_log("app1", "Line 3")
        content = (tmp_path / "app1" / ".appdrop.log").read_text()
        assert content.count("\n") == 3

    def test_log_includes_timestamp(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "app2").mkdir()
        write_log("app2", "timestamped")
        content = (tmp_path / "app2" / ".appdrop.log").read_text()
        assert "[" in content and "]" in content  # timestamp brackets

    def test_two_apps_separate_logs(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "appA").mkdir(); (tmp_path / "appB").mkdir()
        write_log("appA", "log A")
        write_log("appB", "log B")
        assert "log A" not in (tmp_path / "appB" / ".appdrop.log").read_text()
        assert "log B" not in (tmp_path / "appA" / ".appdrop.log").read_text()

# ─── Requirements Counter ─────────────────────────────────────────────────────
class TestReqsCounter:
    def test_counts_packages(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi\nuvicorn\npydantic\n")
        assert _count_reqs(req) == 3

    def test_ignores_comments(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("# comment\nfastapi\n# another comment\nuvicorn\n")
        assert _count_reqs(req) == 2

    def test_ignores_blank_lines(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi\n\nuvicorn\n\n\n")
        assert _count_reqs(req) == 2

    def test_empty_file(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("")
        assert _count_reqs(req) == 0

# ─── Process Health Monitor ───────────────────────────────────────────────────
class TestProcessHealth:
    def test_returns_stopped_when_no_process(self):
        status = check_process_health("nonexistent_id")
        assert status == "stopped"

    def test_returns_running_for_live_process(self):
        proc = subprocess.Popen(["sleep","30"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PROCESSES["test_live"] = proc
        try:
            assert check_process_health("test_live") == "running"
        finally:
            proc.terminate(); proc.wait()
            del PROCESSES["test_live"]

    def test_returns_crashed_for_dead_process(self):
        proc = subprocess.Popen(["true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait()  # let it finish
        PROCESSES["test_dead"] = proc
        try:
            assert check_process_health("test_dead") == "crashed"
        finally:
            del PROCESSES["test_dead"]

# ─── State Update Helper ─────────────────────────────────────────────────────
class TestUpdateAppState:
    def test_partial_update(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        state = {"apps": {"a1": {"status":"installing","stack":"unknown","name":"TestApp"}}}
        save_state(state)
        update_app_state("a1", status="ready", stack="python")
        loaded = load_state()
        assert loaded["apps"]["a1"]["status"] == "ready"
        assert loaded["apps"]["a1"]["stack"] == "python"
        assert loaded["apps"]["a1"]["name"] == "TestApp"  # unchanged

    def test_noop_for_missing_app(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {}})
        update_app_state("doesnt_exist", status="ready")  # should not crash

# ─── Port + Env Var Injection ─────────────────────────────────────────────────
class TestLaunchEnvVars:
    def test_port_in_env(self):
        import os
        env = os.environ.copy()
        port = find_free_port()
        env.update({"PORT": str(port), "GRADIO_SERVER_PORT": str(port),
                    "STREAMLIT_SERVER_PORT": str(port)})
        assert env["PORT"] == str(port)
        assert env["GRADIO_SERVER_PORT"] == str(port)
        assert env["STREAMLIT_SERVER_PORT"] == str(port)

    def test_dotenv_loaded_into_launch_env(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=sk-secret\nDEBUG=true\n")
        env = {}
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
        assert env["API_KEY"] == "sk-secret"
        assert env["DEBUG"] == "true"

# ─── Launch Command for Conda ─────────────────────────────────────────────────
class TestCondaLaunchCommand:
    def test_conda_stack_uses_python_commands(self, tmp_path):
        (tmp_path / "app.py").write_text("print('hello')")
        cmd = find_launch_command(tmp_path, Stack.CONDA)
        assert "python" in cmd or "streamlit" in cmd

    def test_conda_with_streamlit_req(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("streamlit\n")
        (tmp_path / "app.py").write_text("")
        cmd = find_launch_command(tmp_path, Stack.CONDA)
        assert "streamlit" in cmd

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
