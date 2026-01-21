from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json

from .db import connect_db, disconnect_db, create_tables, database


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

# Store connected websocket clients
connected_clients: list[WebSocket] = []


@app.get("/api/health")
async def health_check():
    db_status = "connected" if database and database.is_connected else "not connected"
    return {"status": "ok", "message": "Backend is running", "database": db_status}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # Echo back with server acknowledgment
            response = {"type": "echo", "received": message}
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


# Serve static files from frontend build
static_dir = Path(__file__).parent.parent.parent / "frontend" / "build"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "Frontend not built yet. Run build.sh first."}
