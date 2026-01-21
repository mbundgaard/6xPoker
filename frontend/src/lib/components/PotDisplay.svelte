<script lang="ts">
  interface Pot {
    amount: number;
    eligible_players: string[];
  }

  interface Props {
    pots: Pot[];
  }

  let { pots }: Props = $props();

  const totalPot = $derived(pots.reduce((sum, pot) => sum + pot.amount, 0));
</script>

<div class="pot-display">
  <div class="main-pot">
    <span class="pot-label">Pot</span>
    <span class="pot-amount">{totalPot.toLocaleString()}</span>
  </div>
  {#if pots.length > 1}
    <div class="side-pots">
      {#each pots as pot, i}
        <div class="side-pot">
          <span class="side-pot-label">{i === 0 ? 'Main' : `Side ${i}`}</span>
          <span class="side-pot-amount">{pot.amount.toLocaleString()}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .pot-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .main-pot {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: linear-gradient(135deg, #ffd700, #ff9800);
    padding: 0.5rem 1.5rem;
    border-radius: 20px;
    box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
  }

  .pot-label {
    font-size: 0.7rem;
    color: #1a1a2e;
    text-transform: uppercase;
    font-weight: bold;
  }

  .pot-amount {
    font-size: 1.5rem;
    font-weight: bold;
    color: #1a1a2e;
  }

  .side-pots {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .side-pot {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #16213e;
    padding: 0.25rem 0.75rem;
    border-radius: 8px;
    border: 1px solid #ffd700;
  }

  .side-pot-label {
    font-size: 0.6rem;
    color: #888;
    text-transform: uppercase;
  }

  .side-pot-amount {
    font-size: 0.9rem;
    font-weight: bold;
    color: #ffd700;
  }
</style>
