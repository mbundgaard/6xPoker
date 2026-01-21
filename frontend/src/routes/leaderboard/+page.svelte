<script lang="ts">
  let leaderboard = $state<{ nickname: string; total_points: number; games_played: number }[]>([]);
  let loading = $state(true);
  let error = $state('');

  $effect(() => {
    fetchLeaderboard();
  });

  async function fetchLeaderboard() {
    try {
      const response = await fetch('/api/leaderboard');
      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }
      const data = await response.json();
      leaderboard = data.leaderboard;
    } catch (e) {
      error = 'Failed to load leaderboard';
      console.error(e);
    } finally {
      loading = false;
    }
  }
</script>

<main>
  <header>
    <a href="/" class="back-link">&larr; Back to Lobby</a>
    <h1>Leaderboard</h1>
  </header>

  {#if loading}
    <p class="loading">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if leaderboard.length === 0}
    <section class="card">
      <p class="empty">No games completed yet. Play some games to appear on the leaderboard!</p>
    </section>
  {:else}
    <section class="card">
      <table>
        <thead>
          <tr>
            <th class="rank">#</th>
            <th class="player">Player</th>
            <th class="points">Points</th>
            <th class="games">Games</th>
          </tr>
        </thead>
        <tbody>
          {#each leaderboard as entry, i}
            <tr class:top-three={i < 3}>
              <td class="rank">
                {#if i === 0}
                  <span class="medal gold">1</span>
                {:else if i === 1}
                  <span class="medal silver">2</span>
                {:else if i === 2}
                  <span class="medal bronze">3</span>
                {:else}
                  {i + 1}
                {/if}
              </td>
              <td class="player">{entry.nickname}</td>
              <td class="points">{entry.total_points}</td>
              <td class="games">{entry.games_played}</td>
            </tr>
          {/each}
        </tbody>
      </table>
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

  header {
    margin-bottom: 2rem;
  }

  .back-link {
    color: #e94560;
    text-decoration: none;
    font-size: 0.9rem;
  }

  .back-link:hover {
    text-decoration: underline;
  }

  h1 {
    color: #e94560;
    font-size: 2rem;
    margin: 0.5rem 0 0 0;
  }

  .card {
    background: #16213e;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .loading, .error, .empty {
    text-align: center;
    padding: 2rem;
  }

  .error {
    color: #ff6b6b;
  }

  .empty {
    color: #888;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th, td {
    padding: 0.75rem 0.5rem;
    text-align: left;
  }

  th {
    color: #888;
    font-weight: normal;
    font-size: 0.85rem;
    text-transform: uppercase;
    border-bottom: 1px solid #0f3460;
  }

  td {
    border-bottom: 1px solid #0f3460;
  }

  tr:last-child td {
    border-bottom: none;
  }

  .rank {
    width: 50px;
  }

  .points, .games {
    text-align: right;
    width: 80px;
  }

  th.points, th.games {
    text-align: right;
  }

  .medal {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    font-weight: bold;
    font-size: 0.9rem;
  }

  .medal.gold {
    background: linear-gradient(135deg, #ffd700, #ffaa00);
    color: #1a1a2e;
  }

  .medal.silver {
    background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
    color: #1a1a2e;
  }

  .medal.bronze {
    background: linear-gradient(135deg, #cd7f32, #a05a20);
    color: #1a1a2e;
  }

  .top-three .player {
    font-weight: bold;
  }
</style>
