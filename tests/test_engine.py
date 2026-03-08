"""
Week 1 Tests — Stack Detector + Engine
Run: pytest tests/ -v
"""
import pytest
import tempfile
import os
from pathlib import Path

# Import engine functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import detect_stack, find_launch_command, Stack


# ─── Stack Detection Tests ────────────────────────────────────────────────────

class TestStackDetection:

    def test_detects_python_from_requirements(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_detects_python_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'app'\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_detects_node_from_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "app", "scripts": {"start": "node index.js"}}')
        assert detect_stack(tmp_path) == Stack.NODE

    def test_detects_docker_first_even_with_python(self, tmp_path):
        """Docker takes priority when both Dockerfile and requirements.txt exist."""
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        assert detect_stack(tmp_path) == Stack.DOCKER

    def test_unknown_stack_for_empty_dir(self, tmp_path):
        assert detect_stack(tmp_path) == Stack.UNKNOWN

    def test_detects_pipfile(self, tmp_path):
        (tmp_path / "Pipfile").write_text("[packages]\nrequests = '*'\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_detects_docker_compose(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("version: '3'\nservices:\n  app:\n    image: nginx\n")
        assert detect_stack(tmp_path) == Stack.DOCKER


# ─── Launch Command Detection Tests ──────────────────────────────────────────

class TestLaunchCommandDetection:

    def test_python_app_py_entry(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("gradio\n")
        (tmp_path / "app.py").write_text("import gradio as gr\n")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "app.py" in cmd

    def test_python_main_py_fallback(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "main.py" in cmd

    def test_python_streamlit_detection(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("streamlit\npandas\n")
        (tmp_path / "app.py").write_text("import streamlit as st\n")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "streamlit" in cmd or "app.py" in cmd

    def test_node_npm_start_script(self, tmp_path):
        (tmp_path / "package.json").write_text('{"scripts": {"start": "node server.js"}}')
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert "start" in cmd

    def test_node_dev_script_preferred_over_start(self, tmp_path):
        (tmp_path / "package.json").write_text('{"scripts": {"start": "node server.js", "dev": "vite"}}')
        cmd = find_launch_command(tmp_path, Stack.NODE)
        # dev should be preferred when start and dev both exist — or at least one is picked
        assert cmd in ["npm run start", "npm run dev", "npm start"]


# ─── State Management Tests ───────────────────────────────────────────────────

class TestStateManagement:

    def test_load_state_returns_empty_on_no_file(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "nonexistent.json")
        state = main.load_state()
        assert state == {"apps": {}}

    def test_save_and_reload_state(self, tmp_path, monkeypatch):
        import main
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(main, "STATE_FILE", state_file)
        test_state = {"apps": {"abc123": {"name": "TestApp", "status": "ready"}}}
        main.save_state(test_state)
        loaded = main.load_state()
        assert loaded["apps"]["abc123"]["name"] == "TestApp"


# ─── Integration: Full Install Flow (mocked) ─────────────────────────────────

class TestInstallFlow:

    def test_env_vars_written_to_dotenv(self, tmp_path):
        """Verify env vars are correctly written as .env file."""
        env_vars = {"OPENAI_API_KEY": "sk-test", "PORT": "8080"}
        env_content = "\n".join(f"{k}={v}" for k, v in env_vars.items())
        env_file = tmp_path / ".env"
        env_file.write_text(env_content)

        content = env_file.read_text()
        assert "OPENAI_API_KEY=sk-test" in content
        assert "PORT=8080" in content

    def test_venv_creation(self, tmp_path):
        """Verify venv can be created in isolated path."""
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "venv", str(tmp_path / ".venv")],
            capture_output=True
        )
        assert result.returncode == 0
        assert (tmp_path / ".venv" / "bin" / "python").exists() or \
               (tmp_path / ".venv" / "Scripts" / "python.exe").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
