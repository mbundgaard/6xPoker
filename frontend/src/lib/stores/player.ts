// Player store - simple reactive store without runes

type Subscriber = () => void;

class PlayerStore {
  private _nickname: string | null = null;
  private subscribers: Set<Subscriber> = new Set();

  get nickname(): string | null {
    return this._nickname;
  }

  set nickname(value: string | null) {
    this._nickname = value;
    this.notify();
  }

  subscribe(callback: Subscriber): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  private notify() {
    this.subscribers.forEach(cb => cb());
  }
}

export const playerStore = new PlayerStore();
