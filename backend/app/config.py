import os

# Game settings
STARTING_CHIPS = 1000
SMALL_BLIND = 10
BIG_BLIND = 20
HAND_LIMIT = 50
TURN_TIMER_SECONDS = 30

# Player limits
MIN_PLAYERS = 2
MAX_PLAYERS = 4

# Points awarded by placement (1st place = index 0)
POINTS_BY_PLACEMENT = [10, 5, 2, 1]

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert Render's postgres:// to postgresql:// for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
