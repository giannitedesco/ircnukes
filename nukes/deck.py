# Copyright (c) 2007 Gianni Tedesco
# Released under the terms of the GNU GPL v2 or later
#
# Simulate a never-ending deck of cards. We do this by emulating a
# single deck. When all cards have been dealt, we simply replenish
# the deck with the original set of cards. It generates cards as they
# are dealt using the system PRNG for shuffling.

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

	def __do_args(self, item):
		try:
			return int(item)
		except:
			return item

	def load_file(self, f, clsmap):
		while True:
			ln = f.readline()
			if ln == '':
				break
			ln = ln[:-1]
			if ln == '':
				continue
			if ln[0] == '#':
				continue
			ln = ln.split()
			if len(ln) < 2:
				raise Exception("Bad line: %s"%ln)
			maxcnt = int(ln[0])
			if not clsmap.has_key(ln[1]):
				raise Exception("No such card: %s"%ln[1])
			cls = clsmap[ln[1]]
			args = map(self.__do_args, ln[2:])
			self.add_card(maxcnt, cls, args)
