"""
AppDrop Engine v0.3.0
Weeks 1+2+3: GitHub parser, stack detection, sandbox, WebSocket progress,
             conda support, process health, log streaming
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess, os, shutil, json, uuid, re, socket, asyncio, time
from pathlib import Path
from enum import Enum
import urllib.request

app = FastAPI(title="AppDrop Engine", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

APPS_DIR = Path.home() / ".appdrop" / "apps"
APPS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = Path.home() / ".appdrop" / "state.json"
PROCESSES: dict = {}
WS_CLIENTS: dict = {}

# ── Enums ─────────────────────────────────────────────────────────────────────
class Stack(str, Enum):
    PYTHON = "python"; NODE = "node"; DOCKER = "docker"
    CONDA = "conda";   UNKNOWN = "unknown"

class InstallStage(str, Enum):
    QUEUED       = ("queued",       0,   "Waiting in queue")
    CLONING      = ("cloning",      15,  "Cloning repository")
    DETECTING    = ("detecting",    30,  "Detecting stack")
    CREATING_ENV = ("creating_env", 45,  "Creating isolated environment")
    INSTALLING   = ("installing",   65,  "Installing dependencies")
    CONFIGURING  = ("configuring",  85,  "Configuring app")
    COMPLETE     = ("complete",     100, "Ready to launch")
    FAILED       = ("failed",       0,   "Installation failed")

    def __new__(cls, value, pct, label):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.pct = pct
        obj.label = label
        return obj

class InstallRequest(BaseModel):
    github_url: str
    env_vars: Optional[dict] = {}
    name: Optional[str] = None

# ── State ─────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"apps": {}}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def update_app_state(app_id: str, **kwargs):
    state = load_state()
    if app_id in state["apps"]:
        state["apps"][app_id].update(kwargs)
        save_state(state)

# ── WebSocket broadcaster ─────────────────────────────────────────────────────
async def broadcast(app_id: str, event: dict):
    for ws in list(WS_CLIENTS.get(app_id, [])):
        try:
            await ws.send_json(event)
        except Exception:
            WS_CLIENTS.get(app_id, []).remove(ws)

def emit(app_id: str, stage: InstallStage, message: str = "", error: str = ""):
    update_app_state(app_id,
        install_stage=stage.value, install_pct=stage.pct,
        install_label=stage.label, last_message=message)
    event = {"app_id": app_id, "stage": stage.value, "pct": stage.pct,
             "label": stage.label, "message": message, "error": error, "ts": time.time()}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(app_id, event), loop)
    except Exception:
        pass

# ── GitHub parser ─────────────────────────────────────────────────────────────
def parse_github_url(url: str) -> dict:
    url = url.strip().rstrip("/")
    if url.endswith(".git"): url = url[:-4]
    m = re.search(r"(?:https?://)?github\.com/([^/\s?#]+)/([^/\s?#]+)", url)
    if m:
        owner, repo = m.group(1), m.group(2)
        return {"valid": True, "owner": owner, "repo": repo,
                "clone_url": f"https://github.com/{owner}/{repo}.git",
                "api_url": f"https://api.github.com/repos/{owner}/{repo}"}
    return {"valid": False}

def fetch_repo_metadata(owner: str, repo: str) -> dict:
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"User-Agent": "AppDrop/0.3.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read())
            return {"name": d.get("name", repo), "description": d.get("description",""),
                    "stars": d.get("stargazers_count", 0), "language": d.get("language",""),
                    "default_branch": d.get("default_branch","main")}
    except Exception:
        return {"name": repo, "description":"", "stars":0, "language":"", "default_branch":"main"}

# ── Stack detection ───────────────────────────────────────────────────────────
def detect_stack(repo_path: Path) -> Stack:
    if any((repo_path / f).exists() for f in ["environment.yml","environment.yaml"]):
        return Stack.CONDA
    checks = {
        Stack.DOCKER: ["Dockerfile","docker-compose.yml","docker-compose.yaml"],
        Stack.PYTHON: ["requirements.txt","setup.py","pyproject.toml","Pipfile","setup.cfg"],
        Stack.NODE:   ["package.json","yarn.lock","pnpm-lock.yaml"],
    }
    for stack, files in checks.items():
        if any((repo_path / f).exists() for f in files):
            return stack
    return Stack.UNKNOWN

def find_launch_command(repo_path: Path, stack: Stack) -> str:
    if stack in (Stack.PYTHON, Stack.CONDA):
        for e in ["app.py","main.py","server.py","run.py","webui.py","launch.py"]:
            if (repo_path / e).exists():
                req = repo_path / "requirements.txt"
                if req.exists():
                    txt = req.read_text().lower()
                    if "streamlit" in txt: return f"streamlit run {e}"
                    if "gradio" in txt:    return f"python {e}"
                return f"python {e}"
        return "python main.py"
    if stack == Stack.NODE:
        pkg = repo_path / "package.json"
        if pkg.exists():
            try:
                scripts = json.loads(pkg.read_text()).get("scripts", {})
                for k in ["dev","start","serve"]:
                    if k in scripts: return f"npm run {k}"
            except: pass
        return "npm start"
    return ""

# ── Port allocator ────────────────────────────────────────────────────────────
def find_free_port(start=7800, end=7900) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            try:
                s.bind(("127.0.0.1", port))
                return port  # bind succeeded = port is free
            except OSError:
                continue     # bind failed = port is in use
    raise RuntimeError("No free ports in range")

# ── Process health ────────────────────────────────────────────────────────────
def check_process_health(app_id: str) -> str:
    proc = PROCESSES.get(app_id)
    if proc is None: return "stopped"
    if proc.poll() is None: return "running"
    return "crashed"

# ── Log writer ────────────────────────────────────────────────────────────────
def write_log(app_id: str, line: str):
    log_file = APPS_DIR / app_id / ".appdrop.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {line}\n")

def _count_reqs(req_file: Path) -> int:
    return sum(1 for l in req_file.read_text().splitlines()
               if l.strip() and not l.startswith("#"))

# ── Install worker ────────────────────────────────────────────────────────────
def _run_install(app_id: str, clone_url: str, install_path: Path, env_vars: dict):
    write_log(app_id, f"Starting install: {clone_url}")
    try:
        emit(app_id, InstallStage.CLONING, f"Cloning {clone_url}")
        r = subprocess.run(["git","clone","--depth=1",clone_url,str(install_path)],
                           capture_output=True, timeout=300)
        if r.returncode != 0:
            raise subprocess.CalledProcessError(r.returncode,"git clone",stderr=r.stderr)
        write_log(app_id, "✓ Cloned")

        emit(app_id, InstallStage.DETECTING, "Scanning repo files...")
        stack = detect_stack(install_path)
        update_app_state(app_id, stack=stack.value)
        write_log(app_id, f"✓ Stack: {stack.value}")

        emit(app_id, InstallStage.CREATING_ENV, f"Creating {stack.value} environment...")
        if stack == Stack.PYTHON:
            venv = install_path / ".venv"
            subprocess.run(["python3","-m","venv",str(venv)], check=True, capture_output=True)
            write_log(app_id, "✓ venv created")
        elif stack == Stack.NODE:
            write_log(app_id, "Node — no separate env needed")

        emit(app_id, InstallStage.INSTALLING, "Installing dependencies...")
        if stack == Stack.PYTHON:
            pip = install_path / ".venv" / "bin" / "pip"
            req = install_path / "requirements.txt"
            if req.exists():
                n = _count_reqs(req)
                write_log(app_id, f"pip install ({n} packages)...")
                subprocess.run([str(pip),"install","-r",str(req),"-q"],
                               capture_output=True, timeout=600, check=True)
                write_log(app_id, "✓ pip done")
        elif stack == Stack.NODE:
            subprocess.run(["npm","install","--prefix",str(install_path),"--silent"],
                           capture_output=True, timeout=300, check=True)
            write_log(app_id, "✓ npm install done")

        emit(app_id, InstallStage.CONFIGURING, "Configuring...")
        if env_vars:
            (install_path / ".env").write_text("\n".join(f"{k}={v}" for k,v in env_vars.items()))
            write_log(app_id, f"✓ .env written ({len(env_vars)} vars)")
        launch_cmd = find_launch_command(install_path, stack)
        write_log(app_id, f"✓ launch: {launch_cmd}")

        emit(app_id, InstallStage.COMPLETE, "App ready!")
        update_app_state(app_id, status="ready", launch_command=launch_cmd,
                         installed_at=time.time())
        write_log(app_id, "=== DONE ===")

    except subprocess.CalledProcessError as e:
        err = (e.stderr.decode(errors="ignore") if e.stderr else str(e))[:500]
        emit(app_id, InstallStage.FAILED, error=err)
        update_app_state(app_id, status="error", error_message=err)
        write_log(app_id, f"ERROR: {err}")
        if install_path.exists(): shutil.rmtree(install_path, ignore_errors=True)
    except Exception as e:
        emit(app_id, InstallStage.FAILED, error=str(e))
        update_app_state(app_id, status="error", error_message=str(e)[:500])
        write_log(app_id, f"ERROR: {e}")

# ── API Routes ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status":"ok","version":"0.3.0","conda": bool(shutil.which("conda"))}

@app.get("/apps")
def list_apps():
    state = load_state()
    apps = list(state["apps"].values())
    for a in apps:
        if a["status"] == "running" and check_process_health(a["id"]) == "crashed":
            a["status"] = "error"; a["error_message"] = "Process crashed"
    return {"apps": apps}

@app.post("/validate-url")
def validate_url(body: dict):
    parsed = parse_github_url(body.get("url",""))
    if not parsed["valid"]: raise HTTPException(400, "Invalid GitHub URL")
    return {**parsed, **fetch_repo_metadata(parsed["owner"], parsed["repo"])}

@app.post("/apps/install")
async def install_app(req: InstallRequest, background_tasks: BackgroundTasks):
    parsed = parse_github_url(req.github_url)
    if not parsed["valid"]: raise HTTPException(400, "Invalid GitHub URL")
    app_id = str(uuid.uuid4())[:8]
    install_path = APPS_DIR / app_id
    state = load_state()
    state["apps"][app_id] = {
        "id":app_id,"name":req.name or parsed["repo"],"github_url":req.github_url,
        "clone_url":parsed["clone_url"],"stack":"unknown","status":"installing",
        "install_stage":"queued","install_pct":0,"install_label":"Waiting in queue",
        "port":None,"install_path":str(install_path),"error_message":None,
        "launch_command":None,"last_message":"","installed_at":None,
    }
    save_state(state)
    WS_CLIENTS[app_id] = []
    background_tasks.add_task(_run_install, app_id, parsed["clone_url"], install_path, req.env_vars or {})
    return {"app_id": app_id, "status": "installing"}

@app.get("/apps/{app_id}")
def get_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "Not found")
    return state["apps"][app_id]

@app.websocket("/apps/{app_id}/progress")
async def progress_ws(websocket: WebSocket, app_id: str):
    await websocket.accept()
    WS_CLIENTS.setdefault(app_id, []).append(websocket)
    try:
        state = load_state()
        if app_id in state["apps"]:
            a = state["apps"][app_id]
            await websocket.send_json({"app_id":app_id,"stage":a.get("install_stage","queued"),
                "pct":a.get("install_pct",0),"label":a.get("install_label",""),"ts":time.time()})
        while True:
            await asyncio.sleep(1)
            await websocket.send_json({"ping":True})
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        if app_id in WS_CLIENTS and websocket in WS_CLIENTS[app_id]:
            WS_CLIENTS[app_id].remove(websocket)

@app.get("/apps/{app_id}/logs")
def get_logs(app_id: str, last_n: int = 50):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "Not found")
    log_file = APPS_DIR / app_id / ".appdrop.log"
    if not log_file.exists(): return {"logs":[], "app_id":app_id}
    lines = log_file.read_text().splitlines()
    return {"logs": lines[-last_n:], "total": len(lines)}

@app.post("/apps/{app_id}/launch")
def launch_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "Not found")
    d = state["apps"][app_id]
    if d["status"] != "ready": raise HTTPException(400, f"App is {d['status']}")
    install_path = Path(d["install_path"])
    cmd = d.get("launch_command","")
    if not cmd: raise HTTPException(400, "No launch command")
    port = find_free_port()
    env = os.environ.copy()
    env.update({"PORT":str(port),"GRADIO_SERVER_PORT":str(port),"STREAMLIT_SERVER_PORT":str(port)})
    env_file = install_path / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=",1); env[k.strip()] = v.strip()
    out = open(APPS_DIR / app_id / "stdout.log","w")
    err = open(APPS_DIR / app_id / "stderr.log","w")
    proc = subprocess.Popen(cmd.split(), cwd=str(install_path), env=env, stdout=out, stderr=err)
    PROCESSES[app_id] = proc
    update_app_state(app_id, status="running", port=port, pid=proc.pid)
    return {"port":port,"url":f"http://localhost:{port}","pid":proc.pid}

@app.post("/apps/{app_id}/stop")
def stop_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "Not found")
    if app_id in PROCESSES:
        try: PROCESSES[app_id].terminate(); PROCESSES[app_id].wait(timeout=5)
        except: pass
        del PROCESSES[app_id]
    update_app_state(app_id, status="stopped", port=None, pid=None)
    return {"status":"stopped"}

@app.delete("/apps/{app_id}")
def delete_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "Not found")
    if app_id in PROCESSES:
        try: PROCESSES[app_id].terminate()
        except: pass
        del PROCESSES[app_id]
    shutil.rmtree(Path(state["apps"][app_id]["install_path"]), ignore_errors=True)
    del state["apps"][app_id]
    save_state(state)
    WS_CLIENTS.pop(app_id, None)
    return {"deleted": app_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8742, log_level="warning")

# ════════════════════════════════════════════════════════════════════════════════
# WEEK 4 — App Store Registry + 1-Click Update
# ════════════════════════════════════════════════════════════════════════════════

REGISTRY_DIR = Path(__file__).parent.parent / "registry" / "apps"
REGISTRY_INDEX = Path(__file__).parent.parent / "registry" / "index.json"

@app.get("/registry")
def get_registry(tag: Optional[str] = None, stack: Optional[str] = None, q: Optional[str] = None):
    """Browse the App Store — filter by tag, stack, or search query."""
    apps = []
    for f in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            a = json.loads(f.read_text())
            apps.append(a)
        except Exception:
            continue

    # Filter
    if tag:
        apps = [a for a in apps if tag.lower() in [t.lower() for t in a.get("tags", [])]]
    if stack:
        apps = [a for a in apps if a.get("stack","").lower() == stack.lower()]
    if q:
        q = q.lower()
        apps = [a for a in apps if q in a.get("name","").lower() or q in a.get("description","").lower()]

    # Merge with installed state
    state = load_state()
    installed_urls = {v["github_url"]: v["id"] for v in state["apps"].values()}
    for a in apps:
        a["installed"] = a.get("github_url","") in installed_urls
        if a["installed"]:
            a["installed_id"] = installed_urls[a["github_url"]]

    return {"total": len(apps), "apps": apps}

@app.get("/registry/{registry_id}")
def get_registry_app(registry_id: str):
    """Get a single app from the registry."""
    path = REGISTRY_DIR / f"{registry_id}.json"
    if not path.exists():
        raise HTTPException(404, f"Registry app '{registry_id}' not found")
    a = json.loads(path.read_text())
    state = load_state()
    installed_urls = {v["github_url"]: v["id"] for v in state["apps"].values()}
    a["installed"] = a.get("github_url","") in installed_urls
    return a

@app.post("/registry/submit")
def submit_app(body: dict):
    """Submit a new app to the registry (validates URL + stack before accepting)."""
    url = body.get("github_url","")
    parsed = parse_github_url(url)
    if not parsed["valid"]:
        raise HTTPException(400, "Invalid GitHub URL")
    app_id = parsed["repo"].lower().replace("_","-").replace(".","-")
    existing = REGISTRY_DIR / f"{app_id}.json"
    if existing.exists():
        raise HTTPException(409, f"App '{app_id}' already exists in registry")
    submission = {
        "id": app_id,
        "name": body.get("name", parsed["repo"]),
        "description": body.get("description", ""),
        "github_url": f"https://github.com/{parsed['owner']}/{parsed['repo']}",
        "clone_url": parsed["clone_url"],
        "stack": body.get("stack", "unknown"),
        "tags": body.get("tags", []),
        "default_port": body.get("default_port", 8080),
        "stars_approx": 0,
        "verified": False,
        "added_by": body.get("submitted_by", "community"),
        "min_ram_gb": body.get("min_ram_gb", 4),
        "thumbnail": f"https://opengraph.githubassets.com/1/{parsed['owner']}/{parsed['repo']}",
        "submitted_at": time.time(),
        "status": "pending_review",
    }
    # Save as pending (not in main registry until reviewed)
    pending_dir = REGISTRY_DIR.parent / "pending"
    pending_dir.mkdir(exist_ok=True)
    (pending_dir / f"{app_id}.json").write_text(json.dumps(submission, indent=2))
    return {"submitted": True, "app_id": app_id, "status": "pending_review",
            "message": "Submission received! Will be reviewed before appearing in the store."}

@app.post("/apps/{app_id}/update")
async def update_app(app_id: str, background_tasks: BackgroundTasks):
    """1-click update — git pull + reinstall dependencies."""
    state = load_state()
    if app_id not in state["apps"]:
        raise HTTPException(404, "App not found")
    d = state["apps"][app_id]
    if d["status"] == "running":
        raise HTTPException(400, "Stop the app before updating")
    install_path = Path(d["install_path"])
    if not install_path.exists():
        raise HTTPException(400, "App files not found — reinstall the app")
    update_app_state(app_id, status="updating", install_stage="cloning",
                     install_pct=10, install_label="Pulling latest changes...")
    background_tasks.add_task(_run_update, app_id, install_path, d)
    return {"app_id": app_id, "status": "updating"}

def _run_update(app_id: str, install_path: Path, app_data: dict):
    write_log(app_id, "=== UPDATE STARTED ===")
    try:
        # Step 1: git pull
        write_log(app_id, "git pull...")
        r = subprocess.run(["git", "-C", str(install_path), "pull", "--rebase"],
                          capture_output=True, timeout=120)
        if r.returncode != 0:
            raise Exception(f"git pull failed: {r.stderr.decode()[:300]}")
        write_log(app_id, "✓ git pull done")
        update_app_state(app_id, install_pct=50, install_label="Updating dependencies...")

        # Step 2: reinstall deps
        stack = Stack(app_data.get("stack", "unknown"))
        if stack == Stack.PYTHON:
            pip = install_path / ".venv" / "bin" / "pip"
            req = install_path / "requirements.txt"
            if pip.exists() and req.exists():
                subprocess.run([str(pip), "install", "-r", str(req), "-q"],
                              capture_output=True, timeout=300, check=True)
                write_log(app_id, "✓ pip update done")
        elif stack == Stack.NODE:
            subprocess.run(["npm", "install", "--prefix", str(install_path), "--silent"],
                          capture_output=True, timeout=300, check=True)
            write_log(app_id, "✓ npm update done")

        update_app_state(app_id, status="ready", install_pct=100,
                        install_stage="complete", install_label="Update complete",
                        updated_at=time.time())
        write_log(app_id, "=== UPDATE COMPLETE ===")

    except Exception as e:
        update_app_state(app_id, status="error", install_stage="failed",
                        install_pct=0, error_message=str(e)[:500])
        write_log(app_id, f"UPDATE ERROR: {e}")

@app.get("/apps/{app_id}/update-check")
def check_for_update(app_id: str):
    """Check if a git update is available without pulling."""
    state = load_state()
    if app_id not in state["apps"]:
        raise HTTPException(404, "App not found")
    install_path = Path(state["apps"][app_id]["install_path"])
    if not install_path.exists():
        return {"update_available": False, "reason": "app files missing"}
    try:
        subprocess.run(["git","-C",str(install_path),"fetch","--dry-run"],
                      capture_output=True, timeout=15)
        result = subprocess.run(["git","-C",str(install_path),"status","-uno"],
                               capture_output=True, timeout=10)
        behind = b"behind" in result.stdout
        return {"update_available": behind,
                "current_commit": subprocess.run(
                    ["git","-C",str(install_path),"rev-parse","--short","HEAD"],
                    capture_output=True).stdout.decode().strip()}
    except Exception as e:
        return {"update_available": False, "reason": str(e)}
