# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# warhead base class

import random
from card import card
from globals import *

class warhead(card):
	def __init__(self, megatons=NUKE_YIELD_10MT):
		self.__bodycounts = {NUKE_YIELD_10MT : 2,
					NUKE_YIELD_20MT : 5,
					NUKE_YIELD_50MT : 15,
					NUKE_YIELD_100MT : 25}
		if not self.__bodycounts.has_key(megatons):
			raise Exception("BadNukeYield")
		self.megatons = megatons

	def __str__(self):
		return "warhead(%uM)"%(self.megatons)
	
	def __repr__(self):
		return "warhead(%u)"%(self.megatons)

	def is_weapon(self):
		return True

	def calc_fallout(self, tgt):
		b = self.__bodycounts[self.megatons]
		r = random.randint(0, 16)
		g = tgt.game
		if r < 3:
			g.game_msg(" > Dirty bomb, double yield")
			b = b * 2
		elif r < 5:
			g.game_msg(" > Neutron bomb, double yield")
			b = b *2
			# FIXME: take cards from dead enemy...
		elif r < 7:
			g.game_msg(" > Gamma rays, +10M dead")
			b = b + 10
		elif r < 8:
			g.game_msg(" > Fireball, +1M dead")
			b = b + 1
		elif r < 9:
			g.game_msg(" > Beta particles, +5M dead")
			b = b + 5
		elif r < 10:
			g.game_msg(" > Fallout, +2M dead")
			b = b + 2
		elif r < 11:
			g.game_msg(" > Hit nuclear stockpile, triple yield")
			b = b * 3
			if self.megatons == NUKE_YIELD_100MT:
				raise GameOverMan(tgt.game)
		elif r < 12:
			g.game_msg(" > Hit nuclear power plant, double yield")
			b = b * 2
			# FIXME: if not dead, enemy misses turn

		g.game_msg(" > %s: %uM of your citizens die, boo hoo"%(
				tgt.name, b))
		tgt.pwn(b)

		return b

	def dequeue(self, g, p, tgt = None):
		if tgt == None:
			raise IllegalMoveError(g, p, "Must target warhead")

		# Make sure theres a delivery mech
		if p.weapon == None:
			g.game_msg(" > %s dumps %uM warhead"%(
					p.name, self.megatons))
			return

		p.weapon.use_warhead(self, g, p, tgt)
		card.dequeue(self, g, p, tgt)
