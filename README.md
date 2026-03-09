# AppDrop

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2-FFC131?logo=tauri&logoColor=black)](https://tauri.app/)
[![Tests](https://img.shields.io/badge/tests-255%20passing-brightgreen)](./tests/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

**AppDrop** is a macOS/Linux desktop application that lets you install and run local AI apps with a single click. Think of it as an App Store for open-source AI tools — ComfyUI, Ollama, AUTOMATIC1111, Whisper, and 25 more — all installed into isolated environments with no manual dependency management.

---

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Features](#features)
- [Registry: 28 Pre-Registered Apps](#registry-28-pre-registered-apps)
- [API Reference](#api-reference)
- [WebSocket Events](#websocket-events)
- [Configuration](#configuration)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Testing](#testing)
- [Contributing](#contributing)
- [Project Structure](#project-structure)

---

## Architecture

```
+------------------------------------------------------------------+
|                         Desktop Layer                            |
|                    Tauri 2 (Rust wrapper)                        |
+------------------------------+-----------------------------------+
                               | webview
+------------------------------v-----------------------------------+
|                       Frontend (React + TypeScript)              |
|                                                                  |
|   AppStore  MyApps  Settings  Auth  Onboarding  AppDetail        |
|   InstallModal  Sidebar  Toast                                   |
|                                                                  |
|   REST  <--->  WebSocket ws://localhost:8742/apps/{id}/progress  |
+------------------------------+-----------------------------------+
                               | HTTP / WebSocket
+------------------------------v-----------------------------------+
|                    Engine (FastAPI :8742)                        |
|               engine/main.py — Python 3.10+                     |
|                                                                  |
|  GitHub Parser → Stack Detector → Env Creator → Launcher        |
|  Auth · Rate limiter · Request logger · Crash monitor           |
+----+---------------+------------------+-----------+-------------+
     |               |                  |           |
     v               v                  v           v
+---------+  +--------------+  +-------------+  +--------------+
|Registry |  |  State JSON  |  | Analytics   |  | Users SQLite |
|JSON     |  |~/.appdrop/   |  | JSON        |  | (OAuth)      |
|28 apps  |  |state.json    |  |analytics/   |  |auth.py       |
+---------+  +--------------+  +-------------+  +--------------+
```

---

## Quick Start

> **Requirements:** Python 3.10+, Node.js 18+, Rust (for Tauri builds). Git must be on `$PATH`.

```bash
# 1. Install engine dependencies
pip install -r engine/requirements.txt

# 2. Start the engine (keep this terminal open)
python engine/main.py

# 3. In a second terminal, start the desktop app
npm install && npm run tauri:dev
```

The desktop window opens automatically. The engine listens on `http://localhost:8742`.

To run the web UI only (no Tauri):

```bash
npm run dev   # opens http://localhost:5173
```

---

## Features

### Core Installation

| Feature | Details |
|---|---|
| One-click install | Paste any GitHub URL; AppDrop clones, detects stack, installs deps automatically |
| Smart launch detection | Reads `package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile` |
| Isolated environments | Each app gets its own `venv` (Python) or `node_modules` (Node) |
| Install queue | Max 1 concurrent install; additional installs queue with position indicator |
| Rate limiting | 10 installs per hour |
| Crash recovery | Apps that exit unexpectedly are auto-restarted up to 3 times |
| 1-click update | Pull latest commits and reinstall dependencies |
| Dependency checker | Pre-install scan lists missing system tools with download links |
| Persistent settings | Per-app env vars, port overrides, and flags survive restarts |
| Multi-instance | Run multiple copies of the same app on different ports |
| Auto port conflict | Automatically finds a free port if the default is busy |

### App Store

| Feature | Details |
|---|---|
| 28 pre-registered apps | Curated registry with metadata, tags, RAM requirements, GPU flags |
| App detail modal | Click any card for full info, compatibility badge, stats, README preview |
| Search & filter | Full-text search + filter by stack and tag |
| Natural language search | "I want to run stable diffusion" maps to the right app via Claude |
| App Health Score | 0-100 based on process state, HTTP response, logs, memory |
| Compatibility badges | `excellent` / `ok` / `needs_gpu` / `too_heavy` based on your hardware |
| Community submissions | Submit via UI; lands in `registry/pending/` for review |

### AI Features (requires `ANTHROPIC_API_KEY`)

| Feature | Details |
|---|---|
| AI Smart Installer | Claude reads the README and synthesizes install commands when auto-detection fails |
| Natural language search | Describe what you want; engine returns top matching apps |

### Power User Features

| Feature | Details |
|---|---|
| Fork / Clone apps | Duplicate an installed app with different settings |
| App Templates | Pre-configured bundles: AI Image Studio, Local Chat Suite, Audio Lab, Video Suite |
| Export / Import | Package an app's config as a `.appdrop` bundle |
| Usage Analytics | Local-only: launch count, installs today, top apps |
| Drag-to-install | Drag a GitHub URL from your browser onto the install dialog |
| Keyboard shortcuts | `⌘K` / `⌘N` / `⌘1` / `⌘2` / `⌘3` |

### Authentication

| Feature | Details |
|---|---|
| Google OAuth | Standard PKCE flow; stub mode works without credentials |
| GitHub OAuth | Standard PKCE flow; stub mode works without credentials |
| Guest mode | Full local functionality without an account |

---

## Registry: 28 Pre-Registered Apps

All registry entries live in `registry/apps/` as JSON files.

| App | Stack | Category | Min RAM |
|---|---|---|---|
| AUTOMATIC1111 Stable Diffusion | Python | Image Generation | 8 GB |
| Bark | Python | Audio / TTS | 4 GB |
| ComfyUI | Python | Image Generation | 4 GB |
| ComfyUI Manager | Python | Image Generation | 4 GB |
| Flowise | Node | LLM Orchestration | 2 GB |
| Fooocus | Python | Image Generation | 8 GB |
| GPT4All | Python | LLM | 4 GB |
| InvokeAI | Python | Image Generation | 8 GB |
| Jan | Node | LLM | 4 GB |
| KoboldCpp | Python | LLM | 4 GB |
| LangFlow | Python | LLM Orchestration | 2 GB |
| llama.cpp | Python | LLM | 4 GB |
| LocalAI | Docker | LLM | 8 GB |
| MLX-LM | Python | LLM (Apple Silicon) | 8 GB |
| MusicGen | Python | Audio | 8 GB |
| Ollama | Node | LLM | 4 GB |
| Open WebUI | Node | LLM Frontend | 2 GB |
| Real-ESRGAN | Python | Image Upscaling | 4 GB |
| SadTalker | Python | Video | 8 GB |
| stable-diffusion.cpp | Python | Image Generation | 4 GB |
| Stable Video Diffusion | Python | Video Generation | 16 GB |
| Text Generation WebUI | Python | LLM | 8 GB |
| Tortoise TTS | Python | Audio | 8 GB |
| Video-Retalking | Python | Video | 8 GB |
| Wav2Lip | Python | Video | 4 GB |
| Whisper.cpp | Python | Speech-to-Text | 2 GB |
| Whisper WebUI | Python | Speech-to-Text | 2 GB |
| Lobe Chat | Node | LLM Frontend | 2 GB |

### Adding a Custom App

```json
{
  "id": "my-app",
  "name": "My App",
  "description": "What it does.",
  "github_url": "https://github.com/user/repo",
  "clone_url": "https://github.com/user/repo.git",
  "stack": "python",
  "default_port": 7860,
  "tags": ["image", "diffusion"],
  "min_ram_gb": 8,
  "stars_approx": 10000,
  "verified": false,
  "added_by": "community"
}
```

Drop the file in `registry/apps/` and restart the engine.

---

## API Reference

All endpoints return JSON. Base URL: `http://localhost:8742`.

### Health & System

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Engine version and uptime |
| `GET` | `/system/info` | Platform, RAM, GPU, Apple Silicon, disk |
| `GET` | `/system/deps` | Check git, python3, node, docker, conda |
| `GET` | `/metrics` | Aggregate install/launch/error counts |

### Apps

| Method | Path | Description |
|---|---|---|
| `GET` | `/apps` | List installed apps (`?q=` and `?status=` filters) |
| `GET` | `/apps/{id}` | Single app metadata and state |
| `POST` | `/apps/install` | Begin install from a GitHub URL |
| `POST` | `/apps/{id}/launch` | Start the app process |
| `POST` | `/apps/{id}/stop` | Stop the app process |
| `POST` | `/apps/{id}/restart` | Stop and relaunch |
| `DELETE` | `/apps/{id}` | Uninstall and remove directory |
| `GET` | `/apps/{id}/logs` | Recent log lines |
| `POST` | `/apps/{id}/update` | Pull latest commits and reinstall |
| `GET` | `/apps/{id}/update-check` | Check if behind remote |
| `GET` | `/apps/{id}/settings` | Per-app persistent settings |
| `PUT` | `/apps/{id}/settings` | Save per-app settings |
| `GET` | `/apps/{id}/health-score` | 0-100 health score with breakdown |
| `POST` | `/apps/{id}/fork` | Duplicate app under a new name |
| `GET` | `/apps/{id}/clone-instance` | Launch second instance on new port |
| `GET` | `/apps/{id}/readme` | Fetch upstream README |
| `GET` | `/apps/{id}/export` | Export app bundle |
| `POST` | `/apps/import` | Import app bundle |
| `POST` | `/apps/{id}/ai-setup` | AI-generated install guidance |
| `POST` | `/apps/search-and-install` | Natural language app search |

### Registry

| Method | Path | Description |
|---|---|---|
| `GET` | `/registry` | All pre-registered apps (with compatibility field) |
| `GET` | `/registry/{id}` | Single registry entry |
| `POST` | `/registry/submit` | Submit a community app |
| `POST` | `/validate-url` | Validate GitHub URL before install |

### Templates & Analytics

| Method | Path | Description |
|---|---|---|
| `GET` | `/templates` | List available app bundles |
| `POST` | `/templates/{id}/install` | Install all apps in a bundle |
| `GET` | `/analytics/summary` | Local usage stats |

### Auth

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/google` | Initiate Google OAuth (or stub) |
| `GET` | `/auth/github` | Initiate GitHub OAuth (or stub) |
| `GET` | `/auth/me` | Decode Bearer JWT → user info |
| `POST` | `/auth/logout` | Stateless logout |

---

## WebSocket Events

Connect to `ws://localhost:8742/apps/{id}/progress` after calling `POST /apps/install`:

```json
{
  "app_id": "abc123",
  "stage": "installing",
  "pct": 65,
  "label": "Installing dependencies",
  "message": "Collecting torch==2.1.0",
  "error": "",
  "ts": 1741478400.0
}
```

| Stage | % | Description |
|---|---|---|
| `queued` | 0 | Waiting for install slot |
| `cloning` | 15 | Running `git clone` |
| `detecting` | 30 | Reading manifest files |
| `creating_env` | 45 | Creating `venv` or checking Docker |
| `installing` | 65 | Running `pip install` / `npm install` |
| `configuring` | 85 | Writing config, env vars |
| `complete` | 100 | Ready to launch |
| `failed` | 0 | Install failed (`error` field has details) |

---

## Configuration

Runtime data lives under `~/.appdrop/`:

```
~/.appdrop/
├── state.json          # installed apps, status, settings
├── analytics.json      # local-only usage logs
├── engine.log          # request log
├── users.db            # SQLite OAuth user records
└── apps/
    ├── comfyui/
    └── ...
```

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for AI Smart Installer |
| `GOOGLE_CLIENT_ID` | — | Real Google OAuth |
| `GOOGLE_CLIENT_SECRET` | — | Real Google OAuth |
| `GITHUB_CLIENT_ID` | — | Real GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | — | Real GitHub OAuth |
| `JWT_SECRET` | `appdrop-dev-secret` | Change in production |

Copy `.env.example` to `.env` and fill in values.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` | Quick launcher / install dialog |
| `⌘N` | New install dialog |
| `⌘1` | Switch to App Store |
| `⌘2` | Switch to My Apps |
| `⌘3` | Switch to Settings |

---

## Testing

255 tests across 7 files. The engine must be running on `:8742`.

```bash
python engine/main.py &
pytest tests/ -q
```

| File | Tests | Coverage |
|---|---|---|
| `test_engine.py` | ~25 | Health, install, launch, stop, delete |
| `test_github_parser.py` | ~30 | URL validation, stack detection |
| `test_pipeline.py` | ~60 | End-to-end install pipeline |
| `test_week2.py` | ~25 | Registry, system info, WebSocket |
| `test_week3.py` | ~30 | Update, health score, crash recovery |
| `test_week6.py` | 30 | Auth, compatibility, system info |
| `test_week8.py` | 44 | Analytics, templates, NL search, AI setup, export/import |

---

## Contributing

### Dev Setup

```bash
git clone https://github.com/s1meer/appdrop
cd appdrop
pip install -r engine/requirements.txt
npm install

# Terminal 1: engine
python engine/main.py

# Terminal 2: frontend
npm run dev
```

### Where to Make Changes

| Change | Location |
|---|---|
| Add a registry app | `registry/apps/<id>.json` |
| Install logic / stack detection | `engine/main.py` |
| AI features | `engine/ai_features.py` |
| Auth | `engine/auth.py` |
| New API endpoint | `engine/main.py` |
| New UI page | `src/pages/` |
| New component | `src/components/` |
| Tauri window / menus | `src-tauri/src/` |
| Tests | `tests/` |

### PR Guidelines

- One feature or fix per PR
- Add tests for any changed engine behavior
- Registry entries must include all required fields
- Run `pytest tests/ -q` — all must pass
- Python: Black-formatted; TypeScript: ESLint-clean

### Commit Style

```
feat: add whisper-webui registry entry
fix: docker compose launch priority
docs: update API reference
test: health score edge cases
```

---

## Project Structure

```
appdrop/
├── engine/
│   ├── main.py              # FastAPI engine — all routes + pipeline
│   ├── auth.py              # OAuth, JWT, SQLite user store
│   ├── ai_features.py       # Claude-powered installer + NL search
│   └── requirements.txt
├── registry/
│   ├── index.json           # Registry manifest (28 apps)
│   └── apps/                # JSON app definitions
├── src/
│   ├── App.tsx              # Root: auth gate, onboarding, keyboard shortcuts
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── InstallModal.tsx  # Drag-to-install, WebSocket progress
│   │   └── Toast.tsx         # Top-right notifications
│   ├── hooks/
│   │   ├── useApps.ts
│   │   ├── useRegistry.ts
│   │   ├── useAuth.ts
│   │   └── useToast.ts
│   ├── lib/
│   │   └── api.ts            # All API methods
│   └── pages/
│       ├── AppStore.tsx      # Browse + filter registry
│       ├── MyApps.tsx        # Manage installed apps
│       ├── Settings.tsx      # Theme, analytics, auth
│       ├── Auth.tsx          # Sign in with Google / GitHub / Guest
│       ├── Onboarding.tsx    # 3-step first-run wizard
│       └── AppDetail.tsx     # App info modal
├── src-tauri/
│   ├── tauri.conf.json
│   └── src/
├── tests/
│   ├── test_engine.py
│   ├── test_github_parser.py
│   ├── test_pipeline.py
│   ├── test_week2.py
│   ├── test_week3.py
│   ├── test_week6.py
│   └── test_week8.py
├── .env.example
├── vite.config.ts
└── package.json
```

---

## License

MIT. See [LICENSE](./LICENSE).

---

> Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vitejs.dev/), and [Tauri](https://tauri.app/).
