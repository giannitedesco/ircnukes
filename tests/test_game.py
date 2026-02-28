"""Unit tests for the Nuclear War game engine."""

from __future__ import annotations

import pytest
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nukes
from nukes.globals import (
    GAME_STATE_INIT,
    GAME_STATE_PEACE,
    GAME_STATE_WAR,
    PLAYER_STATE_ALIVE,
    PLAYER_STATE_DEAD,
    PLAYER_STATE_RETALIATE,
    IllegalMoveError,
    GameLogicError,
    GameOverMan,
)
from nukes.player import player
from nukes.warhead import warhead
from nukes.missile import missile
from nukes.bomber import bomber
from nukes.propaganda import propaganda
from nukes.deck import deck


# ---------------------------------------------------------------------------
# Minimal concrete game subclass for testing
# ---------------------------------------------------------------------------

class _TestGame(nukes.game):
    """Concrete game subclass that captures messages for testing."""

    def __init__(self, name: str = "test") -> None:
        self.messages: list[str] = []
        self.player_messages: list[tuple[str, str]] = []
        super().__init__(name)

    def demilitarize(self) -> None:
        self.messages.append("PEACE")

    def pass_control(self, p: nukes.player) -> None:
        self.messages.append(f"TURN:{p.name}")

    def game_msg(self, msg: str) -> None:
        self.messages.append(msg)

    def player_msg(self, p: nukes.player, msg: str) -> None:
        self.player_messages.append((p.name, msg))

    def war(self) -> None:
        self.messages.append("WAR")


def _make_game_with_players(*nicks: str) -> _TestGame:
    """Create a test game and add players without starting."""
    g = _TestGame()
    for nick in nicks:
        p = player(nick)
        g.add_player(p)
    return g


def _make_started_game(*nicks: str) -> _TestGame:
    """Create a test game, add players, and deal cards (commence)."""
    g = _make_game_with_players(*nicks)
    g.commence()
    return g


# ---------------------------------------------------------------------------
# Test: player
# ---------------------------------------------------------------------------

class TestPlayer:
    def test_initial_state(self) -> None:
        p = player("alice")
        assert p.name == "alice"
        assert p.population == 0
        assert p.hand == []
        assert p.card_stack == []
        assert p.state == PLAYER_STATE_ALIVE

    def test_str_repr(self) -> None:
        p = player("bob")
        assert str(p) == "player(bob)"
        assert repr(p) == "player('bob')"

    def test_cards_to_hand(self) -> None:
        p = player("alice")
        w = warhead(10)
        m = missile(10)
        p.hand = [w]
        p.card_stack = [m]
        p.weapon = warhead(20)
        p.cards_to_hand()
        assert len(p.hand) == 3
        assert p.card_stack == []
        assert p.weapon is None

    def test_kill_no_game(self) -> None:
        p = player("alice")
        p.kill()  # should not raise


# ---------------------------------------------------------------------------
# Test: deck
# ---------------------------------------------------------------------------

class TestDeck:
    def test_empty_deck_returns_none(self) -> None:
        d = deck("test")
        assert d.deal_card() is None

    def test_add_and_deal(self) -> None:
        d = deck("test")
        d.add_card(5, warhead, [10])
        card = d.deal_card()
        assert card is not None
        assert isinstance(card, warhead)

    def test_replenish(self) -> None:
        d = deck("test")
        d.add_card(1, warhead, [10])
        for _ in range(10):  # deal more than the max, should replenish
            c = d.deal_card()
            assert c is not None

    def test_len(self) -> None:
        d = deck("test")
        d.add_card(3, warhead, [10])
        d.add_card(2, missile, [10])
        assert len(d) == 5


# ---------------------------------------------------------------------------
# Test: game state machine
# ---------------------------------------------------------------------------

class TestGame:
    def test_initial_state(self) -> None:
        g = _TestGame()
        assert g.state() == GAME_STATE_INIT

    def test_add_player(self) -> None:
        g = _TestGame()
        p = player("alice")
        g.add_player(p)
        assert g.get_player("alice") is p

    def test_duplicate_player_raises(self) -> None:
        g = _TestGame()
        g.add_player(player("alice"))
        with pytest.raises(GameLogicError):
            g.add_player(player("alice"))

    def test_too_few_players_raises(self) -> None:
        g = _TestGame()
        g.add_player(player("alice"))
        with pytest.raises(GameLogicError):
            g.commence()

    def test_commence_deals_cards(self) -> None:
        g = _make_started_game("alice", "bob")
        alice = g.get_player("alice")
        bob = g.get_player("bob")
        assert alice.population > 0
        assert bob.population > 0
        assert len(alice.hand) == 9
        assert len(bob.hand) == 9

    def test_state_transitions_to_peace(self) -> None:
        g = _make_started_game("alice", "bob")
        assert g.state() == GAME_STATE_PEACE

    def test_get_player_missing_raises(self) -> None:
        g = _TestGame()
        with pytest.raises(GameLogicError):
            g.get_player("nobody")

    def test_rename_player(self) -> None:
        g = _make_game_with_players("alice")
        alice = g.get_player("alice")
        g.rename_player(alice, "ALICE")
        assert g.get_player("ALICE") is alice
        with pytest.raises(GameLogicError):
            g.get_player("alice")

    def test_rename_duplicate_raises(self) -> None:
        g = _make_game_with_players("alice", "bob")
        with pytest.raises(GameLogicError):
            g.rename_player(g.get_player("alice"), "bob")


# ---------------------------------------------------------------------------
# Test: warhead / missile / bomber cards
# ---------------------------------------------------------------------------

class TestCards:
    def test_warhead_invalid_yield(self) -> None:
        with pytest.raises(ValueError):
            warhead(999)

    def test_warhead_str_repr(self) -> None:
        w = warhead(10)
        assert str(w) == "w10"
        assert repr(w) == "warhead(10)"

    def test_missile_str_repr(self) -> None:
        m = missile(10, "polaris")
        assert str(m) == "polaris"
        assert repr(m) == "polaris(10)"

    def test_missile_default_str(self) -> None:
        m = missile(20)
        assert str(m) == "missile(20)"

    def test_bomber_str_repr(self) -> None:
        b = bomber(50, "b70")
        assert str(b) == "b70"
        assert repr(b) == "b70(50/50)"

    def test_propaganda_str_repr(self) -> None:
        p = propaganda(5)
        assert str(p) == "p5"
        assert repr(p) == "propaganda(5)"

    def test_missile_deploys_as_weapon(self) -> None:
        g = _make_started_game("alice", "bob")
        alice = g.get_player("alice")
        # Give alice a missile then a warhead in her queue (FIFO queue)
        m = missile(20)
        w = warhead(10)
        alice.hand.insert(0, m)
        alice.queue_card("0")  # missile is first in queue
        alice.hand.insert(0, w)
        alice.queue_card("0")  # warhead is second

        # Make it alice's turn; flip the first queued card (missile)
        g.cur = alice
        assert alice.weapon is None
        alice.flip_card(None)
        # After flipping the missile card, alice should have it as weapon
        assert alice.weapon is m

    def test_warhead_requires_target(self) -> None:
        g = _make_started_game("alice", "bob")
        alice = g.get_player("alice")
        w = warhead(10)
        with pytest.raises(IllegalMoveError):
            w.dequeue(g, alice, None)

    def test_propaganda_requires_target_in_peace(self) -> None:
        g = _make_started_game("alice", "bob")
        alice = g.get_player("alice")
        prop = propaganda(5)
        with pytest.raises(IllegalMoveError):
            prop.dequeue(g, alice, None)

    def test_propaganda_dumps_in_war(self) -> None:
        g = _make_started_game("alice", "bob")
        alice = g.get_player("alice")
        prop = propaganda(5)
        g.transition(GAME_STATE_WAR)
        # Should not raise; just dump the card
        prop.dequeue(g, alice, None)
        assert "dumps propaganda" in " ".join(g.messages)


# ---------------------------------------------------------------------------
# Test: GameOverMan / exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_illegal_move_error(self) -> None:
        e = IllegalMoveError(None, None, "oops")
        assert e.desc == "oops"
        assert str(e) == "oops"

    def test_game_logic_error(self) -> None:
        e = GameLogicError(None, "bad state")
        assert e.desc == "bad state"

    def test_game_over_man_with_winner(self) -> None:
        g = _TestGame()
        p = player("winner")
        exc = GameOverMan(g, p)
        assert exc.winner is p
        assert "winner" in str(exc)

    def test_game_over_man_no_winner(self) -> None:
        g = _TestGame()
        exc = GameOverMan(g)
        assert exc.winner is None
        assert "over" in str(exc).lower()


# ---------------------------------------------------------------------------
# Test: ircnukes wrapper
# ---------------------------------------------------------------------------

class TestIrcNukes:
    def test_create_and_list_cmds(self) -> None:
        from ircnukes import ircnukes as IrcNukes
        messages: list[str] = []
        def privmsg(tgt: str, msg: str) -> None:
            messages.append(f"{tgt}: {msg}")
        g = IrcNukes(privmsg, "#test")
        cmds = g.irc_list_cmds()
        assert "join" in cmds
        assert "status" in cmds
        assert "start" in cmds

    def test_list_pcmds(self) -> None:
        from ircnukes import ircnukes as IrcNukes
        g = IrcNukes(None, None)
        pcmds = g.irc_list_pcmds()
        assert "hand" in pcmds
        assert "queue" in pcmds
        assert "push" in pcmds

    def test_join_game(self) -> None:
        from ircnukes import ircnukes as IrcNukes
        messages: list[str] = []
        def privmsg(tgt: str, msg: str) -> None:
            messages.append(msg)
        g = IrcNukes(privmsg, "#test")
        g.irc_cmd("alice", "join", [])
        assert any("alice" in m for m in messages)

    def test_unknown_command(self) -> None:
        from ircnukes import ircnukes as IrcNukes
        messages: list[str] = []
        def privmsg(tgt: str, msg: str) -> None:
            messages.append(msg)
        g = IrcNukes(privmsg, "#test")
        # alice must be a player for the "not known" path to be reached
        g.irc_cmd("alice", "join", [])
        messages.clear()
        g.irc_cmd("alice", "unknowncmd", [])
        assert any("not known" in m for m in messages)

    def test_nick_change(self) -> None:
        from ircnukes import ircnukes as IrcNukes
        messages: list[str] = []
        def privmsg(tgt: str, msg: str) -> None:
            messages.append(msg)
        g = IrcNukes(privmsg, "#test")
        g.irc_cmd("alice", "join", [])
        g.nick_change("alice", "alice2")
        # alice2 should now be a valid player
        p = g.get_player("alice2")
        assert p.name == "alice2"
