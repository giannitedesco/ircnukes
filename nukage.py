"""Test harness for the ircnukes IRC bot."""

from __future__ import annotations

import random
import sys
from typing import Optional

import nukes
from ircnukes import IrcNukes
from nukebot import CHAN, DECK


class FakeConn:
    """Minimal stand-in for an IRC server connection."""

    def privmsg(self, to: str, msg: str) -> None:
        print(f">>> <{to}> {msg}")

    def quit(self, msg: str) -> None:
        print(f">>> QUIT ({msg})")


_conn = FakeConn()
_game: Optional[IrcNukes] = None


def _barf(msg: str) -> None:
    print(msg)
    raise SystemExit(1)


def _privmsg(tgt: str, msg: str) -> None:
    _conn.privmsg(tgt, msg)


def cmd_pub(
    nick: str, chan: str, text: str, logit: bool = True
) -> None:
    """Simulate a public channel command."""
    global _game
    if logit:
        print(f"<<< {nick} !{text}")
    arg = text.split()
    if not arg:
        return

    cmd = arg[0]

    if cmd == "create":
        try:
            _game = IrcNukes(_privmsg, chan, DECK)
        except nukes.GameLogicError as e:
            print(f"error: {DECK}: {e.desc}")
            return
        print(f"Game created: {_game}")
        return

    if cmd == "savegame":
        if _game is None:
            print("No game to save")
        elif len(arg) < 2:
            print("games need names baby")
        return

    if cmd == "listgames":
        return

    if cmd == "loadgame":
        return

    if cmd == "help":
        tmp = IrcNukes(None, None)
        cmds = tmp.irc_list_cmds()
        cmds.extend(["creategame", "savegame", "loadgame", "listgames"])
        print(f"Commands: {' '.join(cmds)}")
        return

    if _game is None:
        print("No game, try !create")
        return

    try:
        _game.irc_cmd(nick, cmd, arg[1:])
    except nukes.GameOverMan as e:
        if e.winner is None:
            print("GameOver: MAD, noone wins")
        else:
            print(
                f"GameOver: winner is {e.winner.name} "
                f"with {e.winner.population} million population"
            )
        _game = None
    except nukes.IllegalMoveError as e:
        print(f"{e.player}: Illegal Move: {e.desc}")
    except nukes.GameLogicError as e:
        if e.player is None:
            print(f"{nick}: {e.desc}")
        else:
            print(f"{e.player}: {e.desc}")


def cmd_priv(nick: str, text: str) -> None:
    """Simulate a private message command."""
    global _game
    arg = text.split()
    if not arg:
        return

    if arg[0] == "help":
        tmp = IrcNukes(None, None)
        cmds = tmp.irc_list_pcmds()
        print(f"Commands: {' '.join(cmds)}")
        return

    if _game is None:
        return

    try:
        _game.irc_pcmd(nick, arg[0], arg[1:])
    except nukes.GameOverMan as e:
        if e.winner is None:
            print("GameOver: MAD, noone wins")
        else:
            print(
                f"GameOver: winner is {e.winner.name} "
                f"with {e.winner.population} million population"
            )
        _game = None
    except nukes.IllegalMoveError as e:
        print(f"{e.player}: Illegal Move: {e.desc}")
    except nukes.GameLogicError as e:
        if e.player is None:
            print(f"{nick}: Bad Command: {e.desc}")
        else:
            print(f"{e.player}: {e.desc}")


def cmd_nick(old: str, new: str) -> None:
    """Simulate a nick change."""
    global _game
    if _game is None:
        return
    _game.nick_change(old, new)


def cmd_quit(nick: str) -> None:
    """Simulate a user quitting IRC."""
    global _game
    if _game is None:
        return
    try:
        p = _game.get_player(nick)
        p.kill(suicide=True)
    except nukes.GameLogicError as e:
        print(f"quit: {e.desc}")
    except nukes.GameOverMan:
        print("quit: Game Over")


def cmd_kick(kicker: str, kicked: str) -> None:
    """Simulate a kick event."""
    pass


def cmd_part(nick: str) -> None:
    """Simulate a user parting the channel."""
    pass


def testbed() -> None:
    """Run an interactive test script read from stdin."""
    try:
        for raw_line in sys.stdin:
            line = raw_line.rstrip("\n")
            if not line:
                break
            arr = line.split(" ", 2)
            if len(arr) < 2:
                _barf(f"Bad line: {arr}")

            if arr[0] == "randomseed":
                seed = int(arr[1])
                print(f"Seed is {seed}")
                random.seed(seed)
                continue

            print(f"<<< {line}")

            if arr[0] == "chan":
                if len(arr) < 3:
                    _barf(f"Bad line: {arr}")
                cmd_pub(arr[1], CHAN, arr[2], logit=False)
            elif arr[0] == "priv":
                if len(arr) < 3:
                    _barf(f"Bad line: {arr}")
                cmd_priv(arr[1], arr[2])
            elif arr[0] == "nick":
                if len(arr) < 3:
                    _barf(f"Bad line: {arr}")
                cmd_nick(arr[1], arr[2])
            elif arr[0] == "quit":
                cmd_quit(arr[1])
            elif arr[0] == "kick":
                if len(arr) < 3:
                    _barf(f"Bad line: {arr}")
                cmd_kick(arr[1], arr[2])
            elif arr[0] == "part":
                cmd_part(arr[1])
            elif arr[0] == "join":
                cmd_part(arr[1])
            else:
                _barf(f"Bad cmd: {arr}")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    testbed()
