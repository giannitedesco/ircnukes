# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later

import random
from globals import *
from propaganda import propaganda
from missile import missile
from bomber import bomber
from warhead import warhead

class game:
	"Basic game logic and state machine"
	def __init__(self, name="nukes"):
		self.__name = name
		self.__state = GAME_STATE_INIT
		self.__popcards = {5 : 100,
				10 : 50,
				15 : 25,
				25 : 10,
				50 : 5}
		self.__cards = []
		self.__players = {}
		self.__turn = []
		self.cur = None
		self.__corpses = {}

		print "Game init: %s"%self.__name

	def __str__(self):
		return "game(%s)"%self.__name
	def __str__(self):
		return "game(%s)"%self.__name

	# [ Override these methods to do useful things
	def demilitarize(self):
		raise Exception("NotReached")
	def pass_control(self, p, retaliation=False):
		raise Exception("NotReached")
	def player_dead(self, p):
		p.hand.extend(p.card_stack)
		if self.cur == p:
			self.next_turn()
	def player_msg(self, player, msg):
		print " >> %s: %s"%(player, msg)
	def game_msg(self, msg):
		print " >> %s: %s"%(self, msg)
	# ]

	def get_player(self, name):
		if self.__players.has_key(name):
			return self.__players[name]
		if self.__corpses.has_key(name):
			return self.__corpses[name]
		raise GameLogicError(self, "No such player: %s"%name)
	
	def rename_player(self, p, new_name):
		if self.__players.has_key(new_name) or \
			self.__corpses.has_key(new_name):
			raise GameLogicError(self,
				"Already a player %s"%new_name)

		self.__players[new_name] = p
		if self.__players.has_key(p.name):
			del self.__players[p.name]
		if self.__corpses.has_key(p.name):
			del self.__corpses[p.name]
		p.name = new_name

	def kill_player(self, p):
		if self.__corpses.has_key(p.name):
			return

		self.__corpses[p.name] = p
		del self.__players[p.name]
		if self.__turn.count(p):
			self.__turn.remove(p)
		p.population = 0
		self.player_dead(p)

	def state(self):
		"Return the game state"
		return self.__state

	def transition(self, state):
		"Transition between war and peace"

		assert state == GAME_STATE_PEACE or \
			state == GAME_STATE_WAR
		if self.__state == state:
			return
		self.__state = state
		if self.__state == GAME_STATE_WAR:
			self.game_msg("%s: WAR DECLARED"%self.__name)
		else:
			self.game_msg("%s: PEACE"%self.__name)
			for p in self.__players.values():
				p.hand.extend(p.card_stack)
				p.card_stack = []
			self.demilitarize()
			# FIXME: players can change queue now

	def __get_pop(self):
		"Return a random population card"

		if len(self.__popcards) == 0:
			return 0

		x = random.randint(0, len(self.__popcards) - 1)
		k = self.__popcards.keys()[x]
		self.__popcards[k] = self.__popcards[k] - 1
		if self.__popcards[k] == 0:
			del self.__popcards[k]

		return k

	def __randyield(self):
		i = random.randint(0, 100)
		if i < 5:
			return NUKE_YIELD_100MT
		elif i < 20:
			return NUKE_YIELD_50MT
		elif i < 50:
			return NUKE_YIELD_20MT
		else:
			return NUKE_YIELD_10MT

	def deal_card(self):
		"Pick up a card from the top of the deck"

		r = random.randint(1, 100)

		# FIXME: use probability distributions
		if r < 25:
			return propaganda(random.randint(1, 10) * 5)
		elif r < 50:
			return warhead(self.__randyield())
		elif r < 75:
			return bomber(self.__randyield())
		else:
			return missile(self.__randyield())

	def add_player(self, p):
		"Add a player to the game and deal the initial cards"

		assert p.population == 0
		assert len(p.hand) == 0
		assert len(p.card_stack) == 0

		if self.__state != GAME_STATE_INIT:
			raise GameLogicError(self, "Game already started")
		if self.__players.has_key(p.name):
			raise GameLogicError(self, "Duplicate player name")

		# Deal population cards
		for i in range(0, 5):
			p.population += self.__get_pop()

		if p.name == 'jesus':
			p.population -= 27
		for i in range(0,9):
			p.hand.append(self.deal_card())

		print "%s: %s: pop. %uM"%(self, p, p.population)
		self.__players[p.name] = p
		p.game = self

	def commence(self):
		"Prepare the game for the first turn"

		if self.__state != GAME_STATE_INIT:
			raise GameLogicError(self, "Game already started")
		if len(self.__players) < 2:
			raise GameLogicError(self, "Lonely without players")
		for p in self.__players.values():
			if len(p.card_stack) < CARD_STACK_LEN:
				raise GameLogicError(self,
					"Cards not queued", player=p)
		self.__state = GAME_STATE_PEACE
		self.game_msg("Game started")
		self.next_turn()


	def next_turn(self):
		"Play a single turn of the game"

		if self.__state == GAME_STATE_OVER or \
			self.__state == GAME_STATE_INIT:
			raise GameLogicError(self, "Game not in progress")

		if self.cur and self.__corpses.has_key(self.cur.name):
			del self.__corpses[self.cur.name]

		while len(self.__corpses):
			self.cur = self.__corpses.values()[0]

			# Do retaliation if we die in war time
			if self.__state == GAME_STATE_WAR and \
				len(self.__players):
				self.pass_control(self.cur, retaliate=True)
				return
			else:
				del self.__corpses[self.cur.name]

		if len(self.__players) == 0:
			raise GameOverMan(self)
		elif len(self.__players) == 1:
			raise GameOverMan(self,
				self.__players.values()[0])

		# After retaliations return to peace
		if self.cur != None and self.cur.population == 0:
			self.transition(GAME_STATE_PEACE)

		# Re-start turn sequence
		if len(self.__turn) == 0:
			self.__turn = self.__players.values()

		# Figure out who's turn it is
		self.cur = self.__turn.pop(0)
		self.pass_control(self.cur)
