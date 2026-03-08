# AppDrop ▼

> **Turn any GitHub repo into a running app — no terminal, no code, no setup.**

AppDrop is an open-source desktop + web launcher. Paste any GitHub URL → auto-detect the stack → install deps → launch. Works for Python, Node.js, and Docker projects.

![AppDrop](https://img.shields.io/badge/version-0.1.0-blue) ![License](https://img.shields.io/badge/license-Apache%202.0-green) ![Tests](https://img.shields.io/badge/tests-passing-brightgreen) ![Platform](https://img.shields.io/badge/platform-Mac%20%7C%20Windows-lightgrey)

---

## ✨ What It Does

| Without AppDrop | With AppDrop |
|---|---|
| `git clone`, `python -m venv`, `pip install`, edit `.env`... | Paste URL → Click Install |
| 20 minutes of terminal debugging | 3 clicks |
| Works only if you know the stack | Works for anyone |

---

## 🚀 Quick Start

### Run the Engine (Dev Mode)
```bash
git clone https://github.com/s1meer/appdrop.git
cd appdrop
pip install -r engine/requirements.txt
python engine/main.py
# Engine running at http://localhost:8742
```

### Install an App via API
```bash
curl -X POST http://localhost:8742/apps/install \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/comfyanonymous/ComfyUI"}'
```

### Run Tests
```bash
pytest tests/ -v
```

---

## 🏗️ Project Structure

```
appdrop/
├── engine/              # Python FastAPI orchestrator
│   ├── main.py          # API routes + stack detection + installer
│   ├── github_parser.py # GitHub URL parser + README fetcher
│   └── requirements.txt
├── src/                 # React + Tauri frontend
├── registry/apps/       # Community app store JSON
├── tests/               # Pytest suite
└── .github/workflows/   # CI/CD Mac + Windows builds
```

---

## 🧱 Tech Stack

| Layer | Tech |
|---|---|
| Desktop | Tauri (Rust) |
| Frontend | React + Tailwind |
| Engine | Python FastAPI |
| Sandbox | venv / nvm / conda |
| LLM Setup | Claude Haiku (Week 3) |

---

## 📍 Roadmap

- [x] **Week 1** — Engine, stack detection, install, CI/CD, 16 tests passing
- [x] **Week 2** — GitHub parser, real install flow, progress streaming, 28 tests
- [x] **Week 3** — LLM README parser, env wizard, WebSocket, conda, 113 tests
- [x] **Week 4** — App Store, community registry, 1-click update, 181 tests
- [x] **Week 5** — Full UI live, Tauri desktop shell, Next.js web, 23/23 live tests
- [ ] **Week 6** — Signed builds & GitHub Releases (`.dmg` / `.exe`), Windows CI

---

## 🤝 Contributing

PRs welcome. Add apps via `registry/apps/yourapp.json` and open a pull request.

## 📄 License

Apache 2.0 — Built by [Sammy](https://sameerray.com.np)
