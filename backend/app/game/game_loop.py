"""Full game loop management - hand lifecycle, dealing, showdown."""

import asyncio
import uuid
from typing import Optional, Callable, Awaitable

from .models import Game, Hand, PlayerHand, Pot, BettingRound, GameStatus
from .poker import Deck, Card, evaluate_hand, compare_hands
from .actions import fold, get_current_player_nickname
from ..config import SMALL_BLIND, BIG_BLIND, HAND_LIMIT, TURN_TIMER_SECONDS, POINTS_BY_PLACEMENT
from ..db import database, game_results, game_result_players


# Type for broadcast callback
BroadcastCallback = Callable[[str, dict, Optional[str]], Awaitable[None]]


class GameLoop:
    """Manages the game loop for a single game."""

    def __init__(self, game: Game, broadcast: BroadcastCallback):
        self.game = game
        self.broadcast = broadcast  # async fn(game_id, message, viewer_nickname)
        self.deck: Optional[Deck] = None
        self.turn_timer_task: Optional[asyncio.Task] = None

    async def start_game(self):
        """Start the game - called when creator starts it."""
        self.game.status = GameStatus.ACTIVE
        self.game.current_hand_num = 0
        self.game.dealer_position = 0

        await self.broadcast(self.game.id, {
            "type": "game_started",
            "payload": {"game": self.game.to_dict()}
        }, None)

        # Start first hand
        await self.start_hand()

    async def start_hand(self):
        """Start a new hand."""
        # Check if game should end
        active_players = self.game.get_active_players()
        if len(active_players) <= 1:
            await self.end_game()
            return

        if self.game.current_hand_num >= HAND_LIMIT:
            await self.end_game()
            return

        self.game.current_hand_num += 1

        # Rotate dealer
        if self.game.current_hand_num > 1:
            self.game.dealer_position = (self.game.dealer_position + 1) % len(active_players)

        # Create new hand
        self.deck = Deck()
        self.deck.shuffle()

        hand = Hand(
            hand_number=self.game.current_hand_num,
            dealer_position=self.game.dealer_position,
            min_raise=BIG_BLIND,
        )
        hand.pots = [Pot(amount=0, eligible_players=[p.nickname for p in active_players])]

        # Create player hands and deal hole cards
        for player in active_players:
            hole_cards = self.deck.deal(2)
            hand.player_hands[player.nickname] = PlayerHand(
                nickname=player.nickname,
                hole_cards=hole_cards,
            )

        self.game.active_hand = hand

        # Post blinds
        await self.post_blinds()

        # Notify players - each gets their own hole cards
        for player in active_players:
            await self.send_to_player(player.nickname, {
                "type": "hand_started",
                "payload": {
                    "hand_number": hand.hand_number,
                    "dealer_position": hand.dealer_position,
                    "hole_cards": [c.to_dict() for c in hand.player_hands[player.nickname].hole_cards],
                    "your_position": self.game.get_player_position(player.nickname),
                }
            })

        # Start turn timer for first player
        await self.prompt_current_player()

    async def post_blinds(self):
        """Post small and big blinds."""
        active_players = self.game.get_active_players()
        hand = self.game.active_hand
        num_players = len(active_players)

        # Determine blind positions
        if num_players == 2:
            # Heads up: dealer is SB, other is BB
            sb_idx = self.game.dealer_position
            bb_idx = (self.game.dealer_position + 1) % num_players
        else:
            sb_idx = (self.game.dealer_position + 1) % num_players
            bb_idx = (self.game.dealer_position + 2) % num_players

        sb_player = active_players[sb_idx]
        bb_player = active_players[bb_idx]

        # Post small blind
        sb_amount = min(SMALL_BLIND, sb_player.chips)
        sb_player.chips -= sb_amount
        hand.player_hands[sb_player.nickname].current_bet = sb_amount
        hand.player_hands[sb_player.nickname].total_bet = sb_amount
        if sb_player.chips == 0:
            hand.player_hands[sb_player.nickname].is_all_in = True

        # Post big blind
        bb_amount = min(BIG_BLIND, bb_player.chips)
        bb_player.chips -= bb_amount
        hand.player_hands[bb_player.nickname].current_bet = bb_amount
        hand.player_hands[bb_player.nickname].total_bet = bb_amount
        if bb_player.chips == 0:
            hand.player_hands[bb_player.nickname].is_all_in = True

        hand.current_bet = bb_amount
        hand.pots[0].amount = sb_amount + bb_amount

        # First to act is player after BB (or SB in heads up preflop)
        if num_players == 2:
            hand.current_player_idx = 0  # SB acts first in heads up preflop
        else:
            hand.current_player_idx = 0  # Will be adjusted in prompt_current_player

        await self.broadcast(self.game.id, {
            "type": "blinds_posted",
            "payload": {
                "small_blind": {"nickname": sb_player.nickname, "amount": sb_amount},
                "big_blind": {"nickname": bb_player.nickname, "amount": bb_amount},
            }
        }, None)

    async def prompt_current_player(self):
        """Send turn notification and start timer."""
        hand = self.game.active_hand
        if not hand or hand.betting_round == BettingRound.SHOWDOWN:
            await self.resolve_hand()
            return

        current_nickname = get_current_player_nickname(self.game)
        if not current_nickname:
            # No one left to act, advance round or resolve
            await self.check_round_end()
            return

        from .actions import get_valid_actions
        valid_actions = get_valid_actions(self.game, current_nickname)

        await self.broadcast(self.game.id, {
            "type": "turn",
            "payload": {
                "current_player": current_nickname,
                "valid_actions": valid_actions,
                "time_remaining": TURN_TIMER_SECONDS,
                "current_bet": hand.current_bet,
                "pot": hand.get_total_pot(),
            }
        }, None)

        # Start turn timer
        self.cancel_turn_timer()
        self.turn_timer_task = asyncio.create_task(
            self.turn_timeout(current_nickname)
        )

    def cancel_turn_timer(self):
        """Cancel the current turn timer."""
        if self.turn_timer_task and not self.turn_timer_task.done():
            self.turn_timer_task.cancel()

    async def turn_timeout(self, nickname: str):
        """Handle turn timeout - auto-fold."""
        try:
            await asyncio.sleep(TURN_TIMER_SECONDS)

            # Check if still this player's turn
            current = get_current_player_nickname(self.game)
            if current == nickname:
                await self.handle_action(nickname, "fold", {})
        except asyncio.CancelledError:
            pass

    async def handle_action(self, nickname: str, action_type: str, params: dict):
        """Handle a player action."""
        from . import actions

        self.cancel_turn_timer()

        hand = self.game.active_hand
        if not hand:
            return

        try:
            if action_type == "fold":
                actions.fold(self.game, nickname)
            elif action_type == "check":
                actions.check(self.game, nickname)
            elif action_type == "call":
                amount = actions.call(self.game, nickname)
                params["amount"] = amount
            elif action_type == "raise":
                amount = actions.raise_bet(self.game, nickname, params.get("amount", 0))
                params["amount"] = amount
            elif action_type == "all_in":
                amount = actions.all_in(self.game, nickname)
                params["amount"] = amount
            else:
                await self.send_to_player(nickname, {
                    "type": "error",
                    "payload": {"message": f"Unknown action: {action_type}"}
                })
                await self.prompt_current_player()
                return

            # Broadcast action to all players
            await self.broadcast(self.game.id, {
                "type": "player_action",
                "payload": {
                    "nickname": nickname,
                    "action": action_type,
                    "amount": params.get("amount"),
                    "pot": hand.get_total_pot(),
                    "player_chips": self.game.get_player(nickname).chips,
                }
            }, None)

            # Check if hand/round is over
            await self.check_round_end()

        except actions.ActionError as e:
            await self.send_to_player(nickname, {
                "type": "error",
                "payload": {"message": str(e)}
            })
            await self.prompt_current_player()

    async def check_round_end(self):
        """Check if betting round or hand is over."""
        hand = self.game.active_hand
        if not hand:
            return

        active_players = self.game.get_active_players()
        players_in_hand = [
            p for p in active_players
            if p.nickname in hand.player_hands
            and not hand.player_hands[p.nickname].folded
        ]

        # If only one player left, they win
        if len(players_in_hand) <= 1:
            await self.resolve_hand()
            return

        # If we've reached showdown
        if hand.betting_round == BettingRound.SHOWDOWN:
            await self.resolve_hand()
            return

        # Check if we need to deal community cards
        if hand.betting_round == BettingRound.FLOP and len(hand.community_cards) == 0:
            await self.deal_community_cards(3)
        elif hand.betting_round == BettingRound.TURN and len(hand.community_cards) == 3:
            await self.deal_community_cards(1)
        elif hand.betting_round == BettingRound.RIVER and len(hand.community_cards) == 4:
            await self.deal_community_cards(1)

        # Prompt next player
        await self.prompt_current_player()

    async def deal_community_cards(self, count: int):
        """Deal community cards (flop/turn/river)."""
        hand = self.game.active_hand

        # Burn one card
        self.deck.deal_one()

        # Deal community cards
        new_cards = self.deck.deal(count)
        hand.community_cards.extend(new_cards)

        await self.broadcast(self.game.id, {
            "type": "community_cards",
            "payload": {
                "cards": [c.to_dict() for c in new_cards],
                "all_community_cards": [c.to_dict() for c in hand.community_cards],
                "betting_round": hand.betting_round.value,
            }
        }, None)

    async def resolve_hand(self):
        """Resolve the hand - determine winner(s) and award pot(s)."""
        self.cancel_turn_timer()

        hand = self.game.active_hand
        if not hand:
            return

        active_players = self.game.get_active_players()
        players_in_hand = [
            p for p in active_players
            if p.nickname in hand.player_hands
            and not hand.player_hands[p.nickname].folded
        ]

        results = []

        if len(players_in_hand) == 1:
            # Everyone else folded - winner doesn't show cards
            winner = players_in_hand[0]
            winner.chips += hand.get_total_pot()
            results.append({
                "nickname": winner.nickname,
                "won": hand.get_total_pot(),
                "hand_shown": False,
            })
        else:
            # Showdown - evaluate hands
            player_hands_for_eval = []
            for player in players_in_hand:
                ph = hand.player_hands[player.nickname]
                full_hand = ph.hole_cards + hand.community_cards
                player_hands_for_eval.append((player.nickname, full_hand, ph.hole_cards))

            # Find winners
            hands_only = [h[1] for h in player_hands_for_eval]
            winner_indices = compare_hands(hands_only)

            pot_per_winner = hand.get_total_pot() // len(winner_indices)
            remainder = hand.get_total_pot() % len(winner_indices)

            for i, (nickname, full_hand, hole_cards) in enumerate(player_hands_for_eval):
                player = self.game.get_player(nickname)
                hand_result = evaluate_hand(full_hand)

                if i in winner_indices:
                    winnings = pot_per_winner + (1 if i < remainder else 0)
                    player.chips += winnings
                    results.append({
                        "nickname": nickname,
                        "won": winnings,
                        "hand_shown": True,
                        "hole_cards": [c.to_dict() for c in hole_cards],
                        "hand_rank": hand_result.rank.name,
                    })
                else:
                    results.append({
                        "nickname": nickname,
                        "won": 0,
                        "hand_shown": True,
                        "hole_cards": [c.to_dict() for c in hole_cards],
                        "hand_rank": hand_result.rank.name,
                    })

        await self.broadcast(self.game.id, {
            "type": "hand_result",
            "payload": {
                "results": results,
                "community_cards": [c.to_dict() for c in hand.community_cards],
            }
        }, None)

        # Check for eliminations
        await self.check_eliminations()

        # Clear active hand
        self.game.active_hand = None

        # Small delay before next hand
        await asyncio.sleep(3)

        # Start next hand
        await self.start_hand()

    async def check_eliminations(self):
        """Check for and handle player eliminations."""
        for player in self.game.players:
            if not player.is_eliminated and player.chips <= 0:
                player.is_eliminated = True
                player.chips = 0
                self.game.elimination_order.append(player.nickname)
                player.elimination_position = len(self.game.players) - len(self.game.elimination_order) + 1

                await self.broadcast(self.game.id, {
                    "type": "player_eliminated",
                    "payload": {
                        "nickname": player.nickname,
                        "position": player.elimination_position,
                    }
                }, None)

    async def end_game(self):
        """End the game and calculate final standings."""
        self.cancel_turn_timer()
        self.game.status = GameStatus.FINISHED

        # Calculate final placements
        active_players = self.game.get_active_players()

        # Sort active players by chips (descending) for final placement
        active_players.sort(key=lambda p: p.chips, reverse=True)

        placements = []

        # Active players get top placements
        for i, player in enumerate(active_players):
            position = i + 1
            points = POINTS_BY_PLACEMENT[position - 1] if position <= len(POINTS_BY_PLACEMENT) else 0
            player.elimination_position = position
            placements.append({
                "nickname": player.nickname,
                "position": position,
                "chips": player.chips,
                "points": points,
            })

        # Eliminated players already have positions from elimination order (reversed)
        for player in self.game.players:
            if player.is_eliminated:
                position = player.elimination_position
                points = POINTS_BY_PLACEMENT[position - 1] if position <= len(POINTS_BY_PLACEMENT) else 0
                placements.append({
                    "nickname": player.nickname,
                    "position": position,
                    "chips": 0,
                    "points": points,
                })

        # Sort by position
        placements.sort(key=lambda p: p["position"])

        # Save to database
        await self.save_game_result(placements)

        await self.broadcast(self.game.id, {
            "type": "game_ended",
            "payload": {
                "placements": placements,
                "total_hands": self.game.current_hand_num,
            }
        }, None)

    async def save_game_result(self, placements: list[dict]):
        """Save game result to database."""
        if not database or not database.is_connected:
            return

        game_id = str(uuid.uuid4())

        # Insert game result
        await database.execute(
            game_results.insert().values(id=game_id)
        )

        # Insert player results
        for placement in placements:
            await database.execute(
                game_result_players.insert().values(
                    id=str(uuid.uuid4()),
                    game_result_id=game_id,
                    nickname=placement["nickname"],
                    placement=placement["position"],
                    points_awarded=placement["points"],
                )
            )

    async def send_to_player(self, nickname: str, message: dict):
        """Send a message to a specific player."""
        # This will be called from the broadcast callback with viewer_nickname
        await self.broadcast(self.game.id, message, nickname)


# Store active game loops
game_loops: dict[str, GameLoop] = {}


def get_game_loop(game_id: str) -> Optional[GameLoop]:
    """Get the game loop for a game."""
    return game_loops.get(game_id)


def create_game_loop(game: Game, broadcast: BroadcastCallback) -> GameLoop:
    """Create a new game loop."""
    loop = GameLoop(game, broadcast)
    game_loops[game.id] = loop
    return loop


def remove_game_loop(game_id: str):
    """Remove a game loop."""
    if game_id in game_loops:
        loop = game_loops[game_id]
        loop.cancel_turn_timer()
        del game_loops[game_id]
