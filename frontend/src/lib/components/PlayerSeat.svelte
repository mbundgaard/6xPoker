<script lang="ts">
  import Card from './Card.svelte';
  import Timer from './Timer.svelte';

  interface PlayerHand {
    hole_cards: { rank: string; suit: string }[];
    current_bet: number;
    folded: boolean;
    all_in: boolean;
  }

  interface Props {
    nickname: string;
    chips: number;
    isEliminated?: boolean;
    isCurrentTurn?: boolean;
    isDealer?: boolean;
    isSelf?: boolean;
    hand?: PlayerHand | null;
    turnTimer?: number;
    position?: 'top' | 'bottom' | 'left' | 'right';
  }

  let {
    nickname,
    chips,
    isEliminated = false,
    isCurrentTurn = false,
    isDealer = false,
    isSelf = false,
    hand = null,
    turnTimer = 0,
    position = 'bottom'
  }: Props = $props();

  const status = $derived(() => {
    if (isEliminated) return 'eliminated';
    if (hand?.folded) return 'folded';
    if (hand?.all_in) return 'all-in';
    if (isCurrentTurn) return 'active';
    return '';
  });
</script>

<div
  class="player-seat {position}"
  class:current-turn={isCurrentTurn}
  class:eliminated={isEliminated}
  class:folded={hand?.folded}
  class:self={isSelf}
>
  <div class="player-info">
    <div class="name-row">
      {#if isDealer}
        <span class="dealer-chip">D</span>
      {/if}
      <span class="nickname" class:self={isSelf}>{nickname}</span>
    </div>
    <span class="chips">{chips.toLocaleString()}</span>
    {#if status() && status() !== 'active'}
      <span class="status {status()}">{status()}</span>
    {/if}
  </div>

  <div class="cards">
    {#if hand && !isEliminated}
      {#if isSelf && hand.hole_cards?.length === 2}
        <Card card={hand.hole_cards[0]} small />
        <Card card={hand.hole_cards[1]} small />
      {:else if !hand.folded}
        <Card faceDown small />
        <Card faceDown small />
      {/if}
    {/if}
  </div>

  {#if hand?.current_bet && hand.current_bet > 0}
    <div class="bet-amount">{hand.current_bet}</div>
  {/if}

  {#if isCurrentTurn && turnTimer > 0}
    <div class="timer-container">
      <Timer seconds={turnTimer} />
    </div>
  {/if}
</div>

<style>
  .player-seat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: #16213e;
    border-radius: 12px;
    border: 2px solid transparent;
    min-width: 120px;
    transition: all 0.3s ease;
  }

  .player-seat.current-turn {
    border-color: #4caf50;
    box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);
  }

  .player-seat.self {
    background: #1a2744;
  }

  .player-seat.eliminated {
    opacity: 0.5;
  }

  .player-seat.folded {
    opacity: 0.6;
  }

  .player-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .name-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .dealer-chip {
    width: 20px;
    height: 20px;
    background: #ffd700;
    color: #1a1a2e;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: bold;
  }

  .nickname {
    font-weight: bold;
    font-size: 0.9rem;
  }

  .nickname.self {
    color: #4caf50;
  }

  .chips {
    color: #ffd700;
    font-size: 0.85rem;
  }

  .status {
    font-size: 0.75rem;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .status.folded {
    background: #666;
    color: #ccc;
  }

  .status.all-in {
    background: #e94560;
    color: white;
  }

  .status.eliminated {
    background: #333;
    color: #888;
  }

  .cards {
    display: flex;
    gap: 0.25rem;
    min-height: 50px;
  }

  .bet-amount {
    background: #e94560;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
  }

  .timer-container {
    width: 100%;
    margin-top: 0.25rem;
  }
</style>
