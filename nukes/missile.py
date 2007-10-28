# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Missile base class

from card import card
from globals import *

class missile(card):
	def __init__(self, max_payload=10):
		self.max_payload = max_payload
		self.__name  = "missile"

	def __str__(self):
		return "missile(%u)"%(self.max_payload)
	
	def __repr__(self):
		return "missile(%u)"%self.max_payload

	def is_weapon(self):
		return True

	def use_warhead(self, warhead, g, p, tgt):
		# Check weapon yield
		if warhead.megatons > self.max_payload:
			p.weapon = None
			g.game_msg(" > %s wastes %uM warhead and %uM missile"%(
				p.name, warhead.megatons, self.max_payload))
			return

		# Weapon firing commences, this is war
		g.transition(GAME_STATE_WAR)

		g.game_msg(" > %s fires %u megaton missile at %s"%(p.name,
				warhead.megatons, tgt.name))

		# Do the damage
		deaths = warhead.calc_fallout(tgt)
		p.weapon = None

	def dequeue(self, g, p, tgt = None):
		p.weapon = self
		g.game_msg(" > %s deploys missile %s"%(p.name, self))
		card.dequeue(self, g, p, tgt)
