"""Warhead card implementation."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .player import player
    from .game import game

from .card import card
from .globals import (
    NUKE_YIELD_10MT,
    NUKE_YIELD_15MT,
    NUKE_YIELD_20MT,
    NUKE_YIELD_40MT,
    NUKE_YIELD_50MT,
    NUKE_YIELD_75MT,
    NUKE_YIELD_100MT,
    NUKE_YIELD_200MT,
    IllegalMoveError,
    PLAYER_STATE_ALIVE,
)


_BODYCOUNTS: dict[int, int] = {
    NUKE_YIELD_10MT: 2,
    NUKE_YIELD_15MT: 3,
    NUKE_YIELD_20MT: 5,
    NUKE_YIELD_40MT: 10,
    NUKE_YIELD_50MT: 15,
    NUKE_YIELD_75MT: 20,
    NUKE_YIELD_100MT: 25,
    NUKE_YIELD_200MT: 50,
}


class warhead(card):
    """A nuclear warhead card."""

    def __init__(self, megatons: int = NUKE_YIELD_10MT) -> None:
        """Initialise a warhead with the given yield."""
        if megatons not in _BODYCOUNTS:
            raise ValueError(f"BadNukeYield: {megatons}")
        self.megatons = megatons

    def __str__(self) -> str:
        return f"w{self.megatons}"

    def __repr__(self) -> str:
        return f"warhead({self.megatons})"

    def is_weapon(self) -> bool:
        """Return True - warheads are weapons."""
        return True

    def calc_fallout(self, tgt: player) -> int:
        """Calculate and apply the fallout damage to the target."""
        b = _BODYCOUNTS[self.megatons]
        r = random.randint(0, 16)
        g = tgt.game
        assert g is not None
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
            if self.megatons == NUKE_YIELD_100MT:
                g.game_msg(
                    f" > {g.cur.name}, you blew up the world, "  # type: ignore[union-attr]
                )
                g.apocalypse()
        elif r < 12:
            g.game_msg(" > Hit nuclear power plant, double yield")
            b *= 2
            m = True

        g.game_msg(
            f" > {tgt.name}: {b}M of your citizens die, boo hoo"
        )
        tgt.pwn(b)
        if m:
            tgt.missturns += 1

        return b

    def dequeue(self, g: game, p: player, tgt: player | None = None) -> None:
        """Execute the warhead card."""
        if tgt is None:
            raise IllegalMoveError(g, p, "Must target warhead")
        if tgt.state is not PLAYER_STATE_ALIVE:
            raise IllegalMoveError(
                g, p, "Overkill, you may not fuck the dead"
            )

        if p.weapon is None:
            g.game_msg(
                f" > {p.name} dumps {self.megatons}M warhead"
            )
            return

        p.weapon.use_warhead(self, g, p, tgt)
