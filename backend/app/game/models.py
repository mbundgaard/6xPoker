from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class GameStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"


@dataclass
class GamePlayer:
    nickname: str
    chips: int = 0
    is_eliminated: bool = False
    elimination_position: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "nickname": self.nickname,
            "chips": self.chips,
            "is_eliminated": self.is_eliminated,
            "elimination_position": self.elimination_position,
        }


@dataclass
class Game:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creator: str = ""
    status: GameStatus = GameStatus.WAITING
    players: list[GamePlayer] = field(default_factory=list)
    current_hand: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "creator": self.creator,
            "status": self.status.value,
            "players": [p.to_dict() for p in self.players],
            "player_count": len(self.players),
            "current_hand": self.current_hand,
            "created_at": self.created_at.isoformat(),
        }

    def add_player(self, nickname: str, starting_chips: int) -> GamePlayer:
        player = GamePlayer(nickname=nickname, chips=starting_chips)
        self.players.append(player)
        return player

    def get_player(self, nickname: str) -> Optional[GamePlayer]:
        for player in self.players:
            if player.nickname == nickname:
                return player
        return None

    def has_player(self, nickname: str) -> bool:
        return self.get_player(nickname) is not None
