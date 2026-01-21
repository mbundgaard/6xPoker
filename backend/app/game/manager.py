from typing import Optional
from .models import Game, GamePlayer, GameStatus
from ..config import STARTING_CHIPS, MIN_PLAYERS, MAX_PLAYERS


class GameManager:
    """Manages all active games in memory."""

    def __init__(self):
        self._games: dict[str, Game] = {}

    def create_game(self, creator_nickname: str) -> Game:
        """Create a new game and add the creator as the first player."""
        game = Game(creator=creator_nickname)
        game.add_player(creator_nickname, STARTING_CHIPS)
        self._games[game.id] = game
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        return self._games.get(game_id)

    def join_game(self, game_id: str, nickname: str) -> tuple[Optional[Game], Optional[str]]:
        """
        Join an existing game.
        Returns (game, error_message). If successful, error_message is None.
        """
        game = self.get_game(game_id)
        if not game:
            return None, "Game not found"

        if game.status != GameStatus.WAITING:
            return None, "Game has already started"

        if len(game.players) >= MAX_PLAYERS:
            return None, f"Game is full (max {MAX_PLAYERS} players)"

        if game.has_player(nickname):
            return None, "A player with this nickname is already in the game"

        game.add_player(nickname, STARTING_CHIPS)
        return game, None

    def start_game(self, game_id: str, nickname: str) -> tuple[Optional[Game], Optional[str]]:
        """
        Start a game. Only the creator can start it.
        Returns (game, error_message). If successful, error_message is None.
        """
        game = self.get_game(game_id)
        if not game:
            return None, "Game not found"

        if game.creator != nickname:
            return None, "Only the creator can start the game"

        if game.status != GameStatus.WAITING:
            return None, "Game has already started"

        if len(game.players) < MIN_PLAYERS:
            return None, f"Need at least {MIN_PLAYERS} players to start"

        game.status = GameStatus.ACTIVE
        game.current_hand = 1
        return game, None

    def list_waiting_games(self) -> list[Game]:
        """Get all games that are waiting for players."""
        return [g for g in self._games.values() if g.status == GameStatus.WAITING]

    def remove_game(self, game_id: str) -> bool:
        """Remove a game from the manager."""
        if game_id in self._games:
            del self._games[game_id]
            return True
        return False


# Singleton instance
game_manager = GameManager()
