GAME_STATE_INIT		= 0
GAME_STATE_PEACE 	= 1
GAME_STATE_WAR 		= 2
GAME_STATE_OVER 	= 3

# Player starts out as alive, is this way until population hits 0
# if it's war they go to retaliation state until they use !done then
# they go to dead state, if it's peace they go straight to dead
# skipping retaliation altogether
PLAYER_STATE_ALIVE	= 1
PLAYER_STATE_RETALIATE	= 2
PLAYER_STATE_DEAD	= 3

CARD_STACK_LEN		= 2

NUKE_YIELD_10MT 	= 10
NUKE_YIELD_20MT 	= 20
NUKE_YIELD_50MT 	= 50
NUKE_YIELD_100MT 	= 100

class IllegalMoveError(Exception):
	def __init__(self, g, p, desc):
		self.game = g
		self.player = p
		self.desc = desc

class GameLogicError(Exception):
	def __init__(self, g, desc, player=None):
		self.game = g
		self.desc = desc
		self.player = player

class GameOverMan(Exception):
	def __init__(self, g, winner=None):
		self.game = g
		self.winner = winner
