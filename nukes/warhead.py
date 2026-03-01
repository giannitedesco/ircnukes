"""Warhead card implementation."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player
    from .game import Game

from .card import Card
from .globals import (
    NukeYield,
    IllegalMoveError,
    GameLogicError,
    PLAYER_STATE_ALIVE,
)


class Warhead(Card):
    """A nuclear warhead card."""

    def __init__(self, megatons: int = NukeYield.MT10) -> None:
        """Initialise a warhead with the given yield."""
        try:
            self.megatons: NukeYield = NukeYield(megatons)
        except ValueError:
            raise ValueError(f"BadNukeYield: {megatons}")

    def __str__(self) -> str:
        return f"w{self.megatons.value}"

    def __repr__(self) -> str:
        return f"warhead({self.megatons.value})"

    def is_weapon(self) -> bool:
        """Return True - warheads are weapons."""
        return True

    def calc_fallout(self, tgt: "Player") -> int:
        """Calculate and apply the fallout damage to the target."""
        b = self.megatons.popdead
        r = random.randint(0, 16)  # noqa: S311
        g = tgt.game
        if g is None:
            raise GameLogicError(
                None, "calc_fallout called for a player not in a game"
            )
        m = False

        if r < 3:
            g.game_msg(" > Dirty bomb, double yield")
            b *= 2
        elif r < 5:
            g.game_msg(" > Neutron bomb, double yield")
            b *= 2
        elif r < 7:
            g.game_msg(" > Gamma rays, +10M dead")
            b += 10
        elif r < 8:
            g.game_msg(" > Fireball, +1M dead")
            b += 1
        elif r < 9:
            g.game_msg(" > Beta particles, +5M dead")
            b += 5
        elif r < 10:
            g.game_msg(" > Fallout, +2M dead")
            b += 2
        elif r < 11:
            g.game_msg(" > Hit nuclear stockpile, triple yield")
            b *= 3
            if (
                self.megatons == NukeYield.MT100
                and g.cur is not None
            ):
                g.game_msg(
                    f" > {g.cur.name}, you blew up the world, "
                    "it's your job to tidy the mess!"
                )
                g.apocalypse()
        elif r < 12:
            g.game_msg(" > Hit nuclear power plant, double yield")
            g.game_msg(f" > {tgt.name} misses a turn!")
            b *= 2
            m = True

        g.game_msg(
            f" > {tgt.name}: {b}M of your citizens die, boo hoo"
        )
        tgt.pwn(b)
        if m:
            tgt.missturns += 1

        return b

    def dequeue(
        self, g: "Game", p: "Player", tgt: "Player | None" = None
    ) -> None:
        """Execute the warhead card."""
        if tgt is None:
            raise IllegalMoveError(g, p, "Must target warhead")
        if tgt.state is not PLAYER_STATE_ALIVE:
            raise IllegalMoveError(
                g, p, "Overkill, you may not fuck the dead"
            )

        if p.weapon is None:
            g.game_msg(
                f" > {p.name} dumps {self.megatons.value}M warhead"
            )
            return

        p.weapon.use_warhead(self, g, p, tgt)


# Backward-compatible alias
warhead = Warhead
