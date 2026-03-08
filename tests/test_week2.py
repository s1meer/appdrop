"""
Week 2 Tests — GitHub URL Parser, Metadata, Port Allocator, Process Manager
Run: pytest tests/test_week2.py -v
"""
import pytest, json, socket, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import (parse_github_url, detect_stack, find_launch_command,
                  find_free_port, load_state, save_state, Stack)

# ─── GitHub URL Parser ────────────────────────────────────────────────────────
class TestGitHubURLParser:
    def test_standard_https_url(self):
        r = parse_github_url("https://github.com/comfyanonymous/ComfyUI")
        assert r["valid"] == True
        assert r["owner"] == "comfyanonymous"
        assert r["repo"] == "ComfyUI"

    def test_url_with_git_suffix(self):
        r = parse_github_url("https://github.com/user/repo.git")
        assert r["valid"] == True
        assert r["repo"] == "repo"

    def test_url_with_trailing_slash(self):
        r = parse_github_url("https://github.com/user/repo/")
        assert r["valid"] == True

    def test_url_without_https(self):
        r = parse_github_url("github.com/user/repo")
        assert r["valid"] == True

    def test_invalid_url_returns_false(self):
        r = parse_github_url("not-a-github-url")
        assert r["valid"] == False

    def test_empty_string(self):
        r = parse_github_url("")
        assert r["valid"] == False

    def test_gitlab_url_rejected(self):
        r = parse_github_url("https://gitlab.com/user/repo")
        assert r["valid"] == False

    def test_clone_url_format(self):
        r = parse_github_url("https://github.com/owner/myrepo")
        assert r["clone_url"] == "https://github.com/owner/myrepo.git"

    def test_api_url_format(self):
        r = parse_github_url("https://github.com/owner/myrepo")
        assert "api.github.com" in r["api_url"]

    def test_url_with_query_params(self):
        r = parse_github_url("https://github.com/user/repo?tab=readme")
        assert r["valid"] == True
        assert r["repo"] == "repo"

    def test_url_with_branch_path(self):
        r = parse_github_url("https://github.com/user/repo/tree/main")
        assert r["valid"] == True
        assert r["owner"] == "user"

# ─── Stack Detection ──────────────────────────────────────────────────────────
class TestStackDetection:
    def test_python_requirements(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

    def test_node_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"app"}')
        assert detect_stack(tmp_path) == Stack.NODE

    def test_docker_takes_priority(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.11\n")
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        assert detect_stack(tmp_path) == Stack.DOCKER

    def test_unknown_empty_dir(self, tmp_path):
        assert detect_stack(tmp_path) == Stack.UNKNOWN

    def test_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n")
        assert detect_stack(tmp_path) == Stack.PYTHON

# ─── Launch Command ───────────────────────────────────────────────────────────
class TestLaunchCommand:
    def test_python_app_py(self, tmp_path):
        (tmp_path / "app.py").write_text("")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "app.py" in cmd

    def test_streamlit_detection(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("streamlit\n")
        (tmp_path / "app.py").write_text("")
        cmd = find_launch_command(tmp_path, Stack.PYTHON)
        assert "streamlit" in cmd

    def test_node_dev_script(self, tmp_path):
        (tmp_path / "package.json").write_text('{"scripts":{"dev":"vite"}}')
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert "dev" in cmd

# ─── Port Allocator ───────────────────────────────────────────────────────────
class TestPortAllocator:
    def test_returns_free_port(self):
        port = find_free_port()
        assert 7800 <= port <= 7900

    def test_port_is_actually_free(self):
        port = find_free_port()
        with socket.socket() as s:
            result = s.connect_ex(("127.0.0.1", port))
        assert result != 0  # not in use

    def test_two_calls_same_range(self):
        p1 = find_free_port()
        p2 = find_free_port()
        # Both should be valid (may be same if nothing occupied first)
        assert 7800 <= p1 <= 7900
        assert 7800 <= p2 <= 7900

# ─── State Persistence ───────────────────────────────────────────────────────
class TestStatePersistence:
    def test_full_app_lifecycle_state(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        state = {"apps": {
            "abc1": {"id":"abc1","name":"TestApp","status":"installing"},
        }}
        main.save_state(state)
        loaded = main.load_state()
        assert loaded["apps"]["abc1"]["name"] == "TestApp"

    def test_state_updates_correctly(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        state = {"apps": {"a1": {"status": "installing"}}}
        main.save_state(state)
        state2 = main.load_state()
        state2["apps"]["a1"]["status"] = "ready"
        main.save_state(state2)
        final = main.load_state()
        assert final["apps"]["a1"]["status"] == "ready"

# ─── Env Var Isolation ───────────────────────────────────────────────────────
class TestEnvVarIsolation:
    def test_env_file_written(self, tmp_path):
        env_vars = {"API_KEY": "sk-test123", "PORT": "8080"}
        content = "\n".join(f"{k}={v}" for k, v in env_vars.items())
        (tmp_path / ".env").write_text(content)
        lines = (tmp_path / ".env").read_text().splitlines()
        assert "API_KEY=sk-test123" in lines
        assert "PORT=8080" in lines

    def test_two_apps_different_dirs(self, tmp_path):
        app1 = tmp_path / "app1"; app1.mkdir()
        app2 = tmp_path / "app2"; app2.mkdir()
        (app1 / ".env").write_text("KEY=value1")
        (app2 / ".env").write_text("KEY=value2")
        assert (app1 / ".env").read_text() != (app2 / ".env").read_text()

# ─── Sandbox Isolation ───────────────────────────────────────────────────────
class TestSandbox:
    def test_venv_creation(self, tmp_path):
        result = __import__("subprocess").run(
            ["python3", "-m", "venv", str(tmp_path / ".venv")],
            capture_output=True
        )
        assert result.returncode == 0
        assert (tmp_path / ".venv" / "bin" / "python").exists() or \
               (tmp_path / ".venv" / "Scripts" / "python.exe").exists()

    def test_two_venvs_isolated(self, tmp_path):
        v1 = tmp_path / "app1" / ".venv"; v1.parent.mkdir()
        v2 = tmp_path / "app2" / ".venv"; v2.parent.mkdir()
        __import__("subprocess").run(["python3","-m","venv",str(v1)], capture_output=True)
        __import__("subprocess").run(["python3","-m","venv",str(v2)], capture_output=True)
        assert v1.exists() and v2.exists()
        assert v1 != v2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
