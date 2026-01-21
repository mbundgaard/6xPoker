from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import json

from ..game import game_manager, GameStatus


class ConnectionManager:
    """Manages WebSocket connections for games and lobby."""

    def __init__(self):
        # game_id -> {nickname -> WebSocket}
        self._game_connections: dict[str, dict[str, WebSocket]] = {}
        # Lobby subscribers (not in a game yet)
        self._lobby_connections: list[WebSocket] = []

    async def connect_to_lobby(self, websocket: WebSocket):
        """Add a connection to the lobby."""
        await websocket.accept()
        self._lobby_connections.append(websocket)

    def disconnect_from_lobby(self, websocket: WebSocket):
        """Remove a connection from the lobby."""
        if websocket in self._lobby_connections:
            self._lobby_connections.remove(websocket)

    async def connect_to_game(self, websocket: WebSocket, game_id: str, nickname: str) -> Optional[str]:
        """
        Connect a player to a game's WebSocket channel.
        Returns error message if connection fails, None on success.
        """
        game = game_manager.get_game(game_id)
        if not game:
            return "Game not found"

        if not game.has_player(nickname):
            return "You are not a player in this game"

        await websocket.accept()

        if game_id not in self._game_connections:
            self._game_connections[game_id] = {}

        self._game_connections[game_id][nickname] = websocket
        return None

    def disconnect_from_game(self, game_id: str, nickname: str):
        """Remove a player's connection from a game."""
        if game_id in self._game_connections:
            if nickname in self._game_connections[game_id]:
                del self._game_connections[game_id][nickname]
            if not self._game_connections[game_id]:
                del self._game_connections[game_id]

    async def broadcast_to_lobby(self, message: dict):
        """Send a message to all lobby subscribers."""
        dead_connections = []
        for websocket in self._lobby_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(websocket)
        for ws in dead_connections:
            self._lobby_connections.remove(ws)

    async def broadcast_to_game(self, game_id: str, message: dict, exclude_nickname: Optional[str] = None):
        """Send a message to all players in a game."""
        if game_id not in self._game_connections:
            return

        dead_connections = []
        for nickname, websocket in self._game_connections[game_id].items():
            if nickname == exclude_nickname:
                continue
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(nickname)

        for nickname in dead_connections:
            del self._game_connections[game_id][nickname]

    async def send_to_player(self, game_id: str, nickname: str, message: dict):
        """Send a message to a specific player in a game."""
        if game_id not in self._game_connections:
            return
        if nickname not in self._game_connections[game_id]:
            return

        try:
            await self._game_connections[game_id][nickname].send_text(json.dumps(message))
        except Exception:
            del self._game_connections[game_id][nickname]

    def get_game_connections(self, game_id: str) -> dict[str, WebSocket]:
        """Get all connections for a game."""
        return self._game_connections.get(game_id, {})


# Singleton instance
connection_manager = ConnectionManager()


async def handle_game_message(game_id: str, nickname: str, message: dict):
    """Process a message from a player in a game."""
    msg_type = message.get("type")

    if msg_type == "start_game":
        game, error = game_manager.start_game(game_id, nickname)
        if error:
            await connection_manager.send_to_player(game_id, nickname, {
                "type": "error",
                "payload": {"message": error}
            })
        else:
            # Notify all players the game started
            await connection_manager.broadcast_to_game(game_id, {
                "type": "game_started",
                "payload": {
                    "game": game.to_dict(),
                    "message": "Game has started!"
                }
            })
            # Notify lobby that game is no longer available
            await connection_manager.broadcast_to_lobby({
                "type": "lobby_update",
                "payload": {
                    "games": [g.to_dict() for g in game_manager.list_waiting_games()]
                }
            })

    elif msg_type == "action":
        # Will be implemented in Phase 5/6
        await connection_manager.send_to_player(game_id, nickname, {
            "type": "error",
            "payload": {"message": "Game actions not yet implemented"}
        })

    else:
        await connection_manager.send_to_player(game_id, nickname, {
            "type": "error",
            "payload": {"message": f"Unknown message type: {msg_type}"}
        })
