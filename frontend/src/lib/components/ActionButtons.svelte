<script lang="ts">
  interface ValidActions {
    can_fold: boolean;
    can_check: boolean;
    can_call: boolean;
    can_raise: boolean;
    can_all_in: boolean;
    call_amount: number;
    min_raise: number;
    max_raise: number;
  }

  interface Props {
    validActions: ValidActions;
    onAction: (action: string, amount?: number) => void;
    disabled?: boolean;
  }

  let { validActions, onAction, disabled = false }: Props = $props();

  let raiseAmount = $state(validActions.min_raise);

  $effect(() => {
    raiseAmount = validActions.min_raise;
  });

  function handleRaise() {
    onAction('raise', raiseAmount);
  }

  function handleSliderChange(e: Event) {
    const target = e.target as HTMLInputElement;
    raiseAmount = parseInt(target.value);
  }
</script>

<div class="action-buttons">
  <div class="main-actions">
    {#if validActions.can_fold}
      <button class="btn fold" onclick={() => onAction('fold')} {disabled}>
        Fold
      </button>
    {/if}

    {#if validActions.can_check}
      <button class="btn check" onclick={() => onAction('check')} {disabled}>
        Check
      </button>
    {/if}

    {#if validActions.can_call}
      <button class="btn call" onclick={() => onAction('call')} {disabled}>
        Call {validActions.call_amount}
      </button>
    {/if}

    {#if validActions.can_all_in}
      <button class="btn all-in" onclick={() => onAction('all_in')} {disabled}>
        All In
      </button>
    {/if}
  </div>

  {#if validActions.can_raise}
    <div class="raise-section">
      <div class="raise-slider">
        <input
          type="range"
          min={validActions.min_raise}
          max={validActions.max_raise}
          bind:value={raiseAmount}
          oninput={handleSliderChange}
          {disabled}
        />
        <div class="raise-labels">
          <span>{validActions.min_raise}</span>
          <span class="raise-amount">{raiseAmount}</span>
          <span>{validActions.max_raise}</span>
        </div>
      </div>
      <button class="btn raise" onclick={handleRaise} {disabled}>
        Raise to {raiseAmount}
      </button>
    </div>
  {/if}
</div>

<style>
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    background: #16213e;
    border-radius: 12px;
  }

  .main-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 80px;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn.fold {
    background: #666;
    color: white;
  }

  .btn.fold:hover:not(:disabled) {
    background: #777;
  }

  .btn.check {
    background: #4caf50;
    color: white;
  }

  .btn.check:hover:not(:disabled) {
    background: #5cbf60;
  }

  .btn.call {
    background: #2196f3;
    color: white;
  }

  .btn.call:hover:not(:disabled) {
    background: #42a5f5;
  }

  .btn.raise {
    background: #ff9800;
    color: white;
  }

  .btn.raise:hover:not(:disabled) {
    background: #ffa726;
  }

  .btn.all-in {
    background: #e94560;
    color: white;
  }

  .btn.all-in:hover:not(:disabled) {
    background: #ff6b6b;
  }

  .raise-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: center;
  }

  .raise-slider {
    width: 100%;
    max-width: 300px;
  }

  .raise-slider input {
    width: 100%;
    height: 8px;
    -webkit-appearance: none;
    background: #0f3460;
    border-radius: 4px;
    outline: none;
  }

  .raise-slider input::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    background: #ff9800;
    border-radius: 50%;
    cursor: pointer;
  }

  .raise-labels {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 0.8rem;
    color: #888;
    margin-top: 0.25rem;
  }

  .raise-amount {
    color: #ff9800;
    font-weight: bold;
  }
</style>
