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
		self.state = PLAYER_STATE_ALIVE
		self.missturns = 0
		return
	
	def __str__(self):
		return "player(%s)"%self.name

	def __repr__(self):
		return "player('%s')"%self.name

	def __card_by_idx(self, idx):
		"Return a card from the hand by index"

		if idx < 0 or idx >= len(self.hand):
			raise IllegalMoveError(self.game, self,
						"Bad Card Index: %d"%idx)
		assert len(self.card_stack) <= CARD_STACK_LEN
		return self.hand.pop(idx)
	
	def __card_by_name(self, name):
		"Return a card from the hand by name"

		strl = map(lambda x:x.__str__().lower(), self.hand)
		repl = map(lambda x:x.__repr__().lower(), self.hand)
		for i in range(0, len(self.hand)):
			if repl[i] != name.lower() and strl[i] != name.lower():
				continue
			return self.hand.pop(i)
		raise IllegalMoveError(self.game, self,
					"Card %s not found"%name)

	def kill(self, suicide=False):
		if self.state == PLAYER_STATE_DEAD:
			return
		if self.game == None:
			return

		if suicide == False and self.game.state() == GAME_STATE_WAR:
			self.state = PLAYER_STATE_RETALIATE
		else:
			self.state = PLAYER_STATE_DEAD
		self.cards_to_hand()
		self.game.player_dead(self)

	def cards_to_hand(self):
		"Move all cards back in to the hand"

		self.hand.extend(self.card_stack)
		self.card_stack = []
		if self.weapon != None:
			self.hand.append(self.weapon)
			self.weapon = None

	def flip_card(self, tgt):
		"Flip card to take a turn in the game"

		if self.state != PLAYER_STATE_ALIVE:
			raise IllegalMoveError(self.game, self,
						"You're not alive!")
		if self.game.cur != self:
			raise IllegalMoveError(self.game, self,
						"Not your turn")
		if len(self.card_stack) != CARD_STACK_LEN:
			raise IllegalMoveError(self.game, self,
						"Cards not queued")
		c = self.card_stack.pop(0)
		try:
			c.dequeue(self.game, self, tgt)
		except:
			self.card_stack.insert(0, c)
			raise

	def use_card(self, arg, tgt):
		"Use card for final retaliation"

		if self.game.cur != self:
			raise IllegalMoveError(self.game, self,
						"Not your turn")
		if self.state != PLAYER_STATE_RETALIATE:
			raise IllegalMoveError(self.game, self,
					"It's not final retaliation!")

		try:
			c = self.__card_by_idx(int(arg))
		except ValueError:
			c = self.__card_by_name(arg)

		try:
			c.dequeue(self.game, self, tgt)
		except:
			self.hand.append(c)
			raise

	def queue_card(self, arg):
		"Push a card in to the queue"

		if len(self.card_stack) == CARD_STACK_LEN:
			raise IllegalMoveError(self.game, self, "Queue Full")
		if self.state != PLAYER_STATE_ALIVE:
			raise IllegalMoveError(self.game, self,
						"Cannot queue cards when dead")

		try:
			c = self.__card_by_idx(int(arg))
		except ValueError:
			c = self.__card_by_name(arg)

		self.card_stack.append(c)
		if len(self.card_stack) == CARD_STACK_LEN and \
			self.game.state() == GAME_STATE_INIT:
			self.game.game_msg("%s is ready"%self.name)
		return c

	def pwn(self, pwnage):
		"Decrement population"

		i = min(self.population, pwnage)
		self.population = self.population - i
		if self.population == 0:
			self.kill()

	def transfer_population(self, converts, tgt):
		"Transfer population to another player"

		if self.state != PLAYER_STATE_ALIVE:
			raise IllegalMoveError(self.game, self,
				"Cannot transfer population from dead enemy")
		i = min(self.population, converts)
		self.population = self.population - i
		tgt.population = tgt.population + i
		if self.population == 0:
			self.kill()
