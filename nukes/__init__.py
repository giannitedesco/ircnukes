"""Nuclear War card game engine."""

from .globals import (
    GameState,
    PlayerState,
    NukeYield,
    GAME_STATE_INIT,
    GAME_STATE_PEACE,
    GAME_STATE_WAR,
    GAME_STATE_OVER,
    PLAYER_STATE_ALIVE,
    PLAYER_STATE_RETALIATE,
    PLAYER_STATE_DEAD,
    CARD_STACK_LEN,
    NUKE_YIELD_10MT,
    NUKE_YIELD_15MT,
    NUKE_YIELD_20MT,
    NUKE_YIELD_40MT,
    NUKE_YIELD_50MT,
    NUKE_YIELD_75MT,
    NUKE_YIELD_100MT,
    NUKE_YIELD_200MT,
    IllegalMoveError,
    GameLogicError,
    GameOverMan,
)
from .game import Game
from .player import Player
from .card import Card
from .propaganda import Propaganda
from .missile import Missile
from .warhead import Warhead
from .bomber import Bomber

# Backward-compatible lowercase aliases
game = Game
player = Player
card = Card
propaganda = Propaganda
missile = Missile
warhead = Warhead
bomber = Bomber

__all__ = [
    "GameState",
    "PlayerState",
    "NukeYield",
    "GAME_STATE_INIT",
    "GAME_STATE_PEACE",
    "GAME_STATE_WAR",
    "GAME_STATE_OVER",
    "PLAYER_STATE_ALIVE",
    "PLAYER_STATE_RETALIATE",
    "PLAYER_STATE_DEAD",
    "CARD_STACK_LEN",
    "NUKE_YIELD_10MT",
    "NUKE_YIELD_15MT",
    "NUKE_YIELD_20MT",
    "NUKE_YIELD_40MT",
    "NUKE_YIELD_50MT",
    "NUKE_YIELD_75MT",
    "NUKE_YIELD_100MT",
    "NUKE_YIELD_200MT",
    "IllegalMoveError",
    "GameLogicError",
    "GameOverMan",
    "Game",
    "Player",
    "Card",
    "Propaganda",
    "Missile",
    "Warhead",
    "Bomber",
    # Backward-compat aliases
    "game",
    "player",
    "card",
    "propaganda",
    "missile",
    "warhead",
    "bomber",
]
