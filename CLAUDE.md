# CLAUDE.md

This file provides guidance for Claude Code when working on this project.

## Project Overview

6x Poker is a multiplayer No-Limit Texas Hold'em PWA. See `docs/poker-solution.md` for the complete solution design.

## Architecture

- `backend/` - FastAPI Python server
  - `app/main.py` - Entry point, serves API and static frontend
  - REST endpoints at `/api/*`
  - WebSocket at `/ws`
- `frontend/` - SvelteKit app (Svelte 5)
  - Builds to static files in `frontend/build/`
  - FastAPI serves these in production
- Single Render service hosts both frontend and backend

## Commands

### Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm run dev      # Development with hot reload
npm run build    # Production build
```

## Key Patterns

- **No authentication**: Players use nicknames stored in localStorage
- **In-memory game state**: Active games live in server memory, not persisted
- **PostgreSQL**: Only stores completed game results for leaderboard
- **WebSocket**: All real-time game communication

## Current State

Minimal scaffold with:
- Health check endpoint (`GET /api/health`)
- Basic WebSocket echo (`/ws`)
- Simple frontend to test both

## Next Steps

1. Lobby system (create/join games)
2. Game state management
3. Poker hand logic
4. PostgreSQL integration
