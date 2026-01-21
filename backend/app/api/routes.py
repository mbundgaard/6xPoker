from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..game import game_manager

router = APIRouter(prefix="/api")


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
async def create_game(request: CreateGameRequest):
    """Create a new game."""
    nickname = request.nickname.strip().lower()
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname is required")

    game = game_manager.create_game(nickname)
    return {"game": game.to_dict()}


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get a specific game by ID."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game": game.to_dict()}


@router.post("/games/{game_id}/join")
async def join_game(game_id: str, request: JoinGameRequest):
    """Join an existing game."""
    nickname = request.nickname.strip().lower()
    if not nickname:
        raise HTTPException(status_code=400, detail="Nickname is required")

    game, error = game_manager.join_game(game_id, nickname)
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"game": game.to_dict()}
