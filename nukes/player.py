# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Player class

from globals import *

class player:
	def __init__(self, name):
		self.name = name
		self.hand = []
		self.population = 0
		self.card_stack = []
		self.weapon = None
		self.game = None
		return
	
	def __str__(self):
		return "player(%s)"%self.name

	def __repr__(self):
		return "player('%s')"%self.name

	def flip_card(self, tgt):
		if self.game.cur != self:
			raise IllegalMoveError(self.game, self,
						"Not your turn")
		if len(self.card_stack) != CARD_STACK_LEN:
			raise IllegalMoveError(self.game, self,
						"Cards not queued")
		if self.population == 0:
			raise IllegalMoveError(self.game, self,
						"It's final retaliation time!")
		c = self.card_stack.pop(0)
		try:
			c.dequeue(self.game, self, tgt)
		except:
			self.card_stack.insert(0, c)
			raise

	def use_card(self, arg, tgt):
		if self.game.cur != self:
			raise IllegalMoveError(self.game, self,
						"Not your turn")
		if self.population != 0:
			raise IllegalMoveError(self.game, self,
					"It's not final retaliation yet!")

		try:
			c = self.__card_by_idx(int(arg))
		except ValueError:
			c = self.__card_by_name(arg)

		c.dequeue(self.game, self, tgt)

	def pwn(self, pwnage):
		"Decrement population"
		if pwnage >= self.population:
			self.population = 0
			self.game.kill_player(self)
			return
		self.population = self.population - pwnage

	def transfer_population(self, converts):
		"Add population"

		if self.population != 0:
			self.population += converts

	def __card_by_idx(self, idx):
		if idx < 0 or idx >= len(self.hand):
			raise IllegalMoveError(self.game, self,
						"Bad Card Index: %d"%idx)
		assert len(self.card_stack) <= CARD_STACK_LEN
		return self.hand.pop(idx)
	
	def __card_by_name(self, name):
		strl = map(lambda x:x.__str__().lower(), self.hand)
		repl = map(lambda x:x.__repr__().lower(), self.hand)
		for i in range(0, len(self.hand)):
			if repl[i] != name.lower() and strl[i] != name.lower():
				continue
			return self.hand.pop(i)
		raise IllegalMoveError(self.game, self,
					"Card %s not found"%name)

	def queue_card(self, arg):
		"Push a card in to the queue"

		if len(self.card_stack) == CARD_STACK_LEN:
			raise IllegalMoveError(self.game, self, "Queue Full")

		try:
			c = self.__card_by_idx(int(arg))
		except ValueError:
			c = self.__card_by_name(arg)

		self.card_stack.append(c)
		if len(self.card_stack) == CARD_STACK_LEN and \
			self.game.state() == GAME_STATE_INIT:
			self.game.game_msg("%s is ready"%self.name)
		return c
