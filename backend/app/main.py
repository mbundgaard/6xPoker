from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json

from .db import connect_db, disconnect_db, create_tables, database
from .api import router, connection_manager, handle_game_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    if database:
        await create_tables()
    yield
    # Shutdown
    await disconnect_db()


app = FastAPI(lifespan=lifespan)
app.include_router(router)

@app.get("/api/health")
async def health_check():
    db_status = "connected" if database and database.is_connected else "not connected"
    return {"status": "ok", "message": "Backend is running", "database": db_status}


@app.websocket("/ws/lobby")
async def lobby_websocket(websocket: WebSocket):
    """WebSocket for lobby updates (game list changes)."""
    await connection_manager.connect_to_lobby(websocket)
    try:
        while True:
            # Lobby connections just receive updates, no messages expected
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect_from_lobby(websocket)


@app.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str, nickname: str):
    """WebSocket for game communication."""
    error = await connection_manager.connect_to_game(websocket, game_id, nickname)
    if error:
        await websocket.close(code=4000, reason=error)
        return

    # Send current game state on connect
    from .game import game_manager
    game = game_manager.get_game(game_id)
    if game:
        await websocket.send_text(json.dumps({
            "type": "game_joined",
            "payload": {"game": game.to_dict()}
        }))
        # Notify others that player connected
        await connection_manager.broadcast_to_game(game_id, {
            "type": "player_connected",
            "payload": {"nickname": nickname}
        }, exclude_nickname=nickname)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_game_message(game_id, nickname, message)
    except WebSocketDisconnect:
        connection_manager.disconnect_from_game(game_id, nickname)
        # Notify others that player disconnected
        await connection_manager.broadcast_to_game(game_id, {
            "type": "player_disconnected",
            "payload": {"nickname": nickname}
        })


# Serve static files from frontend build
static_dir = Path(__file__).parent.parent.parent / "frontend" / "build"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "Frontend not built yet. Run build.sh first."}
