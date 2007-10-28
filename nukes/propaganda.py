# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Propaganda cards 

from card import card
from globals import *

class propaganda(card):
	def __init__(self, pop=5):
		self.__pop = pop

	def __str__(self):
		return "propaganda(%uM)"%self.__pop
	
	def __repr__(self):
		return "propaganda(%u)"%self.__pop

	def dequeue(self, g, p, tgt = None):
		if g.state() != GAME_STATE_PEACE:
			g.game_msg(" > %s dumps propaganda"%p.name)
			return
		if tgt == None:
			raise IllegalMoveError(g, p, "Target required")
		p.weapon = None
		g.game_msg(" > %s uses propaganda on %s (%uM)"%(
				p.name, tgt.name, self.__pop))
		p.transfer_population(min(self.__pop, tgt.population))
		tgt.pwn(self.__pop)
		card.dequeue(self, g, p, tgt)
