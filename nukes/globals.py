"""Global constants and exceptions for the Nuclear War card game."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import game
    from .player import player

# Game state constants
GAME_STATE_INIT: int = 0
"""Game has been created but not yet started."""

GAME_STATE_PEACE: int = 1
"""Game is in the peace phase."""

GAME_STATE_WAR: int = 2
"""Game is in the war phase."""

GAME_STATE_OVER: int = 3
"""Game has ended."""

# Player state constants
PLAYER_STATE_ALIVE: int = 1
"""Player is alive and active."""

PLAYER_STATE_RETALIATE: int = 2
"""Player is dead but may still retaliate."""

PLAYER_STATE_DEAD: int = 3
"""Player is fully eliminated."""

CARD_STACK_LEN: int = 2
"""Number of cards in a player's queue."""

# Nuclear yield constants (megatons)
NUKE_YIELD_10MT: int = 10
NUKE_YIELD_15MT: int = 15
NUKE_YIELD_20MT: int = 20
NUKE_YIELD_40MT: int = 40
NUKE_YIELD_50MT: int = 50
NUKE_YIELD_75MT: int = 75
NUKE_YIELD_100MT: int = 100
NUKE_YIELD_200MT: int = 200


class IllegalMoveError(Exception):
    """Raised when a player attempts an illegal game move."""

    def __init__(self, g: game | None, p: player | None, desc: str) -> None:
        """Initialise the error with game context and description.

        Args:
            g: The game instance in which the error occurred.
            p: The player who attempted the illegal move.
            desc: Human-readable description of why the move is illegal.
        """
        super().__init__(desc)
        self.game = g
        self.player = p
        self.desc = desc


class GameLogicError(Exception):
    """Raised when a game logic violation occurs."""

    def __init__(
        self, g: game | None, desc: str, player: player | None = None
    ) -> None:
        """Initialise the error with game context and description.

        Args:
            g: The game instance in which the error occurred.
            desc: Human-readable description of the logic error.
            player: Optional player associated with the error.
        """
        super().__init__(desc)
        self.game = g
        self.player = player
        self.desc = desc


class GameOverMan(Exception):
    """Raised when the game ends, optionally with a winner."""

    def __init__(self, g: game, winner: player | None = None) -> None:
        """Initialise the game-over exception.

        Args:
            g: The game instance that has ended.
            winner: The winning player, or None if it was mutual assured
                destruction.
        """
        if winner is not None:
            msg = f"Game over: winner {winner.name}"
        else:
            msg = "Game over"
        super().__init__(msg)
        self.game = g
        self.winner = winner
