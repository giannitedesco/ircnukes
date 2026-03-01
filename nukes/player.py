"""Player class for the Nuclear War card game."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .game import Game

from .globals import (
    CARD_STACK_LEN,
    PlayerState,
    GAME_STATE_INIT,
    GAME_STATE_WAR,
    PLAYER_STATE_ALIVE,
    PLAYER_STATE_DEAD,
    PLAYER_STATE_RETALIATE,
    IllegalMoveError,
)


class Player:
    """Represents a single participant in a Nuclear War game."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.hand: list[Any] = []
        self.population: int = 0
        self.card_stack: list[Any] = []
        self.weapon: Any | None = None
        self.game: "Game | None" = None
        self.state: PlayerState = PlayerState.ALIVE
        self.missturns: int = 0

    def __str__(self) -> str:
        return f"player({self.name})"

    def __repr__(self) -> str:
        return f"player('{self.name}')"

    def __card_by_idx(self, idx: int) -> Any:
        if idx < 0 or idx >= len(self.hand):
            raise IllegalMoveError(
                self.game, self, f"Bad Card Index: {idx}"
            )
        return self.hand.pop(idx)

    def __card_by_name(self, name: str) -> Any:
        strl = [str(x).lower() for x in self.hand]
        repl = [repr(x).lower() for x in self.hand]
        for i in range(len(self.hand)):
            if repl[i] == name.lower() or strl[i] == name.lower():
                return self.hand.pop(i)
        raise IllegalMoveError(self.game, self, f"Card {name} not found")

    def terminate(self, suicide: bool = False) -> None:
        """Kill this player, optionally triggering retaliation."""
        if self.state == PLAYER_STATE_DEAD:
            return
        if self.game is None:
            return

        if not suicide and self.game.state() == GAME_STATE_WAR:
            self.state = PLAYER_STATE_RETALIATE
        else:
            self.state = PLAYER_STATE_DEAD
        self.cards_to_hand()
        self.game.player_dead(self)

    # Public alias keeping the original name
    kill = terminate

    def cards_to_hand(self) -> None:
        """Move all queued and deployed cards back into the hand."""
        self.hand.extend(self.card_stack)
        self.card_stack = []
        if self.weapon is not None:
            self.hand.append(self.weapon)
            self.weapon = None

    def flip_card(self, tgt: "Player | None") -> None:
        """Flip (execute) the first queued card during a normal turn."""
        if self.state != PLAYER_STATE_ALIVE:
            raise IllegalMoveError(self.game, self, "You're not alive!")
        if self.game is None or self.game.cur != self:
            raise IllegalMoveError(self.game, self, "Not your turn")
        if len(self.card_stack) != CARD_STACK_LEN:
            raise IllegalMoveError(self.game, self, "Cards not queued")
        c = self.card_stack.pop(0)
        try:
            c.dequeue(self.game, self, tgt)
        except Exception:
            self.card_stack.insert(0, c)
            raise

    def use_card(self, arg: str, tgt: "Player | None") -> None:
        """Use a card during final retaliation."""
        if self.game is None or self.game.cur != self:
            raise IllegalMoveError(self.game, self, "Not your turn")
        if self.state != PLAYER_STATE_RETALIATE:
            raise IllegalMoveError(
                self.game, self, "It's not final retaliation!"
            )

        try:
            c = self.__card_by_idx(int(arg))
        except ValueError:
            c = self.__card_by_name(arg)

        try:
            c.dequeue(self.game, self, tgt)
        except Exception:
            self.hand.append(c)
            raise

    def queue_card(self, arg: str) -> Any:
        """Push a card from the hand into the queue."""
        if len(self.card_stack) == CARD_STACK_LEN:
            raise IllegalMoveError(self.game, self, "Queue Full")
        if self.state != PLAYER_STATE_ALIVE:
            raise IllegalMoveError(
                self.game, self, "Cannot queue cards when dead"
            )

        try:
            c = self.__card_by_idx(int(arg))
        except ValueError:
            c = self.__card_by_name(arg)

        self.card_stack.append(c)
        if (
            len(self.card_stack) == CARD_STACK_LEN
            and self.game is not None
            and self.game.state() == GAME_STATE_INIT
        ):
            self.game.game_msg(f"{self.name} is ready")
        return c

    def pwn(self, pwnage: int) -> None:
        """Apply population damage to this player."""
        i = min(self.population, pwnage)
        self.population -= i
        if self.population == 0:
            self.terminate()

    def transfer_population(self, converts: int, tgt: "Player") -> None:
        """Transfer population from this player to another."""
        if self.state != PLAYER_STATE_ALIVE:
            raise IllegalMoveError(
                self.game,
                self,
                "Cannot transfer population from dead enemy",
            )
        i = min(self.population, converts)
        self.population -= i
        tgt.population += i
        if self.population == 0:
            self.terminate()


# Backward-compatible alias
player = Player
