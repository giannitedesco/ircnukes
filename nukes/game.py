# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later

import random
from globals import *
from propaganda import propaganda
from missile import missile
from bomber import bomber
from warhead import warhead
from deck import deck

class game:
	"Basic game logic and state machine"
	def __init__(self, name="nukes"):
		self.__name = name
		self.__state = GAME_STATE_INIT
		self.__popcards = deck("population")
		self.__deck = deck("main")
		self.__players = {}
		self.__turn = []
		self.cur = None

		# Population the population cards...heh
		self.__popcards.add_card(100, int, [5])
		self.__popcards.add_card(50, int, [10])
		self.__popcards.add_card(25, int, [15])
		self.__popcards.add_card(10, int, [25])
		self.__popcards.add_card(5, int, [50])

		# Now for the main deck...
		self.__deck.add_card(1, warhead, [NUKE_YIELD_100MT])
		self.__deck.add_card(4, warhead, [NUKE_YIELD_50MT])
		self.__deck.add_card(10, warhead, [NUKE_YIELD_20MT])
		self.__deck.add_card(19, warhead, [NUKE_YIELD_10MT])
		self.__deck.add_card(3, missile, [NUKE_YIELD_100MT, "saturn"])
		self.__deck.add_card(9, missile, [NUKE_YIELD_20MT, "atlas"])
		self.__deck.add_card(9, missile, [NUKE_YIELD_10MT, "polaris"])
		self.__deck.add_card(6, bomber, [NUKE_YIELD_50MT, "b70"])
		self.__deck.add_card(2, propaganda, [20])
		self.__deck.add_card(6, propaganda, [10])
		self.__deck.add_card(12, propaganda, [5])

		# Don't print anything if it's an unnamed game...
		if self.__name != None:
			print "Game init: %s (%u cards in deck)"%(self.__name,
				len(self.__deck))

	def __str__(self):
		return "game(%s)"%self.__name
	def __repr__(self):
		return "game(%s)"%self.__name

	# [ Override these methods to do useful things
	def demilitarize(self):
		raise Exception("NotReached")
	def pass_control(self, p):
		raise Exception("NotReached")
	def player_dead(self, p):
		p.cards_to_hand()
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
		raise GameLogicError(self, "No such player: %s"%name)
	
	def rename_player(self, p, new_name):
		if self.__players.has_key(new_name):
			raise GameLogicError(self,
				"Already a player %s"%new_name)

		self.__players[new_name] = p
		del self.__players[p.name]
		p.name = new_name

	def kill_player(self, p, delete=False):
		if p.state != PLAYER_STATE_ALIVE:
			return
		if self.__state == GAME_STATE_INIT:
			p.state = PLAYER_STATE_DEAD
			if self.__players.has_key(p.name):
				del self.__players[p.name]
			self.player_dead(p)
			return

		if self.__turn.count(p):
			self.__turn.remove(p)

		if self.__state == GAME_STATE_WAR and delete == False:
			p.state = PLAYER_STATE_RETALIATE
		else:
			p.state = PLAYER_STATE_DEAD
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
			for p in self.__alive():
				p.cards_to_hand()
			self.demilitarize()
			# FIXME: players can change queue now

	def __get_pop(self):
		"Return a random population card"
		return self.__popcards.deal_card()

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
		return self.__deck.deal_card()

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
	
	def apocalypse(self):
		for p in self.__players.values():
			p.state = PLAYER_STATE_DEAD
		raise GameOverMan(self)

	def __retaliate(self):
		arr = filter(lambda x:x.state == PLAYER_STATE_RETALIATE,
				self.__players.values())
		return arr

	def __alive(self):
		arr = filter(lambda x:x.state == PLAYER_STATE_ALIVE,
				self.__players.values())
		return arr

	def get_players(self):
		return self.__players.values()

	def next_turn(self):
		"Play a single turn of the game"

		if self.__state == GAME_STATE_OVER or \
			self.__state == GAME_STATE_INIT:
			raise GameLogicError(self, "Game not in progress")

		if self.cur and self.cur.state == PLAYER_STATE_RETALIATE:
			self.cur.state = PLAYER_STATE_DEAD

		# Handle outstanding retaliations
		while len(self.__retaliate()):
			self.cur = self.__retaliate()[0]

			if len(self.__alive()):
				self.pass_control(self.cur)
				return
			else:
				self.cur.state = PLAYER_STATE_DEAD
				break

		# Check for game over conditions
		if len(self.__alive()) == 0:
			raise GameOverMan(self)
		elif len(self.__alive()) == 1:
			raise GameOverMan(self,
				self.__alive()[0])

		# After retaliations return to peace
		if self.cur != None and self.cur.state == PLAYER_STATE_DEAD:
			self.transition(GAME_STATE_PEACE)

		while True:
			# Re-start turn sequence
			if len(self.__turn) == 0:
				self.__turn = self.__alive()

			# Figure out who's turn it is
			self.cur = self.__turn.pop(0)
			if self.cur.missturns:
				self.cur.missturns = self.cur.missturns - 1
				self.game_msg("%s: Miss a turn"%self.cur.name)
				continue
			self.pass_control(self.cur)
			break
