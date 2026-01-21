# Planned File Structure

Target structure as features are implemented:

```
6xPoker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, serves static files
│   │   ├── config.py            # Game settings (chips, blinds, points, etc.)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # REST endpoints (games, leaderboard)
│   │   │   └── websocket.py     # WebSocket handler
│   │   ├── game/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py       # In-memory game state manager
│   │   │   ├── models.py        # Game, Hand, Player dataclasses
│   │   │   ├── poker.py         # Hand evaluation, deck, dealing
│   │   │   └── actions.py       # Fold, check, call, raise logic
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py      # PostgreSQL connection
│   │       ├── models.py        # SQLAlchemy models (GameResult, etc.)
│   │       └── queries.py       # Leaderboard queries
│   ├── requirements.txt
│   └── tests/
│       ├── test_poker.py        # Hand evaluation tests
│       └── test_game.py         # Game logic tests
│
├── frontend/
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css              # Tailwind imports
│   │   ├── routes/
│   │   │   ├── +page.svelte     # Lobby (home)
│   │   │   ├── +layout.svelte
│   │   │   ├── game/
│   │   │   │   └── [id]/
│   │   │   │       └── +page.svelte  # Game table
│   │   │   └── leaderboard/
│   │   │       └── +page.svelte
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── Card.svelte
│   │   │   │   ├── PlayerSeat.svelte
│   │   │   │   ├── ActionButtons.svelte
│   │   │   │   ├── PotDisplay.svelte
│   │   │   │   └── Timer.svelte
│   │   │   ├── stores/
│   │   │   │   ├── game.ts      # Game state store
│   │   │   │   └── player.ts    # Local player (nickname)
│   │   │   └── websocket.ts     # WebSocket client
│   │   └── service-worker.js    # PWA offline support
│   ├── static/
│   │   ├── manifest.json        # PWA manifest
│   │   └── icons/
│   ├── package.json
│   ├── svelte.config.js
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── docs/
│   ├── poker-solution.md        # Full solution design
│   └── planned-structure.md     # This file
│
├── render.yaml                  # Render deployment config
├── build.sh                     # Build script (frontend + backend)
├── README.md
└── CLAUDE.md
```

## Design Decisions

- **`game/` module isolated from `api/`** - Poker logic testable independently of HTTP/WebSocket
- **SvelteKit file-based routing** - `/game/[id]` for dynamic game pages
- **Svelte stores for state** - Reactive game state from WebSocket updates
- **Single `config.py`** - All developer-configurable values in one place
