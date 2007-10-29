# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Missile base class

from card import card
from globals import *

class bomber(card):
	def __init__(self, max_payload=10, name="bomber"):
		self.max_payload = max_payload
		self.payload = max_payload
		self.__name = name

	def __str__(self):
		if self.__name == "bomber":
			return "bomber(%u)"%self.max_payload
		else:
			return self.__name
	
	def __repr__(self):
		return "%s(%u/%u)"%(self.__name, self.payload, self.max_payload)

	def is_weapon(self):
		return True

	def use_warhead(self, warhead, g, p, tgt):
		# Check weapon yield
		if self.payload < warhead.megatons:
			p.weapon = None
			g.game_msg(" > %s wastes %uM warhead on %uM bomber"%(
					p.name, warhead.megatons, self.payload))
			return

		self.payload = self.payload - warhead.megatons

		# Weapon firing commences, this is war
		g.transition(GAME_STATE_WAR)

		g.game_msg(" > bomber: %s fires %u megaton warhead at %s"%(
				p.name, warhead.megatons, tgt.name))

		# Do the damage
		deaths = warhead.calc_fallout(tgt)

		if self.payload <= 0:
			p.weapon = None

	def dequeue(self, g, p, tgt = None):
		p.weapon = self
		g.game_msg(" > %s deploys bomber %s"%(p.name, self))
		card.dequeue(self, g, p, tgt)
