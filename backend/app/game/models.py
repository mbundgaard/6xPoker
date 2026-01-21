from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .poker import Card


class GameStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"


class BettingRound(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


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
class PlayerHand:
    """Tracks a player's state within a single hand."""
    nickname: str
    hole_cards: list = field(default_factory=list)  # list[Card]
    current_bet: int = 0  # Bet in current round
    total_bet: int = 0  # Total bet this hand (for side pots)
    folded: bool = False
    is_all_in: bool = False

    def to_dict(self, show_cards: bool = False) -> dict:
        return {
            "nickname": self.nickname,
            "hole_cards": [c.to_dict() for c in self.hole_cards] if show_cards else None,
            "current_bet": self.current_bet,
            "total_bet": self.total_bet,
            "folded": self.folded,
            "is_all_in": self.is_all_in,
        }


@dataclass
class Pot:
    """Represents a pot (main or side pot)."""
    amount: int = 0
    eligible_players: list[str] = field(default_factory=list)  # nicknames

    def to_dict(self) -> dict:
        return {
            "amount": self.amount,
            "eligible_players": self.eligible_players,
        }


@dataclass
class Hand:
    """Tracks the state of a single hand being played."""
    hand_number: int = 0
    dealer_position: int = 0
    community_cards: list = field(default_factory=list)  # list[Card]
    pots: list[Pot] = field(default_factory=list)
    current_bet: int = 0  # Current bet to call
    min_raise: int = 0  # Minimum raise amount
    betting_round: BettingRound = BettingRound.PREFLOP
    current_player_idx: int = 0
    player_hands: dict[str, PlayerHand] = field(default_factory=dict)  # nickname -> PlayerHand
    last_raiser: Optional[str] = None
    players_acted_this_round: set = field(default_factory=set)

    def to_dict(self, viewer_nickname: Optional[str] = None) -> dict:
        """Convert to dict. Only show hole cards to the viewer."""
        return {
            "hand_number": self.hand_number,
            "dealer_position": self.dealer_position,
            "community_cards": [c.to_dict() for c in self.community_cards],
            "pots": [p.to_dict() for p in self.pots],
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "betting_round": self.betting_round.value,
            "current_player_idx": self.current_player_idx,
            "player_hands": {
                nick: ph.to_dict(show_cards=(nick == viewer_nickname))
                for nick, ph in self.player_hands.items()
            },
        }

    def get_total_pot(self) -> int:
        """Get total of all pots."""
        return sum(p.amount for p in self.pots)


@dataclass
class Game:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creator: str = ""
    status: GameStatus = GameStatus.WAITING
    players: list[GamePlayer] = field(default_factory=list)
    current_hand_num: int = 0
    dealer_position: int = 0
    elimination_order: list[str] = field(default_factory=list)  # nicknames in elimination order
    active_hand: Optional[Hand] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self, viewer_nickname: Optional[str] = None) -> dict:
        result = {
            "id": self.id,
            "creator": self.creator,
            "status": self.status.value,
            "players": [p.to_dict() for p in self.players],
            "player_count": len(self.players),
            "current_hand_num": self.current_hand_num,
            "dealer_position": self.dealer_position,
            "created_at": self.created_at.isoformat(),
        }
        if self.active_hand:
            result["active_hand"] = self.active_hand.to_dict(viewer_nickname)
        return result

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

    def get_active_players(self) -> list[GamePlayer]:
        """Get players who are not eliminated."""
        return [p for p in self.players if not p.is_eliminated]

    def get_player_position(self, nickname: str) -> int:
        """Get position index of a player."""
        for i, p in enumerate(self.players):
            if p.nickname == nickname:
                return i
        return -1
