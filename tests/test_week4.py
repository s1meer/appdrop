"""
AppDrop Week 4 Tests — App Store Registry + 1-Click Update
"""
import pytest, json, time
from pathlib import Path
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
from main import app, REGISTRY_DIR, load_state, save_state

client = TestClient(app)

# ── Registry browse ───────────────────────────────────────────────────────────
class TestRegistryBrowse:
    def test_get_all_apps(self):
        r = client.get("/registry")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] >= 10
        assert len(d["apps"]) >= 10

    def test_apps_have_required_fields(self):
        apps = client.get("/registry").json()["apps"]
        for a in apps:
            for field in ["id","name","description","github_url","stack","tags"]:
                assert field in a, f"Missing field '{field}' in {a.get('id')}"

    def test_filter_by_tag(self):
        r = client.get("/registry?tag=ai")
        assert r.status_code == 200
        apps = r.json()["apps"]
        assert len(apps) >= 3
        for a in apps:
            assert "ai" in [t.lower() for t in a["tags"]]

    def test_filter_by_stack_python(self):
        apps = client.get("/registry?stack=python").json()["apps"]
        assert len(apps) >= 3
        for a in apps:
            assert a["stack"] == "python"

    def test_filter_by_stack_node(self):
        apps = client.get("/registry?stack=node").json()["apps"]
        assert len(apps) >= 2
        for a in apps:
            assert a["stack"] == "node"

    def test_search_by_name(self):
        apps = client.get("/registry?q=whisper").json()["apps"]
        assert len(apps) >= 1
        assert any("whisper" in a["name"].lower() or "whisper" in a["description"].lower()
                   for a in apps)

    def test_search_case_insensitive(self):
        apps_lower = client.get("/registry?q=comfy").json()["apps"]
        apps_upper = client.get("/registry?q=COMFY").json()["apps"]
        assert len(apps_lower) == len(apps_upper)

    def test_empty_search_returns_nothing(self):
        apps = client.get("/registry?q=zzznomatch999xyz").json()["apps"]
        assert len(apps) == 0

class TestRegistryGetSingle:
    def test_get_known_app(self):
        r = client.get("/registry/comfyui")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == "comfyui"
        assert "ComfyUI" in d["name"]

    def test_get_unknown_app_404(self):
        r = client.get("/registry/nonexistent-app-xyz")
        assert r.status_code == 404

    def test_app_has_installed_field(self):
        d = client.get("/registry/comfyui").json()
        assert "installed" in d
        assert isinstance(d["installed"], bool)

    def test_installed_false_when_not_installed(self):
        d = client.get("/registry/comfyui").json()
        # Not installed in test env
        assert d["installed"] is False

class TestRegistrySubmit:
    def test_submit_valid_app(self):
        r = client.post("/registry/submit", json={
            "github_url": "https://github.com/testuser/my-cool-app",
            "name": "My Cool App",
            "description": "A test app submission",
            "stack": "python",
            "tags": ["ai","test"],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["submitted"] is True
        assert d["status"] == "pending_review"
        assert d["app_id"] == "my-cool-app"

    def test_submit_invalid_url_rejected(self):
        r = client.post("/registry/submit", json={
            "github_url": "not-a-url",
            "name": "Bad App",
        })
        assert r.status_code == 400

    def test_submit_duplicate_rejected(self):
        # comfyui already exists in registry
        r = client.post("/registry/submit", json={
            "github_url": "https://github.com/comfyanonymous/ComfyUI",
            "name": "ComfyUI Duplicate",
        })
        assert r.status_code == 409

    def test_submission_saved_as_pending(self):
        client.post("/registry/submit", json={
            "github_url": "https://github.com/testuser/another-app",
            "name": "Another App",
            "stack": "node",
        })
        pending = REGISTRY_DIR.parent / "pending" / "another-app.json"
        assert pending.exists()
        d = json.loads(pending.read_text())
        assert d["status"] == "pending_review"
        assert d["verified"] is False

class TestUpdateCheck:
    def test_update_check_missing_app_404(self):
        r = client.get("/apps/nonexistent/update-check")
        assert r.status_code == 404

    def test_update_check_missing_files(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {"app1": {
            "id":"app1","status":"ready",
            "install_path": str(tmp_path / "missing_dir")
        }}})
        r = client.get("/apps/app1/update-check")
        assert r.status_code == 200
        assert r.json()["update_available"] is False

class TestOneClickUpdate:
    def test_update_nonexistent_app_404(self):
        r = client.post("/apps/nonexistent/update")
        assert r.status_code == 404

    def test_update_running_app_rejected(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {"app1": {
            "id":"app1","status":"running",
            "install_path": str(tmp_path / "app1")
        }}})
        r = client.post("/apps/app1/update")
        assert r.status_code == 400
        assert "Stop" in r.json()["detail"]

    def test_update_missing_files_rejected(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {"app1": {
            "id":"app1","status":"ready","stack":"python",
            "install_path": str(tmp_path / "missing")
        }}})
        r = client.post("/apps/app1/update")
        assert r.status_code == 400

    def test_update_sets_updating_status(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        app_path = tmp_path / "app1"
        app_path.mkdir()
        # init a real git repo so update can run
        subprocess.run(["git","init",str(app_path)], capture_output=True)
        subprocess.run(["git","-C",str(app_path),"commit","--allow-empty","-m","init"],
                      capture_output=True, env={**os.environ,"GIT_AUTHOR_NAME":"test",
                      "GIT_AUTHOR_EMAIL":"t@t.com","GIT_COMMITTER_NAME":"test","GIT_COMMITTER_EMAIL":"t@t.com"})
        save_state({"apps": {"app1": {
            "id":"app1","status":"ready","stack":"python",
            "install_path": str(app_path)
        }}})
        r = client.post("/apps/app1/update")
        assert r.status_code == 200
        assert r.json()["status"] == "updating"

import subprocess, os

class TestRegistryInstalledState:
    def test_installed_app_marked_in_registry(self, tmp_path, monkeypatch):
        import main
        monkeypatch.setattr(main, "STATE_FILE", tmp_path / "state.json")
        save_state({"apps": {"abc123": {
            "id":"abc123",
            "github_url": "https://github.com/comfyanonymous/ComfyUI",
            "status": "ready",
        }}})
        apps = client.get("/registry").json()["apps"]
        comfyui = next((a for a in apps if a["id"] == "comfyui"), None)
        assert comfyui is not None
        assert comfyui["installed"] is True
        assert comfyui["installed_id"] == "abc123"

