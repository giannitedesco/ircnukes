GAME_STATE_INIT		= 0
GAME_STATE_PEACE 	= 1
GAME_STATE_WAR 		= 2
GAME_STATE_OVER 	= 3

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
