"""Tests for poker hand evaluation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.game.poker import (
    Card, Rank, Suit, Deck, HandRank,
    evaluate_hand, evaluate_five_cards, compare_hands
)


def make_card(rank_str: str, suit_str: str) -> Card:
    """Helper to create cards from strings like 'A', 'K', '10' and 'h', 's', 'd', 'c'."""
    rank_map = {
        "2": Rank.TWO, "3": Rank.THREE, "4": Rank.FOUR, "5": Rank.FIVE,
        "6": Rank.SIX, "7": Rank.SEVEN, "8": Rank.EIGHT, "9": Rank.NINE,
        "10": Rank.TEN, "J": Rank.JACK, "Q": Rank.QUEEN, "K": Rank.KING, "A": Rank.ACE
    }
    suit_map = {"c": Suit.CLUBS, "d": Suit.DIAMONDS, "h": Suit.HEARTS, "s": Suit.SPADES}
    return Card(rank_map[rank_str], suit_map[suit_str])


def make_hand(cards_str: str) -> list[Card]:
    """Helper to create hands from strings like 'Ah Kh Qh Jh 10h'."""
    cards = []
    for card_str in cards_str.split():
        suit = card_str[-1]
        rank = card_str[:-1]
        cards.append(make_card(rank, suit))
    return cards


def test_deck():
    """Test deck initialization and dealing."""
    deck = Deck()
    assert len(deck) == 52

    deck.shuffle()
    assert len(deck) == 52

    cards = deck.deal(5)
    assert len(cards) == 5
    assert len(deck) == 47

    card = deck.deal_one()
    assert isinstance(card, Card)
    assert len(deck) == 46


def test_high_card():
    """Test high card hands."""
    hand = make_hand("Ah Kd Qc Jh 9s")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.HIGH_CARD
    assert result.values[0] == Rank.ACE


def test_pair():
    """Test pair detection."""
    hand = make_hand("Ah Ad Kc Qh Js")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.PAIR
    assert result.values[0] == Rank.ACE


def test_two_pair():
    """Test two pair detection."""
    hand = make_hand("Ah Ad Kc Kh Js")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.TWO_PAIR
    assert result.values[0] == Rank.ACE
    assert result.values[1] == Rank.KING


def test_three_of_a_kind():
    """Test three of a kind detection."""
    hand = make_hand("Ah Ad Ac Kh Js")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.THREE_OF_A_KIND
    assert result.values[0] == Rank.ACE


def test_straight():
    """Test straight detection."""
    hand = make_hand("Ah Kd Qc Jh 10s")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.STRAIGHT
    assert result.values[0] == Rank.ACE


def test_wheel_straight():
    """Test A-2-3-4-5 (wheel) straight."""
    hand = make_hand("Ah 2d 3c 4h 5s")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.STRAIGHT
    assert result.values[0] == Rank.FIVE  # 5-high straight


def test_flush():
    """Test flush detection."""
    hand = make_hand("Ah Kh Qh Jh 9h")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.FLUSH
    assert result.values[0] == Rank.ACE


def test_full_house():
    """Test full house detection."""
    hand = make_hand("Ah Ad Ac Kh Ks")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.FULL_HOUSE
    assert result.values[0] == Rank.ACE
    assert result.values[1] == Rank.KING


def test_four_of_a_kind():
    """Test four of a kind detection."""
    hand = make_hand("Ah Ad Ac As Kh")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.FOUR_OF_A_KIND
    assert result.values[0] == Rank.ACE


def test_straight_flush():
    """Test straight flush detection."""
    hand = make_hand("Ah Kh Qh Jh 10h")
    result = evaluate_five_cards(hand)
    assert result.rank == HandRank.STRAIGHT_FLUSH
    assert result.values[0] == Rank.ACE


def test_hand_comparison():
    """Test that higher hands beat lower hands."""
    high_card = make_hand("Ah Kd Qc Jh 9s")
    pair = make_hand("Ah Ad Kc Qh Js")
    flush = make_hand("Ah Kh Qh Jh 9h")

    hc_result = evaluate_five_cards(high_card)
    pair_result = evaluate_five_cards(pair)
    flush_result = evaluate_five_cards(flush)

    assert pair_result > hc_result
    assert flush_result > pair_result
    assert flush_result > hc_result


def test_tiebreaker_high_card():
    """Test high card tiebreaker - higher kickers win."""
    hand1 = make_hand("Ah Kd Qc Jh 9s")
    hand2 = make_hand("Ah Kd Qc Jh 8s")

    result1 = evaluate_five_cards(hand1)
    result2 = evaluate_five_cards(hand2)

    assert result1 > result2


def test_tiebreaker_pair():
    """Test pair tiebreaker - higher pair wins."""
    hand1 = make_hand("Ah Ad Kc Qh Js")  # Pair of Aces
    hand2 = make_hand("Kh Kd Ac Qh Js")  # Pair of Kings

    result1 = evaluate_five_cards(hand1)
    result2 = evaluate_five_cards(hand2)

    assert result1 > result2


def test_seven_card_evaluation():
    """Test finding best 5 cards from 7."""
    # 7 cards with a hidden flush
    cards = make_hand("Ah Kh Qh Jh 9h 2c 3d")
    result = evaluate_hand(cards)
    assert result.rank == HandRank.FLUSH


def test_compare_hands_winner():
    """Test comparing multiple hands to find winner."""
    hand1 = make_hand("Ah Ad Kc Qh Js 2c 3d")  # Pair of Aces
    hand2 = make_hand("Kh Kd Ac Qh Js 2c 3d")  # Pair of Kings
    hand3 = make_hand("Qh Qd Ac Kh Js 2c 3d")  # Pair of Queens

    winners = compare_hands([hand1, hand2, hand3])
    assert winners == [0]  # hand1 (pair of Aces) wins


def test_compare_hands_tie():
    """Test that ties are detected."""
    # Two identical high card hands (different suits don't matter)
    hand1 = make_hand("Ah Kd Qc Jh 9s")
    hand2 = make_hand("As Kc Qd Js 9h")

    winners = compare_hands([hand1, hand2])
    assert winners == [0, 1]  # Tie


if __name__ == "__main__":
    # Run all tests
    test_deck()
    test_high_card()
    test_pair()
    test_two_pair()
    test_three_of_a_kind()
    test_straight()
    test_wheel_straight()
    test_flush()
    test_full_house()
    test_four_of_a_kind()
    test_straight_flush()
    test_hand_comparison()
    test_tiebreaker_high_card()
    test_tiebreaker_pair()
    test_seven_card_evaluation()
    test_compare_hands_winner()
    test_compare_hands_tie()
    print("All poker tests passed!")
