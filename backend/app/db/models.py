import sqlalchemy
from datetime import datetime

metadata = sqlalchemy.MetaData()

game_results = sqlalchemy.Table(
    "game_results",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String(36), primary_key=True),
    sqlalchemy.Column("played_at", sqlalchemy.DateTime, default=datetime.utcnow, nullable=False),
)

game_result_players = sqlalchemy.Table(
    "game_result_players",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String(36), primary_key=True),
    sqlalchemy.Column(
        "game_result_id",
        sqlalchemy.String(36),
        sqlalchemy.ForeignKey("game_results.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sqlalchemy.Column("nickname", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("placement", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("points_awarded", sqlalchemy.Integer, nullable=False),
)
