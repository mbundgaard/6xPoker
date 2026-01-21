# 6xPoker Development Plan

This document outlines the implementation roadmap for the 6xPoker application. Each phase builds on the previous one. Follow phases in order.

---

## Current State

- Basic FastAPI scaffold with health check endpoint
- WebSocket echo endpoint (not game-specific)
- Minimal SvelteKit frontend
- Render deployment configured (web service + PostgreSQL)
- `DATABASE_URL` environment variable set

---

## Phase 1: Configuration & Database Foundation

**Goal:** Establish the configuration system and database connectivity.

### Tasks

1. **Create `backend/app/config.py`**
   - Define all game settings as constants or environment variables
   - Settings: starting chips (1000), small blind (10), big blind (20), hand limit (50), turn timer (30 seconds)
   - Points per placement: 1st=10, 2nd=5, 3rd=2, 4th=1

2. **Create `backend/app/db/database.py`**
   - Async PostgreSQL connection using `asyncpg` or `databases` library
   - Connection pool setup using `DATABASE_URL`
   - Startup/shutdown hooks in FastAPI

3. **Create `backend/app/db/models.py`**
   - SQLAlchemy models for `GameResult` and `GameResultPlayer`
   - See `docs/poker-solution.md` for schema

4. **Create database migration**
   - Use Alembic or raw SQL script
   - Create tables: `game_results`, `game_result_players`

5. **Update `requirements.txt`**
   - Add: `asyncpg`, `sqlalchemy`, `databases` (or chosen ORM/driver)

### Acceptance Criteria

- App starts and connects to PostgreSQL on Render
- Tables exist in database
- Config values accessible throughout the app

---

## Phase 2: Lobby System (REST API)

**Goal:** Players can create and join games via REST endpoints.

### Tasks

1. **Create `backend/app/game/models.py`**
   - Dataclasses for in-memory state: `Game`, `GamePlayer`
   - Game statuses: `waiting`, `active`, `finished`
   - Include: id, creator, status, players list, created_at

2. **Create `backend/app/game/manager.py`**
   - `GameManager` class holding all active games in a dict
   - Methods: `create_game()`, `join_game()`, `get_game()`, `list_waiting_games()`, `remove_game()`
   - Singleton instance or dependency injection

3. **Create `backend/app/api/routes.py`**
   - `GET /api/games` - List all waiting games
   - `POST /api/games` - Create game (body: `{nickname}`)
   - `POST /api/games/{id}/join` - Join game (body: `{nickname}`)
   - Return game details with player list

4. **Register routes in `main.py`**
   - Include router from `api/routes.py`

### Acceptance Criteria

- Can create a game via API and see it in game list
- Can join a game; creator sees updated player list
- Games have unique IDs (use UUID)
- Maximum 4 players enforced

---

## Phase 3: WebSocket Game Connection

**Goal:** Players connect via WebSocket for real-time updates.

### Tasks

1. **Create `backend/app/api/websocket.py`**
   - WebSocket endpoint: `/ws/game/{game_id}?nickname={nickname}`
   - On connect: validate game exists, player is in game
   - Track connections per game in `GameManager`

2. **Define message protocol**
   - Server messages: `lobby_update`, `player_joined`, `game_started`, `error`
   - Client messages: `start_game`
   - Use JSON with `{type, payload}` structure

3. **Implement lobby broadcasts**
   - When game created/joined: broadcast `lobby_update` to lobby subscribers
   - When player joins game: broadcast `player_joined` to game participants

4. **Implement game start**
   - Creator sends `start_game`
   - Validate minimum 2 players
   - Change game status to `active`
   - Broadcast `game_started` with seat positions

5. **Handle disconnections**
   - Remove from connection tracking
   - Don't remove from game (they can reconnect)

### Acceptance Criteria

- Players can connect to game WebSocket
- All players receive real-time updates when someone joins
- Creator can start game; all players notified
- Lobby updates broadcast to lobby subscribers

---

## Phase 4: Poker Core Logic

**Goal:** Implement card dealing and hand evaluation.

### Tasks

1. **Create `backend/app/game/poker.py`**
   - Card representation (rank, suit)
   - Deck class with shuffle and deal methods
   - Hand evaluation function returning hand rank and tiebreaker values
   - Hand ranks: high card, pair, two pair, three of a kind, straight, flush, full house, four of a kind, straight flush

2. **Hand evaluation approach**
   - Given 7 cards (2 hole + 5 community), find best 5-card hand
   - Return comparable tuple: `(hand_rank, tiebreaker_values)`
   - Higher tuple wins

3. **Create `backend/app/game/models.py` additions**
   - `Hand` dataclass: deck, community_cards, pot, current_bet, betting_round, player_hands
   - `PlayerHand` dataclass: hole_cards, current_bet, folded, all_in
   - Betting rounds: `preflop`, `flop`, `turn`, `river`, `showdown`

4. **Write tests in `backend/tests/test_poker.py`**
   - Test each hand type evaluates correctly
   - Test hand comparison (flush beats straight, etc.)
   - Test tiebreakers (higher pair wins, kickers matter)

### Acceptance Criteria

- Deck shuffles and deals correctly
- Hand evaluator correctly ranks all hand types
- Tiebreakers work (A-high flush beats K-high flush)
- All tests pass

---

## Phase 5: Betting & Actions

**Goal:** Implement the betting system and player actions.

### Tasks

1. **Create `backend/app/game/actions.py`**
   - `fold(game, player)` - Mark player folded
   - `check(game, player)` - Valid when no bet to call
   - `call(game, player)` - Match current bet
   - `raise_bet(game, player, amount)` - Increase the bet
   - `all_in(game, player)` - Bet all remaining chips

2. **Implement betting round logic in `manager.py`**
   - Track current player (position-based rotation)
   - Determine valid actions for current player
   - Advance to next player after action
   - Detect when betting round is complete (all players acted, bets matched)

3. **Implement pot management**
   - Main pot calculation
   - Side pot creation when player is all-in with less than others' bets
   - Award correct pots at showdown

4. **Add action validation**
   - Only current player can act
   - Raise must be at least big blind (or all-in)
   - Can't check when there's a bet to call

### Acceptance Criteria

- All actions modify game state correctly
- Betting round ends when all active players have acted and bets match
- Side pots created correctly for all-in scenarios
- Invalid actions rejected with error message

---

## Phase 6: Full Game Loop

**Goal:** Complete hand lifecycle from deal to showdown.

### Tasks

1. **Implement hand flow in `manager.py`**
   - `start_hand()`: Rotate dealer, post blinds, deal hole cards
   - `advance_round()`: Deal community cards (flop=3, turn=1, river=1)
   - `resolve_hand()`: Determine winner(s), award pot(s)

2. **Add turn timer**
   - 30-second timer per player turn
   - Use `asyncio.create_task` with timeout
   - Auto-fold on timeout

3. **Implement WebSocket game events**
   - `hand_started`: Send hole cards (private per player), blinds info
   - `turn`: Current player, valid actions, time remaining
   - `player_action`: Broadcast action taken
   - `community_cards`: Reveal flop/turn/river
   - `hand_result`: Winner(s), cards shown, pot awarded

4. **Implement elimination tracking**
   - When player loses all chips, mark eliminated
   - Track elimination order for final placement
   - Game ends when one player remains OR hand limit reached

5. **Implement game end**
   - Calculate final placements (elimination order, or chip count if hand limit)
   - Award points per `config.py`
   - Save to database (`GameResult`, `GameResultPlayer`)
   - Broadcast `game_ended` with results

### Acceptance Criteria

- Complete hand plays out from blinds to showdown
- Timer auto-folds inactive players
- Eliminations tracked correctly
- Game ends and persists results to database
- Points awarded correctly

---

## Phase 7: Leaderboard

**Goal:** Display all-time player rankings.

### Tasks

1. **Create `backend/app/db/queries.py`**
   - `get_leaderboard()`: Sum points by nickname, order descending
   - Return: list of `{nickname, total_points, games_played}`

2. **Add REST endpoint**
   - `GET /api/leaderboard` - Return top players

3. **Frontend leaderboard page**
   - Route: `/leaderboard`
   - Fetch and display rankings
   - Link from lobby

### Acceptance Criteria

- Leaderboard shows cumulative points across all games
- Updates after each game completes
- Accessible from lobby

---

## Phase 8: Frontend - Lobby

**Goal:** Functional lobby UI for creating/joining games.

### Tasks

1. **Create `frontend/src/lib/stores/player.ts`**
   - Store nickname in Svelte store + localStorage
   - Prompt for nickname on first visit

2. **Create lobby page (`frontend/src/routes/+page.svelte`)**
   - Display list of waiting games (fetch from `/api/games`)
   - "Create Game" button
   - "Join" button per game
   - Link to leaderboard

3. **Create `frontend/src/lib/websocket.ts`**
   - WebSocket client wrapper
   - Connect/disconnect methods
   - Message send/receive with typed events
   - Auto-reconnect logic

4. **Implement lobby WebSocket**
   - Subscribe to `lobby_update` events
   - Update game list in real-time

5. **Navigation to game**
   - After creating or joining, navigate to `/game/{id}`

### Acceptance Criteria

- Can enter nickname (persists across sessions)
- See live list of waiting games
- Create game navigates to game page
- Join game navigates to game page

---

## Phase 9: Frontend - Game Table

**Goal:** Playable game interface.

### Tasks

1. **Create `frontend/src/lib/stores/game.ts`**
   - Reactive store for game state
   - Update from WebSocket events

2. **Create game page (`frontend/src/routes/game/[id]/+page.svelte`)**
   - Connect to game WebSocket on mount
   - Display game state from store

3. **Create components**
   - `Card.svelte`: Display single card (face up or down)
   - `PlayerSeat.svelte`: Player info, chips, cards, status (folded/all-in/turn)
   - `PotDisplay.svelte`: Show pot amount
   - `Timer.svelte`: Countdown for current player's turn
   - `ActionButtons.svelte`: Fold, Check, Call, Raise with amount input

4. **Layout**
   - Players arranged around table (CSS positioning)
   - Community cards in center
   - Pot above community cards
   - Action buttons at bottom (only shown when it's your turn)

5. **Handle all game events**
   - Update store on: `hand_started`, `turn`, `player_action`, `community_cards`, `hand_result`, `player_eliminated`, `game_ended`
   - Show appropriate UI state for each

6. **Waiting room UI**
   - Before game starts, show player list
   - Creator sees "Start Game" button

### Acceptance Criteria

- Game table displays all players and their state
- Cards render correctly (hole cards, community cards)
- Actions submit correctly and update UI
- Timer shows countdown
- Game end shows final results

---

## Phase 10: PWA Features

**Goal:** Installable progressive web app.

### Tasks

1. **Create `frontend/static/manifest.json`**
   - App name, icons, theme color, display mode (standalone)

2. **Create app icons**
   - Multiple sizes: 192x192, 512x512
   - Place in `frontend/static/icons/`

3. **Configure SvelteKit for PWA**
   - Service worker for caching
   - Offline shell support

4. **Add to home screen support**
   - Meta tags in `app.html`
   - iOS-specific meta tags

### Acceptance Criteria

- App installable on mobile devices
- Works offline (shows cached shell)
- Proper icons and splash screens

---

## Phase 11: Polish & Testing

**Goal:** Production-ready quality.

### Tasks

1. **Error handling**
   - Graceful WebSocket disconnection recovery
   - API error responses with useful messages
   - Frontend error display

2. **UI polish**
   - Loading states
   - Animations for card dealing, chip movement
   - Sound effects (optional)

3. **Testing**
   - Backend unit tests for poker logic
   - Backend integration tests for game flow
   - Frontend component tests

4. **Performance**
   - Optimize WebSocket message frequency
   - Minimize re-renders in Svelte

5. **Security review**
   - Validate all inputs
   - Ensure players can't see others' hole cards
   - Rate limiting on API endpoints

### Acceptance Criteria

- No crashes on edge cases
- Smooth user experience
- Tests cover critical paths

---

## Implementation Order Summary

| Phase | Name | Dependencies |
|-------|------|--------------|
| 1 | Configuration & Database | None |
| 2 | Lobby System (REST) | Phase 1 |
| 3 | WebSocket Connection | Phase 2 |
| 4 | Poker Core Logic | None (can parallel with 1-3) |
| 5 | Betting & Actions | Phase 4 |
| 6 | Full Game Loop | Phases 3, 5 |
| 7 | Leaderboard | Phase 1 |
| 8 | Frontend - Lobby | Phase 3 |
| 9 | Frontend - Game Table | Phase 6, 8 |
| 10 | PWA Features | Phase 8 |
| 11 | Polish & Testing | All previous |

---

## Notes for Future Sessions

- Always check current state of files before making changes
- Run `npm run build` in frontend after changes, then test on Render
- Test WebSocket functionality locally with two browser tabs
- Database schema changes require migration or manual SQL
- Check Render logs for deployment/runtime errors: https://dashboard.render.com/web/srv-d5o8hfsoud1c73cf6neg

---

## Quick Reference

**Local Development:**
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

**Render URLs:**
- App: https://sixxpoker.onrender.com
- Dashboard: https://dashboard.render.com/web/srv-d5o8hfsoud1c73cf6neg
- Database: https://dashboard.render.com/d/dpg-d5o8h14hg0os73ff35s0-a

**Key Files:**
- Solution design: `docs/poker-solution.md`
- File structure: `docs/planned-structure.md`
- This plan: `docs/development-plan.md`
