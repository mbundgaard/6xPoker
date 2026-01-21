"""Player actions for poker betting."""

from typing import Optional, Tuple
from .models import Game, Hand, PlayerHand, BettingRound, Pot
from ..config import BIG_BLIND


class ActionError(Exception):
    """Raised when an action is invalid."""
    pass


def get_current_player_nickname(game: Game) -> Optional[str]:
    """Get the nickname of the player whose turn it is."""
    if not game.active_hand:
        return None

    active_players = game.get_active_players()
    hand = game.active_hand

    # Find players still in the hand (not folded, not all-in)
    players_in_hand = [
        p for p in active_players
        if p.nickname in hand.player_hands
        and not hand.player_hands[p.nickname].folded
        and not hand.player_hands[p.nickname].is_all_in
    ]

    if not players_in_hand:
        return None

    # Current player based on index
    idx = hand.current_player_idx % len(players_in_hand)
    return players_in_hand[idx].nickname


def validate_turn(game: Game, nickname: str) -> None:
    """Validate that it's the player's turn."""
    current = get_current_player_nickname(game)
    if current != nickname:
        raise ActionError(f"Not your turn. Waiting for {current}")


def get_valid_actions(game: Game, nickname: str) -> dict:
    """Get valid actions for a player."""
    if not game.active_hand:
        return {}

    hand = game.active_hand
    player_hand = hand.player_hands.get(nickname)
    game_player = game.get_player(nickname)

    if not player_hand or not game_player:
        return {}

    if player_hand.folded or player_hand.is_all_in:
        return {}

    current = get_current_player_nickname(game)
    if current != nickname:
        return {}

    actions = {"fold": True}

    to_call = hand.current_bet - player_hand.current_bet

    if to_call == 0:
        actions["check"] = True
    else:
        actions["call"] = min(to_call, game_player.chips)

    # Raise: minimum is current bet + min_raise
    min_raise_total = hand.current_bet + hand.min_raise
    min_raise_amount = min_raise_total - player_hand.current_bet

    if game_player.chips > to_call:
        actions["raise"] = {
            "min": min(min_raise_amount, game_player.chips),
            "max": game_player.chips,
        }

    # All-in is always available
    actions["all_in"] = game_player.chips

    return actions


def fold(game: Game, nickname: str) -> None:
    """Player folds their hand."""
    validate_turn(game, nickname)

    hand = game.active_hand
    player_hand = hand.player_hands[nickname]
    player_hand.folded = True
    hand.players_acted_this_round.add(nickname)

    advance_action(game)


def check(game: Game, nickname: str) -> None:
    """Player checks (no bet)."""
    validate_turn(game, nickname)

    hand = game.active_hand
    player_hand = hand.player_hands[nickname]

    to_call = hand.current_bet - player_hand.current_bet
    if to_call > 0:
        raise ActionError(f"Cannot check, must call {to_call} or fold")

    hand.players_acted_this_round.add(nickname)
    advance_action(game)


def call(game: Game, nickname: str) -> int:
    """Player calls the current bet. Returns amount called."""
    validate_turn(game, nickname)

    hand = game.active_hand
    player_hand = hand.player_hands[nickname]
    game_player = game.get_player(nickname)

    to_call = hand.current_bet - player_hand.current_bet

    if to_call <= 0:
        raise ActionError("Nothing to call, use check instead")

    # If player doesn't have enough, they go all-in
    actual_call = min(to_call, game_player.chips)

    game_player.chips -= actual_call
    player_hand.current_bet += actual_call
    player_hand.total_bet += actual_call

    if game_player.chips == 0:
        player_hand.is_all_in = True

    hand.players_acted_this_round.add(nickname)
    advance_action(game)

    return actual_call


def raise_bet(game: Game, nickname: str, total_amount: int) -> int:
    """
    Player raises. total_amount is the total bet they want to make this round.
    Returns the amount added to the pot.
    """
    validate_turn(game, nickname)

    hand = game.active_hand
    player_hand = hand.player_hands[nickname]
    game_player = game.get_player(nickname)

    # Calculate how much more they need to put in
    additional = total_amount - player_hand.current_bet

    if additional <= 0:
        raise ActionError("Raise amount must be more than current bet")

    if additional > game_player.chips:
        raise ActionError(f"Not enough chips. You have {game_player.chips}")

    # Minimum raise check
    min_raise_total = hand.current_bet + hand.min_raise
    if total_amount < min_raise_total and additional < game_player.chips:
        raise ActionError(f"Minimum raise is to {min_raise_total}")

    # Calculate the raise amount (how much above current bet)
    raise_amount = total_amount - hand.current_bet

    game_player.chips -= additional
    player_hand.current_bet = total_amount
    player_hand.total_bet += additional

    # Update hand state
    hand.min_raise = max(hand.min_raise, raise_amount)
    hand.current_bet = total_amount
    hand.last_raiser = nickname

    # Reset who needs to act (everyone except raiser who hasn't folded/all-in)
    hand.players_acted_this_round = {nickname}

    if game_player.chips == 0:
        player_hand.is_all_in = True

    advance_action(game)

    return additional


def all_in(game: Game, nickname: str) -> int:
    """Player goes all-in. Returns amount bet."""
    validate_turn(game, nickname)

    hand = game.active_hand
    player_hand = hand.player_hands[nickname]
    game_player = game.get_player(nickname)

    amount = game_player.chips
    if amount == 0:
        raise ActionError("No chips to go all-in with")

    new_total = player_hand.current_bet + amount

    game_player.chips = 0
    player_hand.current_bet = new_total
    player_hand.total_bet += amount
    player_hand.is_all_in = True

    # If this is a raise
    if new_total > hand.current_bet:
        raise_amount = new_total - hand.current_bet
        hand.min_raise = max(hand.min_raise, raise_amount)
        hand.current_bet = new_total
        hand.last_raiser = nickname
        # Reset who needs to act
        hand.players_acted_this_round = {nickname}
    else:
        hand.players_acted_this_round.add(nickname)

    advance_action(game)

    return amount


def advance_action(game: Game) -> None:
    """
    Advance to the next player or next betting round.
    This is called after each action.
    """
    hand = game.active_hand
    active_players = game.get_active_players()

    # Get players still in hand
    players_in_hand = [
        p for p in active_players
        if p.nickname in hand.player_hands
        and not hand.player_hands[p.nickname].folded
    ]

    # Check if only one player remains (everyone else folded)
    if len(players_in_hand) <= 1:
        # Hand is over, will be resolved in game loop
        hand.betting_round = BettingRound.SHOWDOWN
        return

    # Players who can still act (not folded, not all-in)
    can_act = [
        p for p in players_in_hand
        if not hand.player_hands[p.nickname].is_all_in
    ]

    # Check if betting round is complete
    all_acted = all(
        p.nickname in hand.players_acted_this_round
        for p in can_act
    )

    all_matched = all(
        hand.player_hands[p.nickname].current_bet == hand.current_bet
        or hand.player_hands[p.nickname].is_all_in
        for p in players_in_hand
    )

    if (all_acted and all_matched) or len(can_act) == 0:
        # Move to next betting round
        advance_betting_round(game)
    else:
        # Move to next player
        hand.current_player_idx = (hand.current_player_idx + 1) % len(can_act)


def advance_betting_round(game: Game) -> None:
    """Move to the next betting round."""
    hand = game.active_hand

    # Collect bets into pot
    collect_bets_into_pot(game)

    # Reset for new round
    hand.current_bet = 0
    hand.players_acted_this_round = set()
    hand.last_raiser = None

    for ph in hand.player_hands.values():
        ph.current_bet = 0

    # Advance the round
    rounds = [BettingRound.PREFLOP, BettingRound.FLOP, BettingRound.TURN, BettingRound.RIVER, BettingRound.SHOWDOWN]
    current_idx = rounds.index(hand.betting_round)

    if current_idx < len(rounds) - 1:
        hand.betting_round = rounds[current_idx + 1]

    # Reset action to first active player after dealer
    active_players = game.get_active_players()
    players_can_act = [
        p for p in active_players
        if p.nickname in hand.player_hands
        and not hand.player_hands[p.nickname].folded
        and not hand.player_hands[p.nickname].is_all_in
    ]

    if players_can_act:
        # Find first player after dealer
        dealer_pos = game.dealer_position
        for i in range(len(active_players)):
            idx = (dealer_pos + 1 + i) % len(active_players)
            player = active_players[idx]
            if player in players_can_act:
                hand.current_player_idx = players_can_act.index(player)
                break


def collect_bets_into_pot(game: Game) -> None:
    """Collect all current bets into the pot(s), handling side pots."""
    hand = game.active_hand

    # Get all players still in hand
    active_players = game.get_active_players()
    players_in_hand = [
        p.nickname for p in active_players
        if p.nickname in hand.player_hands
        and not hand.player_hands[p.nickname].folded
    ]

    # Get bets sorted by total amount
    bets = [(nick, hand.player_hands[nick].total_bet) for nick in players_in_hand]
    bets.sort(key=lambda x: x[1])

    # Simple pot collection for now (side pot logic can be enhanced)
    total_collected = sum(ph.current_bet for ph in hand.player_hands.values())

    if not hand.pots:
        hand.pots.append(Pot(amount=0, eligible_players=players_in_hand.copy()))

    hand.pots[0].amount += total_collected
    hand.pots[0].eligible_players = players_in_hand.copy()
