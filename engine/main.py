"""AppDrop Engine v0.2.0 - Week 2"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess, os, shutil, json, uuid, re, socket
from pathlib import Path
from enum import Enum
import urllib.request

app = FastAPI(title="AppDrop Engine", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

APPS_DIR = Path.home() / ".appdrop" / "apps"
APPS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = Path.home() / ".appdrop" / "state.json"
PROCESSES: dict = {}

class Stack(str, Enum):
    PYTHON = "python"; NODE = "node"; DOCKER = "docker"; UNKNOWN = "unknown"

class AppStatus(str, Enum):
    INSTALLING = "installing"; READY = "ready"; RUNNING = "running"
    ERROR = "error"; STOPPED = "stopped"

class InstallRequest(BaseModel):
    github_url: str
    env_vars: Optional[dict] = {}
    name: Optional[str] = None

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"apps": {}}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def parse_github_url(url: str) -> dict:
    url = url.strip().rstrip("/").rstrip(".git")
    pattern = r"(?:https?://)?github\.com/([^/\s?#]+)/([^/\s?#]+)"
    m = re.search(pattern, url)
    if m:
        owner, repo = m.group(1), m.group(2)
        return {"valid": True, "owner": owner, "repo": repo,
                "clone_url": f"https://github.com/{owner}/{repo}.git",
                "api_url": f"https://api.github.com/repos/{owner}/{repo}"}
    return {"valid": False}

def fetch_repo_metadata(owner: str, repo: str) -> dict:
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}",
                                     headers={"User-Agent": "AppDrop/0.2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read())
            return {"name": d.get("name", repo), "description": d.get("description", ""),
                    "stars": d.get("stargazers_count", 0), "language": d.get("language", ""),
                    "default_branch": d.get("default_branch", "main")}
    except Exception:
        return {"name": repo, "description": "", "stars": 0, "language": "", "default_branch": "main"}

def detect_stack(repo_path: Path) -> Stack:
    checks = {Stack.DOCKER: ["Dockerfile","docker-compose.yml"],
               Stack.PYTHON: ["requirements.txt","setup.py","pyproject.toml","Pipfile"],
               Stack.NODE: ["package.json","yarn.lock"]}
    for stack, files in checks.items():
        if any((repo_path / f).exists() for f in files):
            return stack
    return Stack.UNKNOWN

def find_launch_command(repo_path: Path, stack: Stack) -> str:
    if stack == Stack.PYTHON:
        for e in ["app.py","main.py","server.py","run.py","webui.py"]:
            if (repo_path / e).exists():
                req = repo_path / "requirements.txt"
                if req.exists() and "streamlit" in req.read_text().lower():
                    return f"streamlit run {e}"
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

def find_free_port(start=7800, end=7900) -> int:
    for port in range(start, end):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free ports")

def _run_install(app_id, clone_url, install_path, env_vars):
    state = load_state()
    try:
        state["apps"][app_id]["install_stage"] = "cloning"; save_state(state)
        subprocess.run(["git","clone","--depth=1",clone_url,str(install_path)],
                       check=True, capture_output=True, timeout=300)
        stack = detect_stack(install_path)
        state["apps"][app_id]["stack"] = stack.value
        state["apps"][app_id]["install_stage"] = "installing_deps"; save_state(state)
        if stack == Stack.PYTHON:
            venv = install_path / ".venv"
            subprocess.run(["python3","-m","venv",str(venv)], check=True, capture_output=True)
            pip = venv / "bin" / "pip"
            req = install_path / "requirements.txt"
            if req.exists():
                subprocess.run([str(pip),"install","-r",str(req),"-q"],
                               check=True, capture_output=True, timeout=600)
        elif stack == Stack.NODE:
            subprocess.run(["npm","install","--prefix",str(install_path)],
                           check=True, capture_output=True, timeout=300)
        if env_vars:
            (install_path / ".env").write_text("\n".join(f"{k}={v}" for k,v in env_vars.items()))
        launch_cmd = find_launch_command(install_path, stack)
        state["apps"][app_id].update({"status":"ready","install_stage":"complete","launch_command":launch_cmd})
        save_state(state)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore") if e.stderr else str(e)
        state["apps"][app_id].update({"status":"error","error_message":err[:500],"install_stage":"failed"})
        save_state(state)
        if install_path.exists(): shutil.rmtree(install_path, ignore_errors=True)
    except Exception as e:
        state["apps"][app_id].update({"status":"error","error_message":str(e)[:500],"install_stage":"failed"})
        save_state(state)

@app.get("/health")
def health(): return {"status":"ok","version":"0.2.0"}

@app.get("/apps")
def list_apps(): return {"apps": list(load_state()["apps"].values())}

@app.post("/validate-url")
def validate_url(body: dict):
    parsed = parse_github_url(body.get("url",""))
    if not parsed["valid"]: raise HTTPException(400, "Invalid GitHub URL")
    meta = fetch_repo_metadata(parsed["owner"], parsed["repo"])
    return {**parsed, **meta}

@app.post("/apps/install")
async def install_app(request: InstallRequest, background_tasks: BackgroundTasks):
    parsed = parse_github_url(request.github_url)
    if not parsed["valid"]: raise HTTPException(400, "Invalid GitHub URL")
    app_id = str(uuid.uuid4())[:8]
    name = request.name or parsed["repo"]
    install_path = APPS_DIR / app_id
    state = load_state()
    state["apps"][app_id] = {"id":app_id,"name":name,"github_url":request.github_url,
        "clone_url":parsed["clone_url"],"stack":"unknown","status":"installing",
        "install_stage":"queued","port":None,"install_path":str(install_path),
        "error_message":None,"launch_command":None}
    save_state(state)
    background_tasks.add_task(_run_install, app_id, parsed["clone_url"], install_path, request.env_vars or {})
    return {"app_id": app_id, "status": "installing"}

@app.get("/apps/{app_id}")
def get_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "App not found")
    return state["apps"][app_id]

@app.post("/apps/{app_id}/launch")
def launch_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "App not found")
    app_data = state["apps"][app_id]
    if app_data["status"] != "ready": raise HTTPException(400, f"App is {app_data['status']}")
    install_path = Path(app_data["install_path"])
    launch_cmd = app_data.get("launch_command","")
    if not launch_cmd: raise HTTPException(400, "No launch command")
    port = find_free_port()
    env = os.environ.copy()
    env.update({"PORT":str(port),"GRADIO_SERVER_PORT":str(port)})
    env_file = install_path / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=",1); env[k.strip()] = v.strip()
    proc = subprocess.Popen(launch_cmd.split(), cwd=str(install_path), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCESSES[app_id] = proc
    state["apps"][app_id].update({"status":"running","port":port,"pid":proc.pid})
    save_state(state)
    return {"port":port,"url":f"http://localhost:{port}","pid":proc.pid}

@app.post("/apps/{app_id}/stop")
def stop_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "App not found")
    if app_id in PROCESSES:
        try: PROCESSES[app_id].terminate(); PROCESSES[app_id].wait(timeout=5)
        except: pass
        del PROCESSES[app_id]
    state["apps"][app_id].update({"status":"stopped","port":None,"pid":None})
    save_state(state)
    return {"status":"stopped"}

@app.delete("/apps/{app_id}")
def delete_app(app_id: str):
    state = load_state()
    if app_id not in state["apps"]: raise HTTPException(404, "App not found")
    if app_id in PROCESSES:
        try: PROCESSES[app_id].terminate()
        except: pass
        del PROCESSES[app_id]
    install_path = Path(state["apps"][app_id]["install_path"])
    if install_path.exists(): shutil.rmtree(install_path, ignore_errors=True)
    del state["apps"][app_id]
    save_state(state)
    return {"deleted": app_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8742, log_level="warning")
