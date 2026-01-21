<script lang="ts">
  interface Props {
    seconds: number;
    maxSeconds?: number;
  }

  let { seconds, maxSeconds = 30 }: Props = $props();

  const percentage = $derived(Math.max(0, Math.min(100, (seconds / maxSeconds) * 100)));
  const isLow = $derived(seconds <= 10);
  const isCritical = $derived(seconds <= 5);
</script>

<div class="timer" class:low={isLow} class:critical={isCritical}>
  <div class="timer-bar" style="width: {percentage}%"></div>
  <span class="timer-text">{seconds}s</span>
</div>

<style>
  .timer {
    position: relative;
    width: 100%;
    height: 24px;
    background: #0f3460;
    border-radius: 12px;
    overflow: hidden;
  }

  .timer-bar {
    height: 100%;
    background: #4caf50;
    transition: width 0.5s linear;
  }

  .timer.low .timer-bar {
    background: #ff9800;
  }

  .timer.critical .timer-bar {
    background: #f44336;
    animation: pulse 0.5s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .timer-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.85rem;
    font-weight: bold;
    color: white;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }
</style>
