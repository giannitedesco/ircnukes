"""Base class for all game cards."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import game
    from .player import player
    from .warhead import warhead as Warhead

from .globals import IllegalMoveError


class card:
    """Abstract base class for all Nuclear War game cards."""

    def is_warhead(self) -> bool:
        """Return True if this card is a warhead.

        Returns:
            Always False for the base card class.
        """
        return False

    def is_weapon(self) -> bool:
        """Return True if this card is a weapon (delivery system).

        Returns:
            Always False for the base card class.
        """
        return False

    def use_warhead(
        self, warhead: Warhead, g: game, p: player, tgt: player
    ) -> None:
        """Attempt to use this card as a warhead delivery system.

        Args:
            warhead: The warhead card being delivered.
            g: The game instance.
            p: The player firing the weapon.
            tgt: The target player.

        Raises:
            IllegalMoveError: Always, since the base card is not a weapon.
        """
        raise IllegalMoveError(g, p, f"{self} not a weapon")

    def dequeue(self, g: game, p: player, tgt: player | None = None) -> None:
        """Execute this card's effect when dequeued from a player's stack.

        Args:
            g: The game instance.
            p: The player who owns this card.
            tgt: Optional target player for targeted cards.
        """
        return
