"""Propaganda card implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import player
    from .game import game

from .card import card
from .globals import GAME_STATE_PEACE, IllegalMoveError


class propaganda(card):
    """A propaganda card that transfers population from enemy to self."""

    def __init__(self, pop: int = 5) -> None:
        """Initialise the propaganda card."""
        self.__pop = pop

    def __str__(self) -> str:
        return f"p{self.__pop}"

    def __repr__(self) -> str:
        return f"propaganda({self.__pop})"

    def dequeue(self, g: game, p: player, tgt: player | None = None) -> None:
        """Execute the propaganda card."""
        if g.state() != GAME_STATE_PEACE:
            g.game_msg(f" > {p.name} dumps propaganda")
            return
        if tgt is None:
            raise IllegalMoveError(g, p, "Target required")
        p.weapon = None
        g.game_msg(
            f" > {p.name} uses propaganda on {tgt.name} ({self.__pop}M)"
        )
        tgt.transfer_population(self.__pop, p)
