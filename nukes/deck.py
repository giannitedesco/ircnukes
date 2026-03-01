"""Simulates a never-ending deck of cards using a random shuffle."""

from __future__ import annotations

import random
from typing import Any

from .globals import GameLogicError


class _DeckCard:
    """Internal representation of a card type in the deck."""

    def __init__(self, max_cnt: int, cls: type[Any], args: list[Any]) -> None:
        self.cnt = max_cnt
        self.max = max_cnt
        self.cls = cls
        self.args = args


class Deck:
    """A shuffled, replenishing deck of game cards."""

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__cards: list[_DeckCard] = []

    def __str__(self) -> str:
        return f"deck({self.__name},{len(self)})"

    def __repr__(self) -> str:
        return f"deck({self.__name})"

    def __replenish(self) -> None:
        for x in self.__cards:
            x.cnt = x.max

    def __len__(self) -> int:
        return sum(x.cnt for x in self.__cards)

    def deal_card(self) -> Any:
        """Deal a single card at random from the deck."""
        if not self.__cards:
            return None

        ds = len(self)
        if ds == 0:
            self.__replenish()
            ds = len(self)

        r = random.randint(0, ds - 1)  # noqa: S311
        i = 0
        for c in self.__cards:
            i += c.cnt
            if r < i:
                c.cnt -= 1
                return c.cls(*c.args)
        return None  # unreachable, satisfies mypy

    def add_card(self, maxcnt: int, cls: type[Any], args: list[Any]) -> None:
        """Register a card type with this deck."""
        self.__cards.append(_DeckCard(maxcnt, cls, args))

    @staticmethod
    def __do_args(item: str) -> int | str:
        try:
            return int(item)
        except ValueError:
            return item

    def load_file(
        self, f: Any, clsmap: dict[str, type[Any]]
    ) -> None:
        """Populate this deck from a deck-definition file."""
        for line in f:
            ln = line.rstrip("\n")
            if not ln or ln[0] == "#":
                continue
            parts = ln.split()
            if len(parts) < 2:
                raise GameLogicError(None, f"Bad line: {parts}")
            try:
                maxcnt = int(parts[0])
            except ValueError:
                raise GameLogicError(None, f"{parts[0]} not an integer")
            if parts[1] not in clsmap:
                raise GameLogicError(None, f"No such card: {parts[1]}")
            cls = clsmap[parts[1]]
            args: list[int | str] = [self.__do_args(t) for t in parts[2:]]
            self.add_card(maxcnt, cls, args)


# Backward-compatible alias
deck = Deck
