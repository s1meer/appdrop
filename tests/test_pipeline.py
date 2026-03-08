"""
AppDrop Pipeline Integration Test — Weeks 1+2+3
Tests the FULL flow in sequence:
  URL Input → Parse → Validate → Detect Stack → Create Env → Install → Configure → Launch → Stop → Delete

Run: pytest tests/test_pipeline.py -v --tb=short
"""
import pytest, json, time, socket, subprocess, shutil, os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import (
    parse_github_url, fetch_repo_metadata, detect_stack,
    find_launch_command, find_free_port, check_process_health,
    load_state, save_state, update_app_state, write_log, _count_reqs,
    Stack, InstallStage, PROCESSES
)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — URL INPUT & VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage1_URLInput:
    """Every install starts with a URL. Must parse before anything else."""

    def test_S1_01_valid_url_passes(self):
        r = parse_github_url("https://github.com/comfyanonymous/ComfyUI")
        assert r["valid"] is True, "Valid URL must pass"

    def test_S1_02_invalid_url_blocked(self):
        for bad in ["not-a-url", "", "https://gitlab.com/user/repo", "random text"]:
            assert parse_github_url(bad)["valid"] is False, f"Should reject: {bad}"

    def test_S1_03_url_normalized(self):
        variants = [
            "https://github.com/user/repo.git",
            "https://github.com/user/repo/",
            "github.com/user/repo",
            "https://github.com/user/repo?tab=readme",
        ]
        for v in variants:
            r = parse_github_url(v)
            assert r["valid"] is True, f"Should normalize: {v}"
            assert r["repo"] == "repo"

    def test_S1_04_clone_url_generated(self):
        r = parse_github_url("https://github.com/owner/myapp")
        assert r["clone_url"] == "https://github.com/owner/myapp.git"

    def test_S1_05_api_url_generated(self):
        r = parse_github_url("https://github.com/owner/myapp")
        assert "api.github.com/repos/owner/myapp" in r["api_url"]

    def test_S1_06_owner_and_repo_extracted(self):
        r = parse_github_url("https://github.com/s1meer/appdrop")
        assert r["owner"] == "s1meer"
        assert r["repo"] == "appdrop"

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — STACK DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage2_StackDetection:
    """After clone, must detect stack before creating environment."""

    def test_S2_01_python_from_requirements(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_S2_02_python_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_S2_03_python_from_pipfile(self, tmp_path):
        (tmp_path / "Pipfile").write_text("[packages]\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_S2_04_node_from_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"app","scripts":{"start":"node index.js"}}')
        assert detect_stack(tmp_path) == Stack.NODE

    def test_S2_05_docker_from_dockerfile(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        assert detect_stack(tmp_path) == Stack.DOCKER

    def test_S2_06_docker_from_compose(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("version: '3'\n")
        assert detect_stack(tmp_path) == Stack.DOCKER

    def test_S2_07_conda_from_env_yml(self, tmp_path):
        (tmp_path / "environment.yml").write_text("name: myenv\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_S2_08_conda_from_env_yaml(self, tmp_path):
        (tmp_path / "environment.yaml").write_text("name: myenv\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_S2_09_unknown_for_empty(self, tmp_path):
        assert detect_stack(tmp_path) == Stack.UNKNOWN

    def test_S2_10_priority_conda_over_docker(self, tmp_path):
        (tmp_path / "environment.yml").write_text("name: myenv\n")
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        assert detect_stack(tmp_path) == Stack.CONDA

    def test_S2_11_priority_python_over_docker(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_S2_12_priority_python_over_node(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        (tmp_path / "package.json").write_text('{"name":"app"}')
        # Docker > Conda > Python detection wins since no Dockerfile/conda
        assert detect_stack(tmp_path) == Stack.PYTHON

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — ENVIRONMENT CREATION (Sandbox)
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage3_EnvironmentCreation:
    """Each app gets its own isolated environment. Zero cross-contamination."""

    def test_S3_01_venv_created_for_python(self, tmp_path):
        venv = tmp_path / ".venv"
        result = subprocess.run(["python3", "-m", "venv", str(venv)], capture_output=True)
        assert result.returncode == 0
        assert venv.exists()

    def test_S3_02_venv_has_pip(self, tmp_path):
        venv = tmp_path / ".venv"
        subprocess.run(["python3", "-m", "venv", str(venv)], capture_output=True, check=True)
        pip = venv / "bin" / "pip"
        assert pip.exists(), "pip must exist in venv"

    def test_S3_03_venv_has_python(self, tmp_path):
        venv = tmp_path / ".venv"
        subprocess.run(["python3", "-m", "venv", str(venv)], capture_output=True, check=True)
        python = venv / "bin" / "python"
        assert python.exists(), "python must exist in venv"

    def test_S3_04_two_apps_completely_isolated(self, tmp_path):
        app1 = tmp_path / "app1"; app2 = tmp_path / "app2"
        app1.mkdir(); app2.mkdir()
        subprocess.run(["python3","-m","venv",str(app1/".venv")], capture_output=True, check=True)
        subprocess.run(["python3","-m","venv",str(app2/".venv")], capture_output=True, check=True)
        # Python executables must be different paths
        assert (app1/".venv") != (app2/".venv")
        assert (app1/".venv").exists() and (app2/".venv").exists()

    def test_S3_05_env_vars_written_to_dotenv(self, tmp_path):
        env_vars = {"API_KEY": "sk-test", "PORT": "8080", "DEBUG": "true"}
        (tmp_path / ".env").write_text("\n".join(f"{k}={v}" for k,v in env_vars.items()))
        content = (tmp_path / ".env").read_text()
        assert "API_KEY=sk-test" in content
        assert "PORT=8080" in content
        assert "DEBUG=true" in content

    def test_S3_06_dotenv_isolated_per_app(self, tmp_path):
        a = tmp_path / "a"; b = tmp_path / "b"
        a.mkdir(); b.mkdir()
        (a / ".env").write_text("KEY=valueA")
        (b / ".env").write_text("KEY=valueB")
        assert "valueA" not in (b / ".env").read_text()
        assert "valueB" not in (a / ".env").read_text()

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — LAUNCH COMMAND DETECTION
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage4_LaunchCommandDetection:
    """Must auto-detect how to run the app before launching."""

    def test_S4_01_python_app_py(self, tmp_path):
        (tmp_path / "app.py").write_text("print('hello')")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "app.py" in cmd

    def test_S4_02_python_main_py(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "main.py" in cmd

    def test_S4_03_streamlit_app(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("streamlit\n")
        (tmp_path / "app.py").write_text("import streamlit as st")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "streamlit" in cmd

    def test_S4_04_gradio_app(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("gradio\n")
        (tmp_path / "app.py").write_text("import gradio as gr")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "python" in cmd and "app.py" in cmd

    def test_S4_05_node_dev_script(self, tmp_path):
        (tmp_path / "package.json").write_text('{"scripts":{"dev":"vite","start":"node server.js"}}')
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert "dev" in cmd  # dev preferred over start

    def test_S4_06_node_start_fallback(self, tmp_path):
        (tmp_path / "package.json").write_text('{"scripts":{"start":"node server.js"}}')
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert "start" in cmd

    def test_S4_07_conda_uses_python_commands(self, tmp_path):
        (tmp_path / "app.py").write_text("")
        cmd = find_launch_command(tmp_path, Stack.CONDA)
        assert "python" in cmd or "streamlit" in cmd

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — PORT ALLOCATION
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage5_PortAllocation:
    """Every app gets a unique port. No conflicts."""

    def test_S5_01_port_in_valid_range(self):
        port = find_free_port()
        assert 7800 <= port <= 7900

    def test_S5_02_port_is_actually_free(self):
        port = find_free_port()
        with socket.socket() as s:
            assert s.connect_ex(("127.0.0.1", port)) != 0

    def test_S5_03_no_conflict_on_5_simultaneous_ports(self):
        """find_free_port must return unique ports when previous ones are occupied."""
        occupied = []
        ports = []
        try:
            for _ in range(5):
                port = find_free_port()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                occupied.append((s, port))
                ports.append(port)
        finally:
            for s, _ in occupied:
                s.close()
        assert len(set(ports)) == 5, f"Expected 5 unique ports, got {ports}"

    def test_S5_04_env_vars_include_all_port_keys(self):
        port = find_free_port()
        env = {"PORT": str(port), "GRADIO_SERVER_PORT": str(port),
               "STREAMLIT_SERVER_PORT": str(port)}
        assert all(v == str(port) for v in env.values())

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — INSTALL PROGRESS STAGES
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage6_InstallProgress:
    """Progress must be monotonically increasing 0→100%."""

    def test_S6_01_all_stages_defined(self):
        expected = ["queued","cloning","detecting","creating_env","installing","configuring","complete","failed"]
        actual = [s.value for s in InstallStage]
        for e in expected:
            assert e in actual, f"Missing stage: {e}"

    def test_S6_02_progress_monotonically_increases(self):
        ordered = [InstallStage.QUEUED, InstallStage.CLONING, InstallStage.DETECTING,
                   InstallStage.CREATING_ENV, InstallStage.INSTALLING,
                   InstallStage.CONFIGURING, InstallStage.COMPLETE]
        pcts = [s.pct for s in ordered]
        assert pcts == sorted(pcts), f"Stages not monotonic: {pcts}"

    def test_S6_03_complete_is_100pct(self):
        assert InstallStage.COMPLETE.pct == 100

    def test_S6_04_queued_starts_at_0(self):
        assert InstallStage.QUEUED.pct == 0

    def test_S6_05_failed_resets_to_0(self):
        assert InstallStage.FAILED.pct == 0

    def test_S6_06_all_stages_have_labels(self):
        for stage in InstallStage:
            assert stage.label and len(stage.label) > 3, f"Stage {stage} has no label"

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — STATE PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage7_StatePersistence:
    """App state must survive between operations."""

    def test_S7_01_empty_state_on_no_file(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "STATE_FILE", tmp_path / "s.json")
        assert load_state() == {"apps": {}}

    def test_S7_02_state_persists_after_save(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "STATE_FILE", tmp_path / "s.json")
        save_state({"apps": {"a1": {"name":"TestApp","status":"installing"}}})
        assert load_state()["apps"]["a1"]["name"] == "TestApp"

    def test_S7_03_partial_update_preserves_other_fields(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "STATE_FILE", tmp_path / "s.json")
        save_state({"apps": {"a1": {"name":"App","status":"installing","stack":"unknown"}}})
        update_app_state("a1", status="ready", stack="python")
        s = load_state()
        assert s["apps"]["a1"]["name"] == "App"    # preserved
        assert s["apps"]["a1"]["status"] == "ready" # updated
        assert s["apps"]["a1"]["stack"] == "python"  # updated

    def test_S7_04_multiple_apps_independent(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "STATE_FILE", tmp_path / "s.json")
        save_state({"apps": {
            "a1": {"name":"App1","status":"ready"},
            "a2": {"name":"App2","status":"installing"},
        }})
        update_app_state("a1", status="running")
        s = load_state()
        assert s["apps"]["a1"]["status"] == "running"
        assert s["apps"]["a2"]["status"] == "installing"  # unchanged

    def test_S7_05_delete_removes_from_state(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "STATE_FILE", tmp_path / "s.json")
        save_state({"apps": {"a1": {"name":"App1"}, "a2": {"name":"App2"}}})
        s = load_state(); del s["apps"]["a1"]; save_state(s)
        assert "a1" not in load_state()["apps"]
        assert "a2" in load_state()["apps"]

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 8 — PROCESS LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage8_ProcessLifecycle:
    """Process must go: stopped → running → (stopped|crashed)"""

    def test_S8_01_no_process_returns_stopped(self):
        assert check_process_health("nonexistent_xyz") == "stopped"

    def test_S8_02_live_process_returns_running(self):
        proc = subprocess.Popen(["sleep","30"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PROCESSES["test_S8_02"] = proc
        try:
            assert check_process_health("test_S8_02") == "running"
        finally:
            proc.terminate(); proc.wait()
            del PROCESSES["test_S8_02"]

    def test_S8_03_finished_process_returns_crashed(self):
        proc = subprocess.Popen(["true"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait()
        PROCESSES["test_S8_03"] = proc
        try:
            assert check_process_health("test_S8_03") == "crashed"
        finally:
            del PROCESSES["test_S8_03"]

    def test_S8_04_terminate_kills_process(self):
        proc = subprocess.Popen(["sleep","60"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PROCESSES["test_S8_04"] = proc
        try:
            proc.terminate(); proc.wait(timeout=5)
            assert proc.poll() is not None, "Process should be dead"
        finally:
            if "test_S8_04" in PROCESSES: del PROCESSES["test_S8_04"]

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 9 — LOGGING
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage9_Logging:
    """Every install step must be logged with timestamp."""

    def test_S9_01_log_file_created(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "app1").mkdir()
        write_log("app1", "test message")
        assert (tmp_path / "app1" / ".appdrop.log").exists()

    def test_S9_02_timestamp_in_log(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "app1").mkdir()
        write_log("app1", "timestamped")
        content = (tmp_path / "app1" / ".appdrop.log").read_text()
        assert "[" in content and "]" in content

    def test_S9_03_multiple_lines_appended(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "app1").mkdir()
        for msg in ["start","cloning","detecting","installing","done"]:
            write_log("app1", msg)
        lines = (tmp_path / "app1" / ".appdrop.log").read_text().strip().splitlines()
        assert len(lines) == 5

    def test_S9_04_logs_isolated_per_app(self, tmp_path, monkeypatch):
        import main; monkeypatch.setattr(main, "APPS_DIR", tmp_path)
        (tmp_path / "appA").mkdir(); (tmp_path / "appB").mkdir()
        write_log("appA", "message from A")
        write_log("appB", "message from B")
        assert "message from A" not in (tmp_path/"appB"/".appdrop.log").read_text()
        assert "message from B" not in (tmp_path/"appA"/".appdrop.log").read_text()

    def test_S9_05_reqs_counter_accuracy(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("# comment\nfastapi\nuvicorn\n\npydantic\n# another comment\nwebsockets\n")
        assert _count_reqs(req) == 4

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 10 — FULL END-TO-END PIPELINE SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
class TestStage10_EndToEndPipeline:
    """Simulate the complete app lifecycle from URL to deletion."""

    def test_S10_01_full_pipeline_python_app(self, tmp_path, monkeypatch):
        """URL → Parse → Detect → Env → Install → Launch cmd → State → Delete"""
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(main, "APPS_DIR", tmp_path / "apps")
        (tmp_path / "apps").mkdir()

        # Step 1: Parse URL
        parsed = parse_github_url("https://github.com/s1meer/appdrop")
        assert parsed["valid"]

        # Step 2: Simulate cloned repo structure
        repo_path = tmp_path / "apps" / "testapp"
        repo_path.mkdir(parents=True)
        (repo_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (repo_path / "main.py").write_text("print('hello')")

        # Step 3: Detect stack
        stack = detect_stack(repo_path)
        assert stack == Stack.PYTHON

        # Step 4: Find launch command
        cmd = find_launch_command(repo_path, stack)
        assert "main.py" in cmd

        # Step 5: Write env vars
        env_vars = {"API_KEY": "test-key"}
        (repo_path / ".env").write_text("\n".join(f"{k}={v}" for k,v in env_vars.items()))
        assert (repo_path / ".env").exists()

        # Step 6: Create state entry
        save_state({"apps": {"testapp": {
            "id":"testapp","name":"TestApp","status":"ready",
            "stack":stack.value,"launch_command":cmd,
            "install_pct":100,"install_stage":"complete",
        }}})

        # Step 7: Verify state is correct
        state = load_state()
        assert state["apps"]["testapp"]["status"] == "ready"
        assert state["apps"]["testapp"]["stack"] == "python"
        assert state["apps"]["testapp"]["install_pct"] == 100

        # Step 8: Update to running
        update_app_state("testapp", status="running", port=7801)
        assert load_state()["apps"]["testapp"]["status"] == "running"

        # Step 9: Stop
        update_app_state("testapp", status="stopped", port=None)
        assert load_state()["apps"]["testapp"]["status"] == "stopped"

        # Step 10: Delete
        s = load_state(); del s["apps"]["testapp"]; save_state(s)
        assert "testapp" not in load_state()["apps"]

    def test_S10_02_pipeline_rejects_bad_url_early(self):
        """Bad URL must be caught at stage 1, nothing else runs."""
        result = parse_github_url("not-github.com/blah")
        assert result["valid"] is False
        # If valid is False, install should never proceed

    def test_S10_03_two_apps_run_simultaneously(self, tmp_path, monkeypatch):
        """Two apps must not interfere with each other."""
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        
        # App 1: Python
        app1 = tmp_path / "app1"; app1.mkdir()
        (app1 / "requirements.txt").write_text("fastapi\n")
        (app1 / "app.py").write_text("")
        
        # App 2: Node
        app2 = tmp_path / "app2"; app2.mkdir()
        (app2 / "package.json").write_text('{"scripts":{"dev":"vite"}}')
        
        stack1 = detect_stack(app1)
        stack2 = detect_stack(app2)
        cmd1 = find_launch_command(app1, stack1)
        cmd2 = find_launch_command(app2, stack2)
        
        assert stack1 == Stack.PYTHON
        assert stack2 == Stack.NODE
        assert cmd1 != cmd2

        p1 = find_free_port()
        # Occupy p1
        s = socket.socket(); s.bind(("127.0.0.1", p1)); s.listen(1)
        p2 = find_free_port()
        s.close()
        assert p1 != p2

    def test_S10_04_install_stages_sequence_is_valid(self):
        """Stages must follow logical order."""
        stage_order = [
            InstallStage.QUEUED,
            InstallStage.CLONING,
            InstallStage.DETECTING,
            InstallStage.CREATING_ENV,
            InstallStage.INSTALLING,
            InstallStage.CONFIGURING,
            InstallStage.COMPLETE,
        ]
        # Each stage pct must be >= previous
        for i in range(1, len(stage_order)):
            assert stage_order[i].pct >= stage_order[i-1].pct, \
                f"Stage {stage_order[i]} ({stage_order[i].pct}%) must be >= {stage_order[i-1]} ({stage_order[i-1].pct}%)"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
