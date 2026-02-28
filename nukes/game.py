"""Core game logic and state machine for Nuclear War."""

from __future__ import annotations

import random
from typing import Any, Callable

from .globals import (
    CARD_STACK_LEN,
    GAME_STATE_INIT,
    GAME_STATE_OVER,
    GAME_STATE_PEACE,
    GAME_STATE_WAR,
    PLAYER_STATE_ALIVE,
    PLAYER_STATE_DEAD,
    PLAYER_STATE_RETALIATE,
    GameLogicError,
    GameOverMan,
)
from .player import player
from .deck import deck
from .propaganda import propaganda
from .missile import missile
from .bomber import bomber
from .warhead import warhead


class game:
    """Core game-state machine for a Nuclear War card game."""

    def __init__(
        self, name: str = "nukes", deckfile: str | None = None
    ) -> None:
        """Initialise a new game with optional deck file."""
        self.__name = name
        self.__state = GAME_STATE_INIT
        self.__popcards = deck("population")
        self.__deck = deck("main")
        self.__players: dict[str, player] = {}
        self.__turn: list[player] = []
        self.cur: player | None = None

        self.__popcards.add_card(12, int, [1])
        self.__popcards.add_card(10, int, [2])
        self.__popcards.add_card(8, int, [5])
        self.__popcards.add_card(6, int, [10])
        self.__popcards.add_card(4, int, [25])

        if deckfile is None:
            return

        try:
            with open(deckfile, "r") as f:
                self.__deck.load_file(
                    f,
                    {
                        "warhead": warhead,
                        "missile": missile,
                        "bomber": bomber,
                        "propaganda": propaganda,
                    },
                )
        except OSError as e:
            raise GameLogicError(self, e.strerror or str(e)) from e
        except GameLogicError:
            raise
        except Exception as e:
            raise GameLogicError(self, str(e)) from e

        print(
            f"Game init: {self.__name} "
            f"(got {len(self.__deck)} cards from deck {deckfile})"
        )

    def __str__(self) -> str:
        return f"game({self.__name})"

    def __repr__(self) -> str:
        return f"game({self.__name})"

    def demilitarize(self) -> None:
        """Called when the game transitions from war back to peace."""
        raise NotImplementedError("demilitarize")

    def pass_control(self, p: player) -> None:
        """Called to hand the turn to player *p*."""
        raise NotImplementedError("pass_control")

    def player_msg(self, p: player, msg: str) -> None:
        """Send a private message to a single player."""
        print(f" >> {p}: {msg}")

    def game_msg(self, msg: str) -> None:
        """Broadcast a message to all players."""
        print(f" >> {self}: {msg}")

    def player_dead(self, p: player) -> None:
        """Handle a player death, checking for game-over conditions."""
        while p in self.__turn:
            self.__turn.remove(p)

        if len(self.__alive()) == 0:
            p.state = PLAYER_STATE_DEAD

        if len(self.__alive()) == 0:
            raise GameOverMan(self)
        elif (
            len(self.__alive() + self.__retaliate()) == 1
            and p.state != PLAYER_STATE_RETALIATE
            and self.__state != GAME_STATE_INIT
        ):
            raise GameOverMan(self, self.__alive()[0])

        if p.state == PLAYER_STATE_RETALIATE:
            if self.cur is p:
                self.next_turn()
            return

        if self.__state == GAME_STATE_INIT:
            if p.name in self.__players:
                del self.__players[p.name]
        else:
            if self.cur is p:
                self.next_turn()

    def get_player(self, name: str) -> player:
        """Look up a player by name."""
        if name in self.__players:
            return self.__players[name]
        raise GameLogicError(self, f"No such player: {name}")

    def rename_player(self, p: player, new_name: str) -> None:
        """Rename a player (handles IRC nick changes)."""
        if new_name in self.__players:
            raise GameLogicError(self, f"Already a player {new_name}")
        self.__players[new_name] = p
        del self.__players[p.name]
        p.name = new_name

    def state(self) -> int:
        """Return the current game state constant."""
        return self.__state

    def war(self) -> None:
        """Hook called when the game transitions to war."""
        return

    def transition(self, state: int) -> None:
        """Transition the game between peace and war."""
        assert state in (GAME_STATE_PEACE, GAME_STATE_WAR)
        if self.__state == state:
            return
        self.__state = state
        if self.__state == GAME_STATE_WAR:
            self.war()
        else:
            for p in self.__alive():
                p.cards_to_hand()
            self.demilitarize()

    def __get_pop(self) -> Any:
        return self.__popcards.deal_card()

    def deal_card(self) -> Any:
        """Pick the top card from the main deck."""
        return self.__deck.deal_card()

    def add_player(self, p: player) -> None:
        """Add a player to the lobby before the game starts."""
        assert p.population == 0
        assert len(p.hand) == 0
        assert len(p.card_stack) == 0

        if self.__state != GAME_STATE_INIT:
            raise GameLogicError(self, "Game already started")
        if p.name in self.__players:
            raise GameLogicError(self, "Duplicate player name")

        print(f"{self}: {p}")
        self.__players[p.name] = p
        p.game = self

    def deal_in_player(self, p: player) -> None:
        """Deal initial cards and population to a player."""
        for _ in range(9):
            p.population += self.__get_pop()
        for _ in range(9):
            p.hand.append(self.deal_card())

    def commence(self) -> None:
        """Start the game and deal cards to all players."""
        if self.__state != GAME_STATE_INIT:
            raise GameLogicError(self, "Game already started")
        if len(self.__players) < 2:
            raise GameLogicError(self, "Lonely without players")
        for p in self.__players.values():
            self.deal_in_player(p)
        self.__state = GAME_STATE_PEACE
        self.game_msg("Game started")
        self.next_turn()

    def apocalypse(self) -> None:
        """Kill all players simultaneously (nuclear apocalypse)."""
        for p in self.__players.values():
            p.state = PLAYER_STATE_DEAD
        raise GameOverMan(self)

    def __retaliate(self) -> list[player]:
        return [
            p for p in self.__players.values()
            if p.state == PLAYER_STATE_RETALIATE
        ]

    def __alive(self) -> list[player]:
        return [
            p for p in self.__players.values()
            if p.state == PLAYER_STATE_ALIVE
        ]

    def get_players(self) -> list[player]:
        """Return all players (alive, retaliating, and dead)."""
        return list(self.__players.values())

    def next_turn(self) -> None:
        """Advance the game to the next player's turn."""
        if self.__state in (GAME_STATE_OVER, GAME_STATE_INIT):
            raise GameLogicError(self, "Game not in progress")

        if self.cur is not None and self.cur.state == PLAYER_STATE_RETALIATE:
            self.cur.state = PLAYER_STATE_DEAD
            game.player_dead(self, self.cur)

        while self.__retaliate():
            self.cur = self.__retaliate()[0]
            if self.__alive():
                self.pass_control(self.cur)
                return
            else:
                self.cur.state = PLAYER_STATE_DEAD
                break

        if not self.__alive():
            raise GameOverMan(self)
        elif len(self.__alive()) == 1:
            raise GameOverMan(self, self.__alive()[0])

        if self.cur is not None and self.cur.state == PLAYER_STATE_DEAD:
            self.transition(GAME_STATE_PEACE)

        while True:
            if not self.__turn:
                self.__turn = self.__alive()

            self.cur = self.__turn.pop(0)
            if self.cur.missturns:
                self.cur.missturns -= 1
                self.game_msg(f"{self.cur.name}: Miss a turn")
                continue
            self.pass_control(self.cur)
            break
