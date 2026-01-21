<script lang="ts">
  interface Props {
    card?: { rank: string; suit: string } | null;
    faceDown?: boolean;
    small?: boolean;
  }

  let { card = null, faceDown = false, small = false }: Props = $props();

  const suitSymbols: Record<string, string> = {
    hearts: '\u2665',
    diamonds: '\u2666',
    clubs: '\u2663',
    spades: '\u2660'
  };

  const rankDisplay: Record<string, string> = {
    '14': 'A',
    '13': 'K',
    '12': 'Q',
    '11': 'J',
    '10': '10',
    '9': '9',
    '8': '8',
    '7': '7',
    '6': '6',
    '5': '5',
    '4': '4',
    '3': '3',
    '2': '2'
  };

  $effect(() => {
    // Debug logging removed
  });
</script>

<div class="card" class:face-down={faceDown || !card} class:small>
  {#if card && !faceDown}
    <span class="rank">{rankDisplay[card.rank] || card.rank}</span>
    <span class="suit" class:red={card.suit === 'hearts' || card.suit === 'diamonds'}>
      {suitSymbols[card.suit] || card.suit}
    </span>
  {:else}
    <div class="card-back"></div>
  {/if}
</div>

<style>
  .card {
    width: 50px;
    height: 70px;
    background: white;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    position: relative;
  }

  .card.small {
    width: 36px;
    height: 50px;
    font-size: 0.8rem;
  }

  .card.face-down {
    background: linear-gradient(135deg, #1a1a2e 25%, #16213e 50%, #1a1a2e 75%);
    background-size: 10px 10px;
  }

  .card-back {
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
      45deg,
      #e94560,
      #e94560 2px,
      #16213e 2px,
      #16213e 8px
    );
    border-radius: 4px;
  }

  .rank {
    font-size: 1.2rem;
    color: #1a1a2e;
  }

  .suit {
    font-size: 1.4rem;
    color: #1a1a2e;
  }

  .suit.red {
    color: #e94560;
  }

  .small .rank {
    font-size: 0.9rem;
  }

  .small .suit {
    font-size: 1rem;
  }
</style>
