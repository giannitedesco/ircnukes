"""Base class for all game cards."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .warhead import Warhead

from .globals import IllegalMoveError


class Card:
    """Abstract base class for all Nuclear War game cards."""

    def is_warhead(self) -> bool:
        """Return True if this card is a warhead."""
        return False

    def is_weapon(self) -> bool:
        """Return True if this card is a weapon (delivery system)."""
        return False

    def use_warhead(
        self, warhead: "Warhead", g: "Game", p: "Player", tgt: "Player"
    ) -> None:
        """Attempt to use this card as a warhead delivery system."""
        raise IllegalMoveError(g, p, f"{self} not a weapon")

    def dequeue(
        self, g: "Game", p: "Player", tgt: "Player | None" = None
    ) -> None:
        """Execute this card's effect when dequeued from a player's stack."""
        return


# Backward-compatible alias
card = Card
