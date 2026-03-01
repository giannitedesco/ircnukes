"""IRC bot front-end for the Nuclear War card game.

Uses the :mod:`irc.bot` library (``python-irc``) to connect to a server,
join a channel, and dispatch game commands.
"""

from __future__ import annotations

import gzip
import os
import pickle
import time
from typing import Optional

import irc.bot  # type: ignore[import-untyped]
import irc.client  # type: ignore[import-untyped]
import irc.strings  # type: ignore[import-untyped]

import nukes
from ircnukes import IrcNukes

# ---------------------------------------------------------------------------
# Bot configuration (can be overridden via environment variables)
# ---------------------------------------------------------------------------

NICK: str = os.environ.get("NUKEBOT_NICK", "[skynet]")
NAME: str = os.environ.get("NUKEBOT_NAME", "ircnuk0rs")
HOST: str = os.environ.get("NUKEBOT_HOST", "irc.libera.chat")
PORT: int = int(os.environ.get("NUKEBOT_PORT", "6667"))
CHAN: str = os.environ.get("NUKEBOT_CHAN", "#nukes")
LOGDIR: str = os.environ.get("NUKEBOT_LOGDIR", "./saved-games")
DECK: str = os.environ.get(
    "NUKEBOT_DECK", "./decks/andrew.looney.deck"
)

# Characters allowed in saved-game names
_OK_CHARS: frozenset[str] = frozenset(
    "-+_.[]()"
    + "".join(chr(c) for c in range(ord("0"), ord("9") + 1))
    + "".join(chr(c) for c in range(ord("a"), ord("z") + 1))
)


class TokenBucket:
    """Rate-limiter using a token-bucket algorithm."""

    def __init__(self, rate: float, burst: float | None = None) -> None:
        """Initialise the token bucket."""
        self._rate = 1.0 / float(rate)
        self._burst = float(burst if burst is not None else rate) * self._rate
        self._toks = self._burst
        self._last = time.monotonic()

    def rate_limit(self, tokens: float = 1.0) -> None:
        """Block until *tokens* tokens are available."""
        if self._rate <= 0:
            return

        now = time.monotonic()
        self._toks += now - self._last
        self._last = now

        if self._toks > self._burst:
            self._toks = self._burst

        if self._toks >= self._rate:
            self._toks -= self._rate

        if self._toks < self._rate:
            time.sleep(self._rate - self._toks)


def _ok_char(c: str) -> bool:
    """Return True if *c* is allowed in a saved-game name."""
    return c in _OK_CHARS


def _name2path(name: str) -> str | None:
    """Convert a game name to its saved-game file path."""
    name = name.lower()
    filtered = "".join(c for c in name if _ok_char(c))
    if len(filtered) != len(name):
        return None
    return os.path.join(LOGDIR, f"{filtered}.gz")


def _path2name(path: str) -> str | None:
    """Convert a saved-game path back to the game name."""
    prefix = LOGDIR
    if len(path) <= len(prefix):
        return None
    rel = path[len(prefix):].lstrip("/")
    if not rel.endswith(".gz"):
        return None
    return rel[:-3]


class NukeBot(irc.bot.SingleServerIRCBot):  # type: ignore[misc]
    """IRC bot that hosts a Nuclear War card game."""

    def __init__(self) -> None:
        """Initialise the bot and connect to the IRC server."""
        server = irc.bot.ServerSpec(HOST, PORT)
        super().__init__([server], NICK, NAME)
        self._game: Optional[IrcNukes] = None
        self._tbf = TokenBucket(2.0, 5.0)
        os.makedirs(LOGDIR, exist_ok=True)

    def privmsg(self, tgt: str, msg: str) -> None:
        """Send a rate-limited PRIVMSG."""
        self._tbf.rate_limit()
        self.connection.privmsg(tgt, msg)

    @staticmethod
    def _get_nick(source: str) -> str:
        """Extract the nick from an IRC source mask."""
        return str(irc.strings.lower(irc.client.NickMask(source).nick))

    def _list_games(self) -> None:
        """Announce all saved games to the channel."""
        names = [
            _path2name(os.path.join(LOGDIR, f))
            for f in os.listdir(LOGDIR)
        ]
        valid = [n for n in names if n is not None]
        if valid:
            self.privmsg(CHAN, f"Saved Games: {', '.join(valid)}")
        else:
            self.privmsg(CHAN, "No saved games")

    def _save_game(self, game: IrcNukes, name: str) -> None:
        """Pickle the current game to a gzip file."""
        entries = os.listdir(LOGDIR)
        if len(entries) > 128:
            raise nukes.GameLogicError(game, "Hey, stop fucking around")

        path = _name2path(name)
        if path is None or _path2name(path) is None:
            self.privmsg(CHAN, "bad game-name, try [a-z0-9_-]")
            return

        game.save_prepare()
        try:
            with gzip.open(path, "wb") as f:
                pickle.dump(game, f)
        except OSError as e:
            self.privmsg(
                CHAN, f"Writing to {path} failed: {e.strerror or str(e)}",
            )
            game.save_done(self.privmsg, CHAN)
            game.dirty = True
            return
        game.save_done(self.privmsg, CHAN)
        self.privmsg(CHAN, f"game '{_path2name(path)}' saved to {path}")

    def _load_game(self, name: str) -> Optional[IrcNukes]:
        """Unpickle a game from a gzip file."""
        path = _name2path(name)
        if path is None or _path2name(path) is None:
            self.privmsg(CHAN, "bad game-name, try [a-z0-9_-]")
            return None

        try:
            with gzip.open(path, "rb") as f:
                ret: IrcNukes = pickle.load(f)
        except OSError as e:
            self.privmsg(
                CHAN, f"Reading from {path} failed: {e.strerror or str(e)}",
            )
            return None
        ret.save_done(self.privmsg, CHAN)
        self.privmsg(CHAN, f"game '{_path2name(path)}' loaded from {path}")
        return ret

    def on_welcome(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Join the game channel after connecting."""
        conn.join(CHAN)

    def on_join(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Greet the channel on join or log other users joining."""
        nick = self._get_nick(ev.source)
        if nick == irc.strings.lower(conn.get_nickname()):
            print(f"Joined: {ev.target}")
            self.privmsg(ev.target, "Would you like to play a game?")
            return
        print(f"{nick} joined {CHAN}")

    def on_privmsg(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a private message from a user."""
        nick = self._get_nick(ev.source)
        text: str = ev.arguments[0]
        print(f"[priv] <{nick}> {text}")
        self._handle_priv(nick, text)

    def on_pubmsg(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a public channel message."""
        nick = self._get_nick(ev.source)
        text: str = ev.arguments[0]
        print(f"[{ev.target}] <{nick}> {text}")
        if not text.startswith("!"):
            return
        self._handle_pub(nick, ev.target, text[1:])

    def on_action(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Log channel actions (/me)."""
        nick = self._get_nick(ev.source)
        print(f"[{ev.target}] * {nick} {ev.arguments[0]}")

    def on_quit(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a user quitting."""
        nick = self._get_nick(ev.source)
        reason = ev.arguments[0] if ev.arguments else ""
        print(f"{nick} quit ({reason})")
        self._handle_quit(nick)

    def on_kick(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a kick event."""
        kicker = self._get_nick(ev.source)
        kicked = ev.arguments[0] if ev.arguments else ev.target
        reason = ev.arguments[1] if len(ev.arguments) > 1 else ""
        print(f"{kicker} kicks {kicked} from {ev.target} ({reason})")

    def on_part(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a user parting the channel."""
        nick = self._get_nick(ev.source)
        reason = ev.arguments[0] if ev.arguments else ""
        print(f"{nick} left {ev.target} ({reason})")

    def on_nick(
        self, conn: irc.client.ServerConnection, ev: irc.client.Event
    ) -> None:
        """Handle a nick change."""
        old = self._get_nick(ev.source)
        new = irc.strings.lower(ev.target)
        print(f"{old} is now known as {new}")
        if self._game is not None:
            self._game.nick_change(old, new)

    def _handle_priv(self, nick: str, text: str) -> None:
        """Process a private message game command."""
        arg = text.split()
        if not arg:
            return

        if arg[0] == "help":
            tmp = IrcNukes(None, None)
            cmds = tmp.irc_list_pcmds()
            self.privmsg(nick, f"Commands: {' '.join(cmds)}")
            return

        if self._game is None:
            return

        try:
            self._game.irc_pcmd(nick, arg[0], arg[1:])
        except nukes.GameOverMan as e:
            self._end_game(e)
        except nukes.IllegalMoveError as e:
            self.privmsg(nick, f"{e.player}: Illegal Move: {e.desc}")
        except nukes.GameLogicError as e:
            if e.player is None:
                self.privmsg(nick, f"{nick}: Bad Command: {e.desc}")
            else:
                self.privmsg(nick, f"{e.player}: {e.desc}")

    def _handle_pub(self, nick: str, chan: str, text: str) -> None:
        """Process a public channel command (``!cmd ...``)."""
        arg = text.split()
        if not arg:
            return

        cmd = arg[0]

        if cmd == "create":
            try:
                self._game = IrcNukes(self.privmsg, chan, DECK)
            except nukes.GameLogicError as e:
                self.privmsg(chan, f"error: {DECK}: {e.desc}")
                return
            self.privmsg(chan, f"Game created: {self._game}")
            return

        if cmd == "savegame":
            if self._game is None:
                self.privmsg(chan, "No game to save")
            elif len(arg) < 2:
                self.privmsg(chan, "games need names baby")
            else:
                self._save_game(self._game, arg[1])
            return

        if cmd == "listgames":
            self._list_games()
            return

        if cmd == "loadgame":
            if self._game is not None and self._game.dirty:
                self.privmsg(chan, "Game in progress, save it first")
            elif len(arg) < 2:
                self.privmsg(chan, "!listgames to find one to load")
            else:
                self._game = self._load_game(arg[1])
            return

        if cmd == "help":
            tmp = IrcNukes(None, None)
            cmds = tmp.irc_list_cmds()
            cmds.extend(["creategame", "savegame", "loadgame", "listgames"])
            self.privmsg(chan, f"Commands: {' '.join(cmds)}")
            return

        if self._game is None:
            self.privmsg(chan, "No game, try !create")
            return

        try:
            self._game.irc_cmd(nick, cmd, arg[1:])
        except nukes.GameOverMan as e:
            self._end_game(e)
        except nukes.IllegalMoveError as e:
            self.privmsg(chan, f"{e.player}: Illegal Move: {e.desc}")
        except nukes.GameLogicError as e:
            if e.player is None:
                self.privmsg(chan, f"{nick}: {e.desc}")
            else:
                self.privmsg(chan, f"{e.player}: {e.desc}")

    def _handle_quit(self, nick: str) -> None:
        """Handle a player quitting IRC during a game."""
        if self._game is None:
            return
        try:
            p = self._game.get_player(nick)
            p.kill(suicide=True)
        except nukes.GameLogicError as e:
            print(f"quit: {e.desc}")
        except nukes.GameOverMan:
            print("quit: Game Over")

    def _end_game(self, e: nukes.GameOverMan) -> None:
        """Announce the end of the game and reset state."""
        if e.winner is None:
            self.privmsg(CHAN, "GameOver: MAD, noone wins")
        else:
            self.privmsg(
                CHAN,
                f"GameOver: winner is {e.winner.name} "
                f"with {e.winner.population} million population",
            )
        self._game = None


if __name__ == "__main__":
    bot = NukeBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.connection.quit("Mutually Assured Destruction")

