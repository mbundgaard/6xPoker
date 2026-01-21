<script lang="ts">
  import Card from './Card.svelte';

  interface CardData {
    rank: string;
    suit: string;
  }

  interface Props {
    cards: CardData[];
  }

  let { cards }: Props = $props();
</script>

<div class="community-cards">
  {#each { length: 5 } as _, i}
    {#if cards[i]}
      <Card card={cards[i]} />
    {:else}
      <div class="card-placeholder"></div>
    {/if}
  {/each}
</div>

<style>
  .community-cards {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
  }

  .card-placeholder {
    width: 50px;
    height: 70px;
    border: 2px dashed #0f3460;
    border-radius: 6px;
    opacity: 0.3;
  }
</style>
