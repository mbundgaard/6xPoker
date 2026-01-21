# Poker PWA - Solution Design

## Overview

A multiplayer poker application for friends and family, delivered as a Progressive Web App (PWA) installable on mobile phones. The application supports multiple concurrent games, real-time gameplay via WebSockets, and an all-time leaderboard.

## Target Users

Small groups of friends (2-4 players per game) playing casual No-Limit Texas Hold'em. No authentication required — players identify themselves by nickname stored locally on their device.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Svelte + Tailwind CSS | PWA interface |
| Backend | FastAPI (Python) | API + WebSocket server |
| Database | PostgreSQL | Persistent storage |
| Hosting | Render | Single service deployment |

### Hosting Architecture

- Single Render service serves both frontend and backend
- Svelte builds to static files, served by FastAPI
- Auto-deploy on push to GitHub main branch
- PostgreSQL instance on Render

---

## Core Features

### Lobby

- View all open (waiting) games
- Create a new game
- Join an existing game
- Games disappear from lobby once started

### Gameplay

- No-Limit Texas Hold'em
- 2-4 players per game
- Fixed starting chips (developer-configured)
- Fixed hand limit (developer-configured)
- Fixed blind levels (no escalation)
- 30-second turn timer with auto-fold on timeout

### Elimination & Scoring

- Player loses all chips → eliminated from the game
- First eliminated = last place, last standing = winner
- If hand limit reached with multiple players remaining, rank by chip count
- Points awarded based on final placement
- All-time leaderboard aggregates points across all games

### Player Identity

- Nickname entered on first use
- Stored in browser local storage
- Normalized (lowercase, trimmed) to reduce duplicates on leaderboard
- No accounts, no authentication

---

## Game Lifecycle

### 1. Lobby Phase

1. Player creates a game
2. Game appears in lobby for all users
3. Other players join (creator sees who has joined)
4. Creator starts the game when ready (minimum 2 players)
5. Game removed from lobby

### 2. Game Phase

1. Hand begins, dealer position assigned (rotates each hand)
2. Blinds posted automatically
3. Hole cards dealt (private to each player)
4. Betting rounds: pre-flop → flop → turn → river
5. Showdown if multiple players remain
6. Pot awarded to winner
7. Eliminated players tracked in order
8. Repeat until hand limit reached or one player remains

### 3. End Phase

1. Final placements determined
2. Points awarded and persisted
3. All players notified of results
4. Connections closed

---

## Data Models

### Persisted (PostgreSQL)

Only completed game results are stored. No ongoing game state is persisted.

**GameResult**
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| played_at | Timestamp | When game completed |

**GameResultPlayer**
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| game_result_id | UUID | Foreign key to GameResult |
| nickname | String | Normalized player nickname |
| placement | Integer | Final position (1 = winner) |
| points_awarded | Integer | Points earned |

### In-Memory (During Active Game)

Game state lives in server memory while a game is active. Lost on server restart (acceptable for casual play).

**Game**
- id
- creator nickname
- status (waiting / active / finished)
- list of players
- current hand number
- elimination order

**GamePlayer**
- nickname
- chips
- eliminated flag
- elimination position

**Hand**
- deck (remaining cards)
- community cards
- pot (including side pots)
- current bet
- current player
- betting round (pre-flop / flop / turn / river)

**PlayerHand**
- hole cards
- current bet this round
- folded flag
- all-in flag

---

## API Design

### REST Endpoints

**Lobby**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/games | List open games |
| POST | /api/games | Create a new game |
| POST | /api/games/{id}/join | Join a game |

**Leaderboard**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/leaderboard | Get all-time rankings |

### WebSocket Connection

Connect to: `/ws/game/{game_id}?nickname={nickname}`

**Server → Client Events**

| Event | Description |
|-------|-------------|
| lobby_update | Game list changed |
| game_joined | Confirmation with current players |
| player_joined | New player joined |
| game_started | Game begins, seat positions |
| hand_started | Hole cards dealt, blinds posted |
| turn | Whose turn, valid actions, time remaining |
| player_action | Someone acted |
| community_cards | Flop/turn/river revealed |
| hand_result | Winner, pot awarded |
| player_eliminated | Someone busted out |
| game_ended | Final placements and points |

**Client → Server Events**

| Event | Description |
|-------|-------------|
| start_game | Creator starts the game |
| action | Player action (fold/check/call/raise with amount) |

---

## Disconnect Handling

- 30-second turn timer applies to all players
- Timeout or disconnect → auto-fold
- Player remains in game, folded for that hand
- Reconnecting player rejoins next hand
- No pause functionality
- Chips bleed via blinds if player stays disconnected

---

## PWA Considerations

- Service worker caches app for offline shell
- Updates download in background
- New version activates on next app open
- Simple "update available" prompt if needed (nice-to-have)
- Installable to home screen on mobile devices

---

## Points System

Points awarded based on placement. Example for 4 players:

| Placement | Points |
|-----------|--------|
| 1st | 10 |
| 2nd | 5 |
| 3rd | 2 |
| 4th | 1 |

Exact values are developer-configured.

---

## Leaderboard

- All-time cumulative points
- Query: sum of points_awarded grouped by nickname
- Visible to all players from the lobby

---

## Configuration (Developer-Set)

| Setting | Description |
|---------|-------------|
| Starting chips | Chips each player begins with |
| Hand limit | Maximum hands per game |
| Blind amounts | Small blind / big blind values |
| Turn timer | Seconds before auto-fold (30) |
| Points per placement | Points awarded for each position |

---

## Out of Scope (v1)

- User accounts / authentication
- Private or invite-only games
- Spectator mode
- Increasing blinds
- Hand history / replay
- Multiple tables per game
- Chat
- API versioning
- Game state persistence (survives server restart)

---

## Deployment

1. Push to GitHub main branch
2. Render detects change, builds:
   - Frontend: Svelte compiles to static files
   - Backend: Python dependencies installed
3. FastAPI starts, serves frontend + API + WebSocket
4. PostgreSQL connection via environment variable

Collaborators can push to GitHub without Render access. Auto-deploy handles the rest.
