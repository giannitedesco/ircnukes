#!/usr/bin/python

from sys import stdin
import random
import nukes
from ircnukes import ircnukes
from nukebot import cmd_pub, cmd_priv

class fake_conn:
        def privmsg(self, to, msg):
                print ">>> <%s> %s"%(to, msg)
        def quit(self, msg):
                print ">>> QUIT (%s)"%msg

conn = fake_conn()
game = None
chan = "#nuke-test"

def barf(arg):
	print arg
	raise SystemExit

def testbed():
	try:
		while True:
			str = stdin.readline()[:-1]
			if str == '':
				break
			arr = str.split(' ', 2)
			if len(arr) < 2:
				barf("Bad line: %s"%arr)

			if arr[0] == "randomseed":
				print "Seed is %u"%int(arr[1])
				random.seed(int(arr[1]))
				continue

			if len(arr) < 3:
				barf("Bad line: %s"%arr)

			print "<<< %s"%str

			if arr[0] == "chan":
				cmd_pub(conn, arr[1], chan, arr[2], logit=False)
			elif arr[0] == "priv":
				cmd_priv(conn, arr[1], arr[2])
			else:
				barf("Bad cmd: %s"%arr)
	except KeyboardInterrupt:
		return

if __name__ == "__main__":
	testbed()
