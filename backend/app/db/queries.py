from .database import database

CREATE_TABLES_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS game_results (
        id VARCHAR(36) PRIMARY KEY,
        played_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_result_players (
        id VARCHAR(36) PRIMARY KEY,
        game_result_id VARCHAR(36) NOT NULL REFERENCES game_results(id) ON DELETE CASCADE,
        nickname VARCHAR(50) NOT NULL,
        placement INTEGER NOT NULL,
        points_awarded INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_game_result_players_nickname ON game_result_players(nickname)",
    "CREATE INDEX IF NOT EXISTS idx_game_result_players_game_result_id ON game_result_players(game_result_id)",
]


async def create_tables():
    """Create database tables if they don't exist."""
    if database:
        for statement in CREATE_TABLES_STATEMENTS:
            await database.execute(statement)


async def get_leaderboard(limit: int = 100):
    """Get all-time leaderboard sorted by total points."""
    if not database:
        return []

    query = """
        SELECT
            nickname,
            SUM(points_awarded) as total_points,
            COUNT(*) as games_played
        FROM game_result_players
        GROUP BY nickname
        ORDER BY total_points DESC
        LIMIT :limit
    """
    rows = await database.fetch_all(query=query, values={"limit": limit})
    return [dict(row._mapping) for row in rows]
