# 6x Poker

A multiplayer No-Limit Texas Hold'em PWA for friends and family.

## Tech Stack

- **Frontend**: Svelte 5 + SvelteKit
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (planned)
- **Hosting**: Render

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` and `/ws` to the backend at `localhost:8000`.

## Deployment

Push to `main` branch. Render auto-deploys via `render.yaml`.

## Documentation

See [docs/poker-solution.md](docs/poker-solution.md) for the full solution design.
