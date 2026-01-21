// Game store - manages game state from WebSocket updates

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

function createGameStore() {
  let currentGame = $state<Game | null>(null);
  let waitingGames = $state<Game[]>([]);

  return {
    get currentGame() {
      return currentGame;
    },
    set currentGame(game: Game | null) {
      currentGame = game;
    },
    get waitingGames() {
      return waitingGames;
    },
    set waitingGames(games: Game[]) {
      waitingGames = games;
    },
    updateGame(game: Game) {
      currentGame = game;
    },
    clear() {
      currentGame = null;
    }
  };
}

export const gameStore = createGameStore();
