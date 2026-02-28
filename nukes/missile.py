"""Missile delivery-system card."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import player
    from .warhead import warhead as Warhead
    from .game import game

from .card import card
from .globals import GAME_STATE_WAR


class missile(card):
    """A ballistic missile card used as a warhead delivery system."""

    def __init__(
        self, max_payload: int = 10, name: str = "missile"
    ) -> None:
        """Initialise the missile."""
        self.max_payload = max_payload
        self.__name = name

    def __str__(self) -> str:
        if self.__name == "missile":
            return f"missile({self.max_payload})"
        return self.__name

    def __repr__(self) -> str:
        return f"{self.__name}({self.max_payload})"

    def is_weapon(self) -> bool:
        """Return True - missiles are delivery systems."""
        return True

    def use_warhead(
        self, warhead: Warhead, g: game, p: player, tgt: player
    ) -> None:
        """Fire the missile carrying the given warhead at the target."""
        if warhead.megatons > self.max_payload:
            p.weapon = None
            g.game_msg(
                f" > {p.name} wastes {warhead.megatons}M warhead "
                f"and {self.max_payload}M missile"
            )
            return

        g.transition(GAME_STATE_WAR)
        g.game_msg(
            f" > {p.name} fires {warhead.megatons} megaton missile "
            f"at {tgt.name}"
        )
        warhead.calc_fallout(tgt)
        p.weapon = None

    def dequeue(self, g: game, p: player, tgt: player | None = None) -> None:
        """Deploy this missile (set it as the player active weapon)."""
        p.weapon = self
        g.game_msg(f" > {p.name} deploys missile {self}")
