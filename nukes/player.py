"""Player class for the Nuclear War card game."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .game import game

from .globals import (
    CARD_STACK_LEN,
    GAME_STATE_INIT,
    GAME_STATE_WAR,
    PLAYER_STATE_ALIVE,
    PLAYER_STATE_DEAD,
    PLAYER_STATE_RETALIATE,
    IllegalMoveError,
)


class player:
    """Represents a single participant in a Nuclear War game.

    Attributes:
        name: The player's IRC nickname (case-normalised).
        hand: Cards currently held in the player's hand.
        population: Current population count in millions.
        card_stack: Cards queued for the next turn.
        weapon: The delivery system currently deployed, if any.
        game: The game this player belongs to.
        state: Current player state (alive / retaliating / dead).
        missturns: Number of turns this player must skip.
    """

    def __init__(self, name: str) -> None:
        """Initialise a new player with empty hand and zero population.

        Args:
            name: The player's IRC nickname.
        """
        self.name = name
        self.hand: list[Any] = []
        self.population: int = 0
        self.card_stack: list[Any] = []
        self.weapon: Any | None = None
        self.game: game | None = None
        self.state: int = PLAYER_STATE_ALIVE
        self.missturns: int = 0

    def __str__(self) -> str:
        return f"player({self.name})"

    def __repr__(self) -> str:
        return f"player('{self.name}')"

    def __card_by_idx(self, idx: int) -> Any:
        """Remove and return a card from the hand by index.

        Args:
            idx: Zero-based index into the player's hand.

        Returns:
            The card at the given index.

        Raises:
            IllegalMoveError: If the index is out of range.
        """
        if idx < 0 or idx >= len(self.hand):
            raise IllegalMoveError(
                self.game, self, f"Bad Card Index: {idx}"
            )
        assert len(self.card_stack) <= CARD_STACK_LEN
        return self.hand.pop(idx)

    def __card_by_name(self, name: str) -> Any:
        """Remove and return a card from the hand by name.

        Args:
            name: The string or repr representation of the card.

        Returns:
            The first matching card.

        Raises:
            IllegalMoveError: If no card with the given name is found.
        """
        strl = [str(x).lower() for x in self.hand]
        repl = [repr(x).lower() for x in self.hand]
        for i in range(len(self.hand)):
            if repl[i] == name.lower() or strl[i] == name.lower():
                return self.hand.pop(i)
        raise IllegalMoveError(self.game, self, f"Card {name} not found")

    def kill(self, suicide: bool = False) -> None:
        """Kill this player, optionally triggering retaliation.

        In war time a non-suicide death transitions the player to the
        *retaliating* state; otherwise the player goes straight to dead.

        Args:
            suicide: If True, skip retaliation (e.g. !suicide command).
        """
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

    def cards_to_hand(self) -> None:
        """Move all queued and deployed cards back into the hand."""
        self.hand.extend(self.card_stack)
        self.card_stack = []
        if self.weapon is not None:
            self.hand.append(self.weapon)
            self.weapon = None

    def flip_card(self, tgt: player | None) -> None:
        """Flip (execute) the first queued card during a normal turn.

        Args:
            tgt: Optional target player for weapon cards.

        Raises:
            IllegalMoveError: If the player cannot flip a card right now.
        """
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

    def use_card(self, arg: str, tgt: player | None) -> None:
        """Use a card during final retaliation.

        Args:
            arg: Either the integer index of a card or its name/repr.
            tgt: Optional target player.

        Raises:
            IllegalMoveError: If it is not this player's turn or they
                are not in the retaliation state.
        """
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
        """Push a card from the hand into the queue.

        Args:
            arg: Either the integer index of a card or its name/repr.

        Returns:
            The card that was queued.

        Raises:
            IllegalMoveError: If the queue is full or the player is dead.
        """
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
        """Apply population damage to this player.

        If population reaches zero the player is eliminated.

        Args:
            pwnage: Number of population millions to remove.
        """
        i = min(self.population, pwnage)
        self.population -= i
        if self.population == 0:
            self.kill()

    def transfer_population(self, converts: int, tgt: player) -> None:
        """Transfer population from this player to another.

        Args:
            converts: Maximum millions to transfer.
            tgt: The player who gains the population.

        Raises:
            IllegalMoveError: If this player is not alive.
        """
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
            self.kill()
