from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..game import game_manager
from .websocket import connection_manager

router = APIRouter(prefix="/api")


async def broadcast_lobby_update():
    """Broadcast updated game list to all lobby subscribers."""
    games = game_manager.list_waiting_games()
    await connection_manager.broadcast_to_lobby({
        "type": "lobby_update",
        "payload": {"games": [g.to_dict() for g in games]}
    })


class CreateGameRequest(BaseModel):
    nickname: str


class JoinGameRequest(BaseModel):
    nickname: str


@router.get("/games")
async def list_games():
    """List all games waiting for players."""
    games = game_manager.list_waiting_games()
    return {"games": [g.to_dict() for g in games]}


@router.post("/games")
async def create_game(request: CreateGameRequest, background_tasks: BackgroundTasks):
    """Create a new game."""
    nickname = request.nickname.strip().lower()
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname is required")

    game = game_manager.create_game(nickname)
    background_tasks.add_task(broadcast_lobby_update)
    return {"game": game.to_dict()}


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get a specific game by ID."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game": game.to_dict()}


@router.post("/games/{game_id}/join")
async def join_game(game_id: str, request: JoinGameRequest, background_tasks: BackgroundTasks):
    """Join an existing game."""
    nickname = request.nickname.strip().lower()
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname is required")

    game, error = game_manager.join_game(game_id, nickname)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Notify lobby of player count change
    background_tasks.add_task(broadcast_lobby_update)

    # Notify players already in the game
    async def notify_game_players():
        await connection_manager.broadcast_to_game(game_id, {
            "type": "player_joined",
            "payload": {
                "nickname": nickname,
                "game": game.to_dict()
            }
        })

    background_tasks.add_task(notify_game_players)

    return {"game": game.to_dict()}
