"""Propaganda card implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player
    from .game import Game

from .card import Card
from .globals import GameState, IllegalMoveError


class Propaganda(Card):
    """A propaganda card that transfers population from enemy to self."""

    def __init__(self, pop: int = 5) -> None:
        """Initialise the propaganda card."""
        self.__pop = pop

    def __str__(self) -> str:
        return f"p{self.__pop}"

    def __repr__(self) -> str:
        return f"propaganda({self.__pop})"

    def dequeue(
        self, g: "Game", p: "Player", tgt: "Player | None" = None
    ) -> None:
        """Execute the propaganda card."""
        if g.state() != GameState.PEACE:
            g.game_msg(f" > {p.name} dumps propaganda")
            return
        if tgt is None:
            raise IllegalMoveError(g, p, "Target required")
        p.weapon = None
        g.game_msg(
            f" > {p.name} uses propaganda on {tgt.name} ({self.__pop}M)"
        )
        tgt.transfer_population(self.__pop, p)


# Backward-compatible alias
propaganda = Propaganda
