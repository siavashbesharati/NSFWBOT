# NSFWBOT

Telegram AI bot with Venice integration, character system, chat memory, payments, and Flask admin dashboard.

## Core Docs

- Persian unified guide: `PROJECT_SUMMARY_FA.md`
- Docker deployment: `DOCKER_DEPLOYMENT.md`

## Quick Run

```bash
pip install -r requirements.txt
python start_bot.py start
```

Dashboard default URL:

- `http://127.0.0.1:5000`

## Runtime Modes

- Full stack: `python start_bot.py start`
- Bot only: `python start_bot.py bot-only`
- Dashboard only: `python start_bot.py dashboard-only`

## Configuration Model

- Application settings are DB-first (stored in `admin_settings`).
- Keep only runtime envs as needed by host:
  - `DATABASE_PATH`
  - `PORT` (hosted platforms)

## Deploy Targets

- Railway
- PythonAnywhere
- Docker/VPS

For full setup and deployment steps, use `PROJECT_SUMMARY_FA.md`.