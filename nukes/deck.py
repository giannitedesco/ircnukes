# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Card base class

from globals import *
from random import randint

class deck_card:
	def __init__(self, max, cls, args):
		self.cnt = max
		self.max = max
		self.cls = cls
		self.args = args

class deck:
	def __init__(self, name):
		self.__name = name
		self.__cards = []

	def __str__(self):
		return "deck(%s,%u)"%(self.__name, len(self))

	def __repr__(self):
		return "deck(%s)"%self.__name

	def __replenish(self):
		for x in self.__cards:
			x.cnt = x.max

	def __len__(self):
		return sum(map(lambda x:x.cnt, self.__cards))

	def deal_card(self):
		if len(self.__cards) == 0:
			return None

		ds = len(self)
		if ds == 0:
			self.__replenish()
			ds = len(self)

		r = randint(0, ds - 1)
		i = 0
		for c in self.__cards:
			i = i + c.cnt
			if r < i:
				c.cnt = c.cnt - 1
				ret = c.cls(*c.args)
				return ret

	def add_card(self, maxcnt, cls, args):
		self.__cards.append(deck_card(maxcnt, cls, args))
