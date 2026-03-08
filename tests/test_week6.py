"""
AppDrop Week 6+7 Tests — Smart Launches, System Info, Compatibility, Auth Stub
"""
import pytest, json, os
from pathlib import Path
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import (app, find_launch_command, get_compat, get_system_info,
                  load_state, save_state, Stack)

client = TestClient(app, follow_redirects=False)


# ── System Info ───────────────────────────────────────────────────────────────
class TestSystemInfo:
    def test_endpoint_returns_200(self):
        r = client.get("/system/info")
        assert r.status_code == 200

    def test_has_cpu_section(self):
        d = client.get("/system/info").json()
        assert "cpu" in d
        assert "cores" in d["cpu"]
        assert "model" in d["cpu"]
        assert "is_apple_silicon" in d["cpu"]

    def test_has_ram(self):
        d = client.get("/system/info").json()
        assert "ram_gb" in d
        assert isinstance(d["ram_gb"], (int, float))
        assert d["ram_gb"] > 0

    def test_has_disk(self):
        d = client.get("/system/info").json()
        assert "disk_free_gb" in d
        assert d["disk_free_gb"] >= 0

    def test_has_gpu_section(self):
        d = client.get("/system/info").json()
        assert "gpu" in d
        assert "has_metal" in d["gpu"]
        assert "has_cuda" in d["gpu"]

    def test_has_platform(self):
        d = client.get("/system/info").json()
        assert d["platform"] in ("mac", "windows", "linux")

    def test_has_recommended_apps(self):
        d = client.get("/system/info").json()
        assert "recommended_apps" in d
        assert isinstance(d["recommended_apps"], list)


# ── Compatibility ─────────────────────────────────────────────────────────────
class TestCompatibility:
    def _sys(self, ram=16, metal=True, cuda=False):
        return {"ram_gb": ram, "gpu": {"has_metal": metal, "has_cuda": cuda}}

    def test_excellent_when_ram_double(self):
        app_data = {"min_ram_gb": 4, "tags": ["llm"]}
        assert get_compat(app_data, self._sys(ram=16)) == "excellent"

    def test_ok_when_ram_just_enough(self):
        app_data = {"min_ram_gb": 8, "tags": ["llm"]}
        assert get_compat(app_data, self._sys(ram=10)) == "ok"

    def test_too_heavy_when_ram_insufficient(self):
        app_data = {"min_ram_gb": 24, "tags": ["image-generation"]}
        assert get_compat(app_data, self._sys(ram=8)) == "too_heavy"

    def test_needs_gpu_for_video_without_gpu(self):
        app_data = {"min_ram_gb": 8, "tags": ["video"]}
        assert get_compat(app_data, self._sys(ram=32, metal=False, cuda=False)) == "needs_gpu"

    def test_excellent_with_image_gen_and_metal(self):
        app_data = {"min_ram_gb": 4, "tags": ["image-generation"]}
        assert get_compat(app_data, self._sys(ram=32, metal=True)) == "excellent"

    def test_too_heavy_takes_priority_over_needs_gpu(self):
        app_data = {"min_ram_gb": 48, "tags": ["video"]}
        assert get_compat(app_data, self._sys(ram=8, metal=False)) == "too_heavy"


# ── Docker Launch Command ─────────────────────────────────────────────────────
class TestDockerLaunchCmd:
    def test_docker_compose_yml(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        cmd = find_launch_command(tmp_path, Stack.DOCKER)
        assert cmd == "docker compose up"

    def test_docker_compose_yaml(self, tmp_path):
        (tmp_path / "docker-compose.yaml").write_text("version: '3'")
        cmd = find_launch_command(tmp_path, Stack.DOCKER)
        assert cmd == "docker compose up"

    def test_docker_no_compose_file(self, tmp_path):
        cmd = find_launch_command(tmp_path, Stack.DOCKER)
        assert cmd == "docker compose up"


# ── Launch Command: Special Node Apps ─────────────────────────────────────────
class TestNodeLaunchCmd:
    def test_flowise_override(self, tmp_path):
        flowise_dir = tmp_path / "flowise"
        flowise_dir.mkdir()
        (flowise_dir / "package.json").write_text(json.dumps({"name":"flowise","scripts":{"start":"node dist/index.js"}}))
        cmd = find_launch_command(flowise_dir, Stack.NODE)
        assert cmd == "npx flowise start"

    def test_jan_override(self, tmp_path):
        jan_dir = tmp_path / "jan"
        jan_dir.mkdir()
        (jan_dir / "package.json").write_text(json.dumps({"name":"jan","scripts":{"dev":"vite"}}))
        cmd = find_launch_command(jan_dir, Stack.NODE)
        assert cmd == "npm run dev"

    def test_node_prefers_dev_script(self, tmp_path):
        (tmp_path / "package.json").write_text(json.dumps({"name":"my-app","scripts":{"dev":"vite","start":"node index.js"}}))
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert cmd == "npm run dev"

    def test_node_fallback_npm_start(self, tmp_path):
        cmd = find_launch_command(tmp_path, Stack.NODE)
        assert cmd == "npm start"


# ── Launch Backfill in list_apps ──────────────────────────────────────────────
class TestLaunchBackfill:
    def test_backfills_empty_launch_command(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "package.json").write_text(json.dumps({"scripts":{"dev":"vite"}}))
        save_state({"apps": {"myapp": {
            "id": "myapp", "status": "ready", "stack": "node",
            "install_path": str(app_dir), "launch_command": None,
            "github_url": "", "error_message": None,
        }}})
        r = client.get("/apps")
        assert r.status_code == 200
        apps = r.json()["apps"]
        assert len(apps) == 1
        assert apps[0]["launch_command"] == "npm run dev"

    def test_skips_apps_without_install_path(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {"orphan": {
            "id": "orphan", "status": "ready", "stack": "python",
            "install_path": str(tmp_path / "missing"), "launch_command": None,
            "github_url": "", "error_message": None,
        }}})
        r = client.get("/apps")
        assert r.status_code == 200
        # Should not crash even with missing path


# ── Auth Stub ─────────────────────────────────────────────────────────────────
class TestAuthStub:
    def test_me_without_token_returns_401(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_with_invalid_token_returns_401(self):
        r = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_github_stub_redirects(self):
        # Without GITHUB_CLIENT_ID, stub mode → redirect to /?token=...
        env_backup = os.environ.pop("GITHUB_CLIENT_ID", None)
        try:
            r = client.get("/auth/github")
            assert r.status_code in (302, 307)
            location = r.headers.get("location","")
            assert "token=" in location
        finally:
            if env_backup:
                os.environ["GITHUB_CLIENT_ID"] = env_backup

    def test_google_stub_redirects(self):
        env_backup = os.environ.pop("GOOGLE_CLIENT_ID", None)
        try:
            r = client.get("/auth/google")
            assert r.status_code in (302, 307)
            location = r.headers.get("location","")
            assert "token=" in location
        finally:
            if env_backup:
                os.environ["GOOGLE_CLIENT_ID"] = env_backup

    def test_logout_returns_ok(self):
        r = client.post("/auth/logout")
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ── Registry Compatibility ────────────────────────────────────────────────────
class TestRegistryCompat:
    def test_registry_includes_compatibility_field(self):
        r = client.get("/registry")
        assert r.status_code == 200
        apps = r.json()["apps"]
        assert len(apps) > 0
        for a in apps:
            assert "compatibility" in a, f"Missing compatibility in {a.get('id')}"

    def test_compatibility_values_are_valid(self):
        apps = client.get("/registry").json()["apps"]
        valid = {"excellent", "ok", "needs_gpu", "too_heavy"}
        for a in apps:
            assert a["compatibility"] in valid, f"{a['id']}: {a['compatibility']}"

    def test_registry_has_28_apps(self):
        apps = client.get("/registry").json()["apps"]
        assert len(apps) >= 28
