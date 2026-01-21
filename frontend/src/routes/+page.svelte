<script lang="ts">
  import { goto } from '$app/navigation';
  import { wsClient } from '$lib/websocket';
  import { gameStore, type Game } from '$lib/stores/game.svelte';

  let nickname = $state('');
  let savedNickname = $state<string | null>(null);
  let games = $state<Game[]>([]);
  let loading = $state(false);
  let error = $state('');
  let showNicknameInput = $state(true);

  // Load nickname from localStorage on mount
  $effect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('6xpoker_nickname');
      if (stored) {
        savedNickname = stored;
        nickname = stored;
        showNicknameInput = false;
        connectToLobby();
      }
    }
  });

  async function saveNickname() {
    const trimmed = nickname.trim().toLowerCase();
    if (!trimmed) {
      error = 'Please enter a nickname';
      return;
    }
    if (trimmed.length < 2) {
      error = 'Nickname must be at least 2 characters';
      return;
    }
    localStorage.setItem('6xpoker_nickname', trimmed);
    savedNickname = trimmed;
    showNicknameInput = false;
    error = '';
    await connectToLobby();
  }

  function changeNickname() {
    showNicknameInput = true;
  }

  async function connectToLobby() {
    try {
      await wsClient.connect('/ws/lobby');
      wsClient.on('lobby_update', (msg) => {
        games = msg.payload.games;
      });
      await fetchGames();
    } catch (e) {
      console.error('Failed to connect to lobby:', e);
    }
  }

  async function fetchGames() {
    try {
      const response = await fetch('/api/games');
      const data = await response.json();
      games = data.games;
    } catch (e) {
      console.error('Failed to fetch games:', e);
    }
  }

  async function createGame() {
    if (!savedNickname) return;

    loading = true;
    error = '';

    try {
      const response = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: savedNickname })
      });

      if (!response.ok) {
        const data = await response.json();
        error = data.detail || 'Failed to create game';
        return;
      }

      const data = await response.json();
      gameStore.currentGame = data.game;
      goto(`/game/${data.game.id}`);
    } catch (e) {
      error = 'Failed to create game';
    } finally {
      loading = false;
    }
  }

  async function joinGame(gameId: string) {
    if (!savedNickname) return;

    loading = true;
    error = '';

    try {
      const response = await fetch(`/api/games/${gameId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: savedNickname })
      });

      if (!response.ok) {
        const data = await response.json();
        error = data.detail || 'Failed to join game';
        return;
      }

      const data = await response.json();
      gameStore.currentGame = data.game;
      goto(`/game/${data.game.id}`);
    } catch (e) {
      error = 'Failed to join game';
    } finally {
      loading = false;
    }
  }
</script>

<main>
  <h1>6x Poker</h1>

  {#if showNicknameInput}
    <section class="card">
      <h2>Enter Your Nickname</h2>
      <p>This will be displayed to other players.</p>
      <div class="input-group">
        <input
          type="text"
          bind:value={nickname}
          placeholder="Your nickname..."
          maxlength="20"
          onkeypress={(e) => e.key === 'Enter' && saveNickname()}
        />
        <button onclick={saveNickname} disabled={!nickname.trim()}>
          Continue
        </button>
      </div>
      {#if error}
        <p class="error">{error}</p>
      {/if}
    </section>
  {:else}
    <section class="card">
      <div class="header-row">
        <span>Playing as: <strong>{savedNickname}</strong></span>
        <button class="link-btn" onclick={changeNickname}>Change</button>
      </div>
    </section>

    <section class="card">
      <div class="header-row">
        <h2>Open Games</h2>
        <button onclick={createGame} disabled={loading}>
          {loading ? 'Creating...' : 'Create Game'}
        </button>
      </div>

      {#if error}
        <p class="error">{error}</p>
      {/if}

      {#if games.length === 0}
        <p class="empty">No games available. Create one to get started!</p>
      {:else}
        <ul class="game-list">
          {#each games as game}
            <li class="game-item">
              <div class="game-info">
                <span class="creator">Created by {game.creator}</span>
                <span class="players">{game.player_count}/4 players</span>
              </div>
              <button
                onclick={() => joinGame(game.id)}
                disabled={loading || game.player_count >= 4}
              >
                {game.player_count >= 4 ? 'Full' : 'Join'}
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    <section class="card">
      <a href="/leaderboard" class="link">View Leaderboard →</a>
    </section>
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: #eee;
    min-height: 100vh;
  }

  main {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }

  h1 {
    text-align: center;
    color: #e94560;
    font-size: 2.5rem;
    margin-bottom: 2rem;
  }

  h2 {
    margin: 0;
    font-size: 1.2rem;
  }

  .card {
    background: #16213e;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }

  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .input-group {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  input {
    flex: 1;
    padding: 0.75rem 1rem;
    border: 2px solid #0f3460;
    border-radius: 8px;
    background: #1a1a2e;
    color: #eee;
    font-size: 1rem;
  }

  input:focus {
    outline: none;
    border-color: #e94560;
  }

  button {
    padding: 0.75rem 1.5rem;
    background: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  button:hover:not(:disabled) {
    background: #ff6b6b;
  }

  button:disabled {
    background: #444;
    cursor: not-allowed;
  }

  .link-btn {
    background: transparent;
    color: #e94560;
    padding: 0.25rem 0.5rem;
    text-decoration: underline;
  }

  .link-btn:hover {
    background: transparent;
    color: #ff6b6b;
  }

  .error {
    color: #ff6b6b;
    margin-top: 0.5rem;
  }

  .empty {
    color: #888;
    text-align: center;
    padding: 2rem;
  }

  .game-list {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0 0;
  }

  .game-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #1a1a2e;
    border-radius: 8px;
    margin-bottom: 0.5rem;
  }

  .game-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .creator {
    font-weight: bold;
  }

  .players {
    color: #888;
    font-size: 0.9rem;
  }

  .link {
    color: #e94560;
    text-decoration: none;
    display: block;
    text-align: center;
  }

  .link:hover {
    text-decoration: underline;
  }
</style>
