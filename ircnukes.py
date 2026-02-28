"""IRC-aware wrapper around the Nuclear War game engine."""

from __future__ import annotations

from typing import Callable

import nukes
from irc.strings import lower as irc_lower  # type: ignore[import-untyped]


# Type alias for a privmsg-style callable: (target, message) -> None
PrivmsgFn = Callable[[str, str], None]


class ircnukes(nukes.game):
    """A :class:`nukes.game` sub-class wired to an IRC connection."""

    def __init__(
        self,
        conn: PrivmsgFn | None,
        chan: str | None,
        deck: str | None = None,
    ) -> None:
        """Initialise the IRC game."""
        # Declare instance variable types
        self.__nc: dict[str, Callable[..., None]] = {}
        self.__cmd: dict[str, Callable[..., None]] = {}
        self.__pcmd: dict[str, Callable[..., None]] = {}
        self.__pcmd_alias: dict[str, str] = {}
        self.__privmsg: PrivmsgFn | None = None
        self.__chan: str | None = None
        self.dirty: bool = False
        self.save_done(conn, chan)
        nukes.game.__init__(self, chan or "nukes", deck)

    def save_prepare(self) -> None:
        """Prepare the object for pickling."""
        self.__nc = {}
        self.__cmd = {}
        self.__pcmd = {}
        self.__privmsg = None
        self.__chan = None
        self.dirty = False

    def save_done(self, conn: PrivmsgFn | None, chan: str | None) -> None:
        """Restore a freshly loaded/saved game ready for use."""
        self.__nc = {
            "join": self.__joingame,
            "status": self.__status,
        }
        self.__cmd = {
            "start": self.__startgame,
            "suicide": self.__suicide,
            "flip": self.__flip,
            "use": self.__use,
            "done": self.__done,
        }
        self.__pcmd = {
            "hand": self.__get_hand,
            "queue": self.__get_queue,
            "population": self.__get_pop,
            "push": self.__push_card,
        }
        self.__pcmd_alias = {
            "h": "hand",
            "p": "push",
            "q": "queue",
            "pop": "population",
        }
        self.__privmsg = conn
        self.__chan = chan
        self.dirty = False

    def pass_control(self, p: nukes.player) -> None:
        """Announce whose turn it is."""
        assert p.state != nukes.PLAYER_STATE_DEAD
        if p.state == nukes.PLAYER_STATE_ALIVE:
            self.game_msg(f"{p.name} it's your go!")
            return
        self.game_msg(f"{p.name}, it's time for final retaliation!")
        self.game_msg(f"{p.name} has: {p.hand}")

    def deal_in_player(self, p: nukes.player) -> None:
        """Deal cards to a player and notify them of their starting hand."""
        nukes.game.deal_in_player(self, p)
        self.__get_pop(p)
        self.__get_hand(p)
        self.__get_queue(p)
        self.dirty = True

    def nick_change(self, old: str, new: str) -> None:
        """Handle an IRC nick change for an in-game player."""
        if old == new:
            return
        try:
            p = self.get_player(old)
            self.rename_player(p, new)
            self.dirty = True
        except nukes.GameLogicError as e:
            self.game_msg(f"Error renaming {old} to {new}: {e.desc}")

    def add_player(self, p: nukes.player) -> None:
        """Add a player to the game lobby."""
        nukes.game.add_player(self, p)

    def war(self) -> None:
        """Announce war in the IRC channel."""
        self.game_msg("\x02\x034,99WAR DECLARED!\x02\x03")

    def demilitarize(self) -> None:
        """Announce the return to peace in the IRC channel."""
        self.game_msg(
            "\x02\x033,99Peace time\x02\x03, re-create your queues!"
        )

    def player_dead(self, p: nukes.player) -> None:
        """Announce a player's death and advance the game state."""
        if self.state() == nukes.GAME_STATE_INIT:
            self.game_msg(f"{p.name} was deterred and ran home crying")
        elif self.state() == nukes.GAME_STATE_WAR:
            self.game_msg(f"{p.name} reduced to rubble.. loser")
        else:
            self.game_msg(f"{p.name} died from a peace offensive")
        nukes.game.player_dead(self, p)

    def player_msg(self, p: nukes.player, msg: str) -> None:
        """Send a private message to a player via IRC."""
        if self.__privmsg is not None:
            self.__privmsg(p.name, msg)

    def game_msg(self, msg: str) -> None:
        """Send a message to the game channel via IRC."""
        if self.__privmsg is not None and self.__chan is not None:
            self.__privmsg(self.__chan, msg)

    def get_player(self, name: str) -> nukes.player:
        """Return a player by IRC nick (case-insensitive lookup)."""
        return nukes.game.get_player(self, irc_lower(name))

    # ------------------------------------------------------------------
    # Private message commands
    # ------------------------------------------------------------------

    def __get_pop(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """View your population."""
        self.player_msg(p, f"Population {p.population}M")

    def __get_hand(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """View the cards in your hand."""
        self.player_msg(p, f"Hand: {p.hand}")

    def __get_queue(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """View the contents of your card queue."""
        if not p.card_stack:
            self.player_msg(p, "Queue: <empty>")
            return
        self.player_msg(p, f"Queue: {p.card_stack}")

    def __push_card(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Push a card into your queue."""
        if arg is None or len(arg) < 1:
            return
        p.queue_card(arg[0])
        self.__get_queue(p)
        self.dirty = True

    # ------------------------------------------------------------------
    # Channel commands
    # ------------------------------------------------------------------

    def __startgame(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Start a new game in the current channel."""
        self.commence()
        self.dirty = True

    def __suicide(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Leave a game at any time."""
        p.kill(suicide=True)
        self.dirty = True

    def __joingame(
        self,
        nick: str,
        cmd: str = "",
        args: list[str] | None = None,
    ) -> None:
        """Join a game that has been created."""
        p = nukes.player(nick)
        self.add_player(p)
        self.game_msg(f"{p} joins the game")
        self.dirty = True

    def __flip(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Flip the first card in your queue when it's your turn."""
        if arg and len(arg) >= 1:
            tgt: nukes.player | None = self.get_player(arg[0])
        else:
            tgt = None

        p.flip_card(tgt)
        p.hand.append(self.deal_card())
        self.__get_hand(p)
        self.next_turn()
        self.dirty = True

    def __use(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Flip any card in your hand during final retaliation."""
        if arg is None or len(arg) < 1:
            raise nukes.IllegalMoveError(self, p, "No card specified")
        tgt: nukes.player | None
        if len(arg) >= 2:
            tgt = self.get_player(arg[1])
        else:
            tgt = None
        p.use_card(arg[0], tgt)
        self.dirty = True

    def __done(
        self,
        p: nukes.player,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """Finish your retaliation."""
        if p != self.cur:
            raise nukes.IllegalMoveError(self, p, "Not your turn")
        self.next_turn()
        self.dirty = True

    def __status(
        self,
        nick: str,
        cmd: str = "",
        arg: list[str] | None = None,
    ) -> None:
        """View game or player status."""
        state_labels = {
            nukes.PLAYER_STATE_ALIVE: "alive",
            nukes.PLAYER_STATE_RETALIATE: "retaliating",
            nukes.PLAYER_STATE_DEAD: "dead",
        }

        if self.state() == nukes.GAME_STATE_PEACE:
            self.game_msg("\x02\x033,99Peace time\x03:\x02")
        elif self.state() == nukes.GAME_STATE_WAR:
            self.game_msg("\x02\x034,99War time\x03:\x02")
        else:
            self.game_msg("Game status:")

        players: list[nukes.player]
        if arg and len(arg) >= 1:
            players = [self.get_player(name) for name in arg]
        else:
            players = self.get_players()

        for x in players:
            weapon_str = f": {x.weapon!r}" if x.weapon is not None else ""
            cur_str = " (*)" if self.cur is x else ""
            self.game_msg(
                f" > {x.name}: {state_labels[x.state]}"
                f"{weapon_str}{cur_str}"
            )

    # ------------------------------------------------------------------
    # Public IRC dispatch
    # ------------------------------------------------------------------

    def irc_cmd(self, nick: str, cmd: str, args: list[str]) -> None:
        """Dispatch a channel command from an IRC user."""
        cmd = cmd.lower()

        if cmd in self.__nc:
            self.__nc[cmd](nick, cmd, args)
            return

        p = self.get_player(nick)

        if cmd in self.__cmd:
            self.__cmd[cmd](p, cmd, args)
            return

        self.game_msg(f"{nick}: command '{cmd}' not known")

    def irc_pcmd(self, nick: str, cmd: str, args: list[str]) -> None:
        """Dispatch a private-message command from an IRC user."""
        p = self.get_player(nick)
        cmd = self.__pcmd_alias.get(cmd, cmd)

        if cmd in self.__pcmd:
            self.__pcmd[cmd](p, cmd, args)
            return

        if self.__privmsg is not None:
            self.__privmsg(nick, f"{nick}: command '{cmd}' not known")

    def irc_list_cmds(self) -> list[str]:
        """Return all available channel command names."""
        ret = list(self.__nc.keys())
        ret.extend(self.__cmd.keys())
        return ret

    def irc_list_pcmds(self) -> list[str]:
        """Return all available private-message command names."""
        return list(self.__pcmd.keys())
