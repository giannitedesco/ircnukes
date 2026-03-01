"""Global constants, enumerations, and exceptions for the Nuclear War card game."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .player import Player


class GameState(IntEnum):
    """Enumeration of possible game phase states."""

    INIT = 0
    PEACE = 1
    WAR = 2
    OVER = 3


class PlayerState(IntEnum):
    """Enumeration of possible player lifecycle states."""

    ALIVE = 1
    RETALIATE = 2
    DEAD = 3


_YIELD_POPDEAD: dict[int, int] = {
    10: 2,
    15: 3,
    20: 5,
    40: 10,
    50: 15,
    75: 20,
    100: 25,
    200: 50,
}


class NukeYield(IntEnum):
    """Nuclear warhead yield in megatons with associated kill data."""

    MT10 = 10
    MT15 = 15
    MT20 = 20
    MT40 = 40
    MT50 = 50
    MT75 = 75
    MT100 = 100
    MT200 = 200

    @property
    def popdead(self) -> int:
        """Base population millions killed by a direct hit at this yield."""
        return _YIELD_POPDEAD[self.value]


# ---------------------------------------------------------------------------
# Miscellaneous constants
# ---------------------------------------------------------------------------

CARD_STACK_LEN: int = 2
"""Number of cards in a player's queue."""

# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

GAME_STATE_INIT = GameState.INIT
GAME_STATE_PEACE = GameState.PEACE
GAME_STATE_WAR = GameState.WAR
GAME_STATE_OVER = GameState.OVER

PLAYER_STATE_ALIVE = PlayerState.ALIVE
PLAYER_STATE_RETALIATE = PlayerState.RETALIATE
PLAYER_STATE_DEAD = PlayerState.DEAD

NUKE_YIELD_10MT = NukeYield.MT10
NUKE_YIELD_15MT = NukeYield.MT15
NUKE_YIELD_20MT = NukeYield.MT20
NUKE_YIELD_40MT = NukeYield.MT40
NUKE_YIELD_50MT = NukeYield.MT50
NUKE_YIELD_75MT = NukeYield.MT75
NUKE_YIELD_100MT = NukeYield.MT100
NUKE_YIELD_200MT = NukeYield.MT200


class IllegalMoveError(Exception):
    """Raised when a player attempts an illegal game move."""

    def __init__(
        self, g: "Game | None", p: "Player | None", desc: str
    ) -> None:
        super().__init__(desc)
        self.game = g
        self.player = p
        self.desc = desc


class GameLogicError(Exception):
    """Raised when a game logic violation occurs."""

    def __init__(
        self, g: "Game | None", desc: str, player: "Player | None" = None
    ) -> None:
        super().__init__(desc)
        self.game = g
        self.player = player
        self.desc = desc


class GameOverMan(Exception):
    """Raised when the game ends, optionally with a winner."""

    def __init__(self, g: "Game", winner: "Player | None" = None) -> None:
        if winner is not None:
            msg = f"Game over: winner {winner.name}"
        else:
            msg = "Game over"
        super().__init__(msg)
        self.game = g
        self.winner = winner
