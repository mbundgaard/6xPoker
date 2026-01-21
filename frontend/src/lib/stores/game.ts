// Game store - simple reactive store without runes
console.log('[GameStore] Module loading');

export interface GamePlayer {
  nickname: string;
  chips: number;
  is_eliminated: boolean;
  elimination_position: number | null;
}

export interface Game {
  id: string;
  creator: string;
  status: 'waiting' | 'active' | 'finished';
  players: GamePlayer[];
  player_count: number;
  current_hand_num: number;
  dealer_position: number;
  created_at: string;
  active_hand?: any;
}

type Subscriber = () => void;

class GameStore {
  private _currentGame: Game | null = null;
  private _waitingGames: Game[] = [];
  private subscribers: Set<Subscriber> = new Set();

  get currentGame(): Game | null {
    return this._currentGame;
  }

  set currentGame(game: Game | null) {
    this._currentGame = game;
    this.notify();
  }

  get waitingGames(): Game[] {
    return this._waitingGames;
  }

  set waitingGames(games: Game[]) {
    this._waitingGames = games;
    this.notify();
  }

  updateGame(game: Game) {
    this._currentGame = game;
    this.notify();
  }

  clear() {
    this._currentGame = null;
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

export const gameStore = new GameStore();
console.log('[GameStore] Store created');
