# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Card base class

from globals import *

class card:
	def is_warhead(self):
		return False

	def is_weapon(self):
		return False

	def use_warhead(self, warhead, g, p, tgt):
		raise IllegalMoveError(g, p, "%s not a weapon"%self)

	def dequeue(self, g, p, tgt = None):
		"Dequeue a card from the deck, optionally aiming " \
		"it at a target player"

		#if tgt != None:
		#	if tgt.population == 0:
		#		g.kill_player(tgt)
		#if p.population == 0:
		#	g.kill_player(p)
		return
