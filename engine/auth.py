"""
AppDrop Auth — Stub OAuth (Google + GitHub) with JWT
Wirable: set GOOGLE_CLIENT_ID / GITHUB_CLIENT_ID env vars to enable real OAuth.
Without env vars, stub mode auto-creates a demo user and returns a JWT.
"""
import os, json, time, sqlite3, uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Optional

# ── JWT (python-jose) ────────────────────────────────────────────────────────
try:
    from jose import jwt as jose_jwt, JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False

JWT_SECRET = os.environ.get("JWT_SECRET", "appdrop-dev-secret")
JWT_ALGO   = "HS256"
JWT_EXPIRY = 30 * 24 * 3600  # 30 days

def _sign(payload: dict) -> str:
    if not JOSE_AVAILABLE:
        import base64
        header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
        body   = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        return f"{header}.{body}."
    data = {**payload, "exp": time.time() + JWT_EXPIRY, "iat": time.time()}
    return jose_jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGO)

def _verify(token: str) -> Optional[dict]:
    if not JOSE_AVAILABLE:
        try:
            import base64
            parts = token.split(".")
            pad = lambda s: s + "=" * (-len(s) % 4)
            return json.loads(base64.urlsafe_b64decode(pad(parts[1])))
        except Exception:
            return None
    try:
        return jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        return None

# ── SQLite DB ─────────────────────────────────────────────────────────────────
DB_PATH = Path.home() / ".appdrop" / "users.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                email       TEXT UNIQUE,
                name        TEXT,
                avatar_url  TEXT,
                provider    TEXT,
                provider_id TEXT,
                created_at  REAL,
                last_login  REAL
            )
        """)
        conn.commit()

_init_db()

def _upsert_user(email: str, name: str, avatar_url: str, provider: str, provider_id: str) -> dict:
    now = time.time()
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row:
            conn.execute("UPDATE users SET last_login=?, name=?, avatar_url=? WHERE email=?",
                         (now, name, avatar_url, email))
            conn.commit()
            return dict(row)
        uid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id,email,name,avatar_url,provider,provider_id,created_at,last_login) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (uid, email, name, avatar_url, provider, provider_id, now, now))
        conn.commit()
        return {"id": uid, "email": email, "name": name, "avatar_url": avatar_url,
                "provider": provider, "provider_id": provider_id,
                "created_at": now, "last_login": now}

def _get_user_by_id(uid: str) -> Optional[dict]:
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row else None

# ── Demo user (stub mode) ─────────────────────────────────────────────────────
def _stub_user(provider: str = "stub") -> str:
    user = _upsert_user(
        email="demo@appdrop.local",
        name="Demo User",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=appdrop",
        provider=provider,
        provider_id="demo",
    )
    return _sign({"sub": user["id"], "email": user["email"], "name": user["name"],
                  "avatar": user["avatar_url"]})

# ── Router ────────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/google")
def auth_google():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        token = _stub_user("google")
        return RedirectResponse(f"/?token={token}")
    redirect_uri = "http://127.0.0.1:8742/auth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url)

@auth_router.get("/google/callback")
def auth_google_callback(code: str = "", error: str = ""):
    if error or not code:
        raise HTTPException(400, f"OAuth error: {error or 'no code'}")
    client_id     = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri  = "http://127.0.0.1:8742/auth/google/callback"
    import urllib.request, urllib.parse
    token_data = urllib.parse.urlencode({
        "code": code, "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read())
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {e}")
    userinfo_req = urllib.request.Request(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
        info = json.loads(resp.read())
    user = _upsert_user(info["email"], info.get("name",""), info.get("picture",""),
                        "google", info["sub"])
    token = _sign({"sub": user["id"], "email": user["email"],
                   "name": user["name"], "avatar": user.get("avatar_url","")})
    return RedirectResponse(f"/?token={token}")

@auth_router.get("/github")
def auth_github():
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    if not client_id:
        token = _stub_user("github")
        return RedirectResponse(f"/?token={token}")
    redirect_uri = "http://127.0.0.1:8742/auth/github/callback"
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=user:email"
    )
    return RedirectResponse(url)

@auth_router.get("/github/callback")
def auth_github_callback(code: str = "", error: str = ""):
    if error or not code:
        raise HTTPException(400, f"OAuth error: {error or 'no code'}")
    client_id     = os.environ.get("GITHUB_CLIENT_ID", "")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
    import urllib.request, urllib.parse
    token_data = urllib.parse.urlencode({
        "client_id": client_id, "client_secret": client_secret, "code": code,
    }).encode()
    req = urllib.request.Request(
        "https://github.com/login/oauth/access_token",
        data=token_data,
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read())
    except Exception as e:
        raise HTTPException(400, f"Token exchange failed: {e}")
    access_token = tokens.get("access_token", "")
    user_req = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}", "User-Agent": "AppDrop/0.6.0"}
    )
    with urllib.request.urlopen(user_req, timeout=10) as resp:
        info = json.loads(resp.read())
    email = info.get("email") or f"{info['login']}@github.local"
    user = _upsert_user(email, info.get("name") or info["login"],
                        info.get("avatar_url",""), "github", str(info["id"]))
    token = _sign({"sub": user["id"], "email": user["email"],
                   "name": user["name"], "avatar": user.get("avatar_url","")})
    return RedirectResponse(f"/?token={token}")

@auth_router.get("/me")
def auth_me(request: Request):
    auth = request.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth[7:]
    payload = _verify(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    uid = payload.get("sub")
    user = _get_user_by_id(uid) if uid else None
    if not user:
        raise HTTPException(401, "User not found")
    return {k: user[k] for k in ["id","email","name","avatar_url","provider","created_at","last_login"]}

@auth_router.post("/logout")
def auth_logout():
    return {"ok": True}
