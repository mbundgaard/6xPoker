<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { wsClient } from '$lib/websocket';
  import { gameStore, type Game, type GamePlayer } from '$lib/stores/game';
  import Card from '$lib/components/Card.svelte';
  import PlayerSeat from '$lib/components/PlayerSeat.svelte';
  import ActionButtons from '$lib/components/ActionButtons.svelte';
  import PotDisplay from '$lib/components/PotDisplay.svelte';
  import CommunityCards from '$lib/components/CommunityCards.svelte';
  import Timer from '$lib/components/Timer.svelte';

  let gameId = $derived($page.params.id);
  let nickname = $state<string | null>(null);
  let game = $state<Game | null>(null);
  let error = $state('');
  let connected = $state(false);
  let turnTimer = $state(30);
  let timerInterval: ReturnType<typeof setInterval> | null = null;
  let validActions = $state<any>(null);
  let handResult = $state<any>(null);
  let showResult = $state(false);

  onMount(async () => {
    // Get nickname from localStorage
    if (typeof window !== 'undefined') {
      nickname = localStorage.getItem('6xpoker_nickname');
      if (!nickname) {
        goto('/');
        return;
      }
    }

    await connectToGame();
  });

  onDestroy(() => {
    if (timerInterval) {
      clearInterval(timerInterval);
    }
    wsClient.disconnect();
  });

  async function connectToGame() {
    try {
      // Clear any existing handlers from previous pages
      wsClient.clearHandlers();

      // Set up message handlers BEFORE connecting
      // (server sends game_joined immediately on connect)
      wsClient.on('game_joined', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('player_joined', (msg) => {
        if (game) {
          game = {
            ...game,
            players: msg.payload.players,
            player_count: msg.payload.players.length
          };
        }
      });

      wsClient.on('player_connected', (msg) => {
        // Could show a toast notification
      });

      wsClient.on('player_disconnected', (msg) => {
        // Could show a toast notification
      });

      wsClient.on('game_started', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('hand_started', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
        showResult = false;
        handResult = null;
      });

      wsClient.on('blinds_posted', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('turn', (msg) => {
        validActions = msg.payload.valid_actions;
        turnTimer = msg.payload.time_remaining || 30;
        startTimer();
      });

      wsClient.on('player_action', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
        // Clear valid actions if it's no longer our turn
        if (game?.active_hand?.action_on !== nickname) {
          validActions = null;
          stopTimer();
        }
      });

      wsClient.on('community_cards', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('hand_result', (msg) => {
        handResult = msg.payload;
        game = msg.payload.game;
        gameStore.currentGame = game;
        showResult = true;
        validActions = null;
        stopTimer();
      });

      wsClient.on('player_eliminated', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('game_ended', (msg) => {
        game = msg.payload.game;
        gameStore.currentGame = game;
      });

      wsClient.on('error', (msg) => {
        error = msg.payload.message;
        setTimeout(() => error = '', 3000);
      });

      wsClient.on('disconnect', () => {
        connected = false;
      });

      // Connect after handlers are set up
      await wsClient.connect(`/ws/game/${gameId}?nickname=${nickname}`);
      connected = true;
    } catch (e) {
      console.error('Failed to connect:', e);
      error = 'Failed to connect to game';
    }
  }

  function startTimer() {
    stopTimer();
    timerInterval = setInterval(() => {
      if (turnTimer > 0) {
        turnTimer--;
      }
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function startGame() {
    wsClient.send('start_game');
  }

  function sendAction(action: string, amount?: number) {
    wsClient.send('action', { action, amount });
  }

  // Computed values
  const isCreator = $derived(game?.creator === nickname);
  const isWaiting = $derived(game?.status === 'waiting');
  const isActive = $derived(game?.status === 'active');
  const isFinished = $derived(game?.status === 'finished');
  const canStartGame = $derived(isCreator && isWaiting && (game?.player_count || 0) >= 2);
  const isMyTurn = $derived(game?.active_hand?.action_on === nickname);
  const activeHand = $derived(game?.active_hand);
  const myPlayer = $derived(game?.players.find(p => p.nickname === nickname));
  const myHand = $derived(activeHand?.player_hands?.[nickname as string]);

  // Get player positions (up to 4 players in clockwise order)
  const positionedPlayers = $derived(() => {
    if (!game?.players || !nickname) return [];

    const players = [...game.players];
    const myIndex = players.findIndex(p => p.nickname === nickname);

    // Rotate array so current player is at bottom
    const rotated = [...players.slice(myIndex), ...players.slice(0, myIndex)];

    // Assign positions based on player count
    const positions = ['bottom', 'left', 'top', 'right'];
    return rotated.map((player, i) => ({
      ...player,
      position: positions[i % 4],
      hand: activeHand?.player_hands?.[player.nickname],
      isDealer: game?.dealer_position === game?.players.indexOf(player),
      isCurrentTurn: activeHand?.action_on === player.nickname
    }));
  });
</script>

<svelte:head>
  <title>Game - 6x Poker</title>
</svelte:head>

<main>
  {#if !connected && !error}
    <div class="loading">Connecting to game...</div>
  {:else if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if game}
    <!-- Waiting Room -->
    {#if isWaiting}
      <div class="waiting-room">
        <h1>Waiting for Players</h1>
        <p class="game-code">Game ID: <code>{game.id.slice(0, 8)}</code></p>

        <div class="player-list">
          <h2>Players ({game.player_count}/4)</h2>
          <ul>
            {#each game.players as player}
              <li class:creator={player.nickname === game.creator}>
                {player.nickname}
                {#if player.nickname === game.creator}
                  <span class="badge">Host</span>
                {/if}
                {#if player.nickname === nickname}
                  <span class="badge you">You</span>
                {/if}
              </li>
            {/each}
          </ul>
        </div>

        {#if canStartGame}
          <button class="start-btn" onclick={startGame}>
            Start Game
          </button>
        {:else if isCreator}
          <p class="waiting-text">Waiting for at least 2 players...</p>
        {:else}
          <p class="waiting-text">Waiting for host to start the game...</p>
        {/if}

        <a href="/" class="leave-link">Leave Game</a>
      </div>

    <!-- Active Game -->
    {:else if isActive || isFinished}
      <div class="game-table">
        <!-- Header -->
        <header class="game-header">
          <span>Hand #{game.current_hand_num}</span>
          <span class="round">{activeHand?.betting_round || 'Waiting'}</span>
        </header>

        <!-- Table Layout -->
        <div class="table-container">
          <!-- Top player -->
          {#each positionedPlayers() as player}
            {#if player.position === 'top'}
              <div class="seat-top">
                <PlayerSeat
                  nickname={player.nickname}
                  chips={player.chips}
                  isEliminated={player.is_eliminated}
                  isCurrentTurn={player.isCurrentTurn}
                  isDealer={player.isDealer}
                  isSelf={player.nickname === nickname}
                  hand={player.hand}
                  turnTimer={player.isCurrentTurn ? turnTimer : 0}
                />
              </div>
            {/if}
          {/each}

          <div class="middle-row">
            <!-- Left player -->
            {#each positionedPlayers() as player}
              {#if player.position === 'left'}
                <div class="seat-left">
                  <PlayerSeat
                    nickname={player.nickname}
                    chips={player.chips}
                    isEliminated={player.is_eliminated}
                    isCurrentTurn={player.isCurrentTurn}
                    isDealer={player.isDealer}
                    isSelf={player.nickname === nickname}
                    hand={player.hand}
                    turnTimer={player.isCurrentTurn ? turnTimer : 0}
                  />
                </div>
              {/if}
            {/each}

            <!-- Center: Pot and Community Cards -->
            <div class="table-center">
              {#if activeHand?.pots && activeHand.pots.length > 0}
                <PotDisplay pots={activeHand.pots} />
              {/if}

              <CommunityCards cards={activeHand?.community_cards || []} />

              <!-- Hand Result Overlay -->
              {#if showResult && handResult}
                <div class="hand-result">
                  <h3>Hand Complete</h3>
                  {#each handResult.winners as winner}
                    <p class="winner">
                      <strong>{winner.nickname}</strong> wins {winner.amount} with {winner.hand_description || 'best hand'}
                    </p>
                  {/each}
                </div>
              {/if}
            </div>

            <!-- Right player -->
            {#each positionedPlayers() as player}
              {#if player.position === 'right'}
                <div class="seat-right">
                  <PlayerSeat
                    nickname={player.nickname}
                    chips={player.chips}
                    isEliminated={player.is_eliminated}
                    isCurrentTurn={player.isCurrentTurn}
                    isDealer={player.isDealer}
                    isSelf={player.nickname === nickname}
                    hand={player.hand}
                    turnTimer={player.isCurrentTurn ? turnTimer : 0}
                  />
                </div>
              {/if}
            {/each}
          </div>

          <!-- Bottom player (self) -->
          {#each positionedPlayers() as player}
            {#if player.position === 'bottom'}
              <div class="seat-bottom">
                <PlayerSeat
                  nickname={player.nickname}
                  chips={player.chips}
                  isEliminated={player.is_eliminated}
                  isCurrentTurn={player.isCurrentTurn}
                  isDealer={player.isDealer}
                  isSelf={player.nickname === nickname}
                  hand={player.hand}
                  turnTimer={player.isCurrentTurn ? turnTimer : 0}
                />
              </div>
            {/if}
          {/each}
        </div>

        <!-- Action Buttons (only when it's your turn) -->
        {#if isMyTurn && validActions && !myPlayer?.is_eliminated}
          <div class="action-area">
            <ActionButtons
              {validActions}
              onAction={sendAction}
            />
          </div>
        {/if}

        <!-- Game Finished -->
        {#if isFinished}
          <div class="game-over">
            <h2>Game Over!</h2>
            <div class="final-standings">
              <h3>Final Standings</h3>
              {#each game.players.sort((a, b) => (a.elimination_position || 99) - (b.elimination_position || 99)) as player, i}
                <div class="standing">
                  <span class="place">#{i + 1}</span>
                  <span class="name">{player.nickname}</span>
                  <span class="chips">{player.chips} chips</span>
                </div>
              {/each}
            </div>
            <a href="/" class="return-btn">Return to Lobby</a>
          </div>
        {/if}
      </div>
    {/if}
  {:else}
    <div class="loading">Loading game...</div>
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
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    font-size: 1.2rem;
    color: #888;
  }

  .error-banner {
    background: #e94560;
    color: white;
    padding: 0.75rem;
    text-align: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
  }

  /* Waiting Room */
  .waiting-room {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
    gap: 1.5rem;
  }

  .waiting-room h1 {
    color: #e94560;
    margin: 0;
  }

  .game-code {
    color: #888;
  }

  .game-code code {
    background: #16213e;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    color: #4caf50;
  }

  .player-list {
    background: #16213e;
    padding: 1.5rem;
    border-radius: 12px;
    min-width: 250px;
  }

  .player-list h2 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: #888;
  }

  .player-list ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .player-list li {
    padding: 0.75rem;
    border-bottom: 1px solid #0f3460;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .player-list li:last-child {
    border-bottom: none;
  }

  .badge {
    font-size: 0.7rem;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    background: #ffd700;
    color: #1a1a2e;
  }

  .badge.you {
    background: #4caf50;
    color: white;
  }

  .start-btn {
    padding: 1rem 3rem;
    background: #4caf50;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1.2rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
  }

  .start-btn:hover {
    background: #5cbf60;
  }

  .waiting-text {
    color: #888;
  }

  .leave-link {
    color: #e94560;
    text-decoration: none;
    margin-top: 1rem;
  }

  .leave-link:hover {
    text-decoration: underline;
  }

  /* Game Table */
  .game-table {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .game-header {
    display: flex;
    justify-content: space-between;
    padding: 1rem;
    background: #16213e;
  }

  .round {
    text-transform: capitalize;
    color: #4caf50;
  }

  .table-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .middle-row {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .table-center {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 2rem;
    background: radial-gradient(ellipse at center, #0f3460 0%, #1a1a2e 70%);
    border-radius: 100px;
    margin: 0 1rem;
    min-height: 200px;
    position: relative;
  }

  .seat-top, .seat-bottom {
    display: flex;
    justify-content: center;
  }

  .seat-left, .seat-right {
    display: flex;
    align-items: center;
  }

  .action-area {
    padding: 1rem;
    border-top: 1px solid #0f3460;
  }

  .hand-result {
    position: absolute;
    background: rgba(22, 33, 62, 0.95);
    padding: 1rem 2rem;
    border-radius: 12px;
    text-align: center;
    border: 2px solid #ffd700;
  }

  .hand-result h3 {
    margin: 0 0 0.5rem 0;
    color: #ffd700;
  }

  .winner {
    margin: 0.25rem 0;
    color: #4caf50;
  }

  /* Game Over */
  .game-over {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(26, 26, 46, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    z-index: 50;
  }

  .game-over h2 {
    color: #ffd700;
    font-size: 2rem;
    margin: 0;
  }

  .final-standings {
    background: #16213e;
    padding: 1.5rem;
    border-radius: 12px;
    min-width: 280px;
  }

  .final-standings h3 {
    margin: 0 0 1rem 0;
    text-align: center;
    color: #888;
  }

  .standing {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid #0f3460;
    gap: 1rem;
  }

  .standing:last-child {
    border-bottom: none;
  }

  .standing .place {
    font-weight: bold;
    color: #ffd700;
    min-width: 30px;
  }

  .standing .name {
    flex: 1;
  }

  .standing .chips {
    color: #888;
  }

  .return-btn {
    padding: 1rem 2rem;
    background: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    text-decoration: none;
    font-size: 1rem;
    cursor: pointer;
  }

  .return-btn:hover {
    background: #ff6b6b;
  }

  /* Responsive */
  @media (max-width: 600px) {
    .table-center {
      border-radius: 50px;
      padding: 1rem;
      min-height: 150px;
    }

    .middle-row {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>
