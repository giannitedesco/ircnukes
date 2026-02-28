"""Bomber delivery-system card."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import player
    from .warhead import warhead as Warhead
    from .game import game

from .card import card
from .globals import GAME_STATE_WAR


class bomber(card):
    """A strategic bomber card used as a reusable warhead carrier."""

    def __init__(
        self, max_payload: int = 10, name: str = "bomber"
    ) -> None:
        """Initialise the bomber."""
        self.max_payload = max_payload
        self.payload = max_payload
        self.__name = name

    def __str__(self) -> str:
        if self.__name == "bomber":
            return f"bomber({self.max_payload})"
        return self.__name

    def __repr__(self) -> str:
        return f"{self.__name}({self.payload}/{self.max_payload})"

    def is_weapon(self) -> bool:
        """Return True - bombers are delivery systems."""
        return True

    def use_warhead(
        self, warhead: Warhead, g: game, p: player, tgt: player
    ) -> None:
        """Drop the warhead from this bomber onto the target."""
        if self.payload < warhead.megatons:
            p.weapon = None
            g.game_msg(
                f" > {p.name} wastes {warhead.megatons}M warhead "
                f"on {self.payload}M bomber"
            )
            return

        self.payload -= warhead.megatons
        g.transition(GAME_STATE_WAR)
        g.game_msg(
            f" > bomber: {p.name} fires {warhead.megatons} megaton "
            f"warhead at {tgt.name}"
        )
        warhead.calc_fallout(tgt)

        if self.payload <= 0:
            p.weapon = None

    def dequeue(self, g: game, p: player, tgt: player | None = None) -> None:
        """Deploy this bomber (set it as the player active weapon)."""
        p.weapon = self
        g.game_msg(f" > {p.name} deploys bomber {self}")
