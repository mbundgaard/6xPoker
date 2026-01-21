from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations
import random
from typing import Optional


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    def __str__(self):
        return ["♣", "♦", "♥", "♠"][self.value]


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self):
        if self.value <= 10:
            return str(self.value)
        return {11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]


class HandRank(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def to_dict(self) -> dict:
        return {"rank": self.rank.value, "suit": self.suit.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(rank=Rank(data["rank"]), suit=Suit(data["suit"]))


class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        self.reset()

    def reset(self):
        """Reset deck to full 52 cards."""
        self.cards = [
            Card(rank=rank, suit=suit)
            for suit in Suit
            for rank in Rank
        ]

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, count: int = 1) -> list[Card]:
        """Deal cards from the top of the deck."""
        if count > len(self.cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self.cards)} remaining")
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt

    def deal_one(self) -> Card:
        """Deal a single card."""
        return self.deal(1)[0]

    def __len__(self):
        return len(self.cards)


@dataclass
class HandResult:
    """Result of evaluating a poker hand."""
    rank: HandRank
    values: tuple  # Tiebreaker values (highest first)
    cards: list[Card]  # The 5 cards that make the hand

    def __lt__(self, other: "HandResult") -> bool:
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.values < other.values

    def __eq__(self, other: "HandResult") -> bool:
        return self.rank == other.rank and self.values == other.values

    def __le__(self, other: "HandResult") -> bool:
        return self < other or self == other

    def __gt__(self, other: "HandResult") -> bool:
        return other < self

    def __ge__(self, other: "HandResult") -> bool:
        return other <= self

    def to_dict(self) -> dict:
        return {
            "rank": self.rank.value,
            "rank_name": self.rank.name.replace("_", " ").title(),
            "cards": [c.to_dict() for c in self.cards],
        }


def evaluate_five_cards(cards: list[Card]) -> HandResult:
    """Evaluate exactly 5 cards and return the hand result."""
    assert len(cards) == 5, "Must evaluate exactly 5 cards"

    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    # Check for flush
    is_flush = len(set(suits)) == 1

    # Check for straight
    is_straight = False
    straight_high = None

    # Normal straight check
    if ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5:
        is_straight = True
        straight_high = ranks[0]

    # Wheel (A-2-3-4-5) - Ace counts as 1
    if set(ranks) == {Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE}:
        is_straight = True
        straight_high = Rank.FIVE  # 5-high straight

    # Count rank occurrences
    rank_counts: dict[Rank, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    # Sort by count (desc) then by rank (desc)
    sorted_counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    counts = [c for _, c in sorted_counts]
    sorted_ranks = [r for r, _ in sorted_counts]

    # Determine hand rank
    if is_straight and is_flush:
        return HandResult(HandRank.STRAIGHT_FLUSH, (straight_high,), cards)

    if counts == [4, 1]:
        return HandResult(HandRank.FOUR_OF_A_KIND, (sorted_ranks[0], sorted_ranks[1]), cards)

    if counts == [3, 2]:
        return HandResult(HandRank.FULL_HOUSE, (sorted_ranks[0], sorted_ranks[1]), cards)

    if is_flush:
        return HandResult(HandRank.FLUSH, tuple(ranks), cards)

    if is_straight:
        return HandResult(HandRank.STRAIGHT, (straight_high,), cards)

    if counts == [3, 1, 1]:
        kickers = sorted([r for r in sorted_ranks[1:]], reverse=True)
        return HandResult(HandRank.THREE_OF_A_KIND, (sorted_ranks[0],) + tuple(kickers), cards)

    if counts == [2, 2, 1]:
        pairs = sorted([sorted_ranks[0], sorted_ranks[1]], reverse=True)
        return HandResult(HandRank.TWO_PAIR, (pairs[0], pairs[1], sorted_ranks[2]), cards)

    if counts == [2, 1, 1, 1]:
        kickers = sorted([r for r in sorted_ranks[1:]], reverse=True)
        return HandResult(HandRank.PAIR, (sorted_ranks[0],) + tuple(kickers), cards)

    return HandResult(HandRank.HIGH_CARD, tuple(ranks), cards)


def evaluate_hand(cards: list[Card]) -> HandResult:
    """
    Evaluate the best 5-card hand from any number of cards (typically 7).
    Returns the best possible HandResult.
    """
    if len(cards) < 5:
        raise ValueError(f"Need at least 5 cards, got {len(cards)}")

    if len(cards) == 5:
        return evaluate_five_cards(cards)

    # Try all 5-card combinations and return the best
    best: Optional[HandResult] = None
    for combo in combinations(cards, 5):
        result = evaluate_five_cards(list(combo))
        if best is None or result > best:
            best = result

    return best


def compare_hands(hands: list[list[Card]]) -> list[int]:
    """
    Compare multiple hands and return indices of winners (can be multiple for ties).
    """
    results = [evaluate_hand(hand) for hand in hands]
    best_result = max(results)
    return [i for i, r in enumerate(results) if r == best_result]
