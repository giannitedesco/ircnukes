#!/usr/bin/python

from sys import stdin
import random
import nukes
from ircnukes import ircnukes
from nukebot import cmd_pub, cmd_priv, cmd_nick, cmd_quit, cmd_kick, cmd_part

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

			print "<<< %s"%str

			if arr[0] == "chan":
				if len(arr) < 3:
					barf("Bad line: %s"%arr)
				cmd_pub(conn, arr[1], chan, arr[2], logit=False)
			elif arr[0] == "priv":
				if len(arr) < 3:
					barf("Bad line: %s"%arr)
				cmd_priv(conn, arr[1], arr[2])
			elif arr[0] == "nick":
				if len(arr) < 3:
					barf("Bad line: %s"%arr)
				cmd_nick(conn, arr[1], arr[2])
			elif arr[0] == "quit":
				cmd_quit(conn, arr[1])
			elif arr[0] == "kick":
				if len(arr) < 3:
					barf("Bad line: %s"%arr)
				cmd_kick(conn, arr[1], arr[2])
			elif arr[0] == "part":
				cmd_part(conn, arr[1])
			elif arr[0] == "join":
				cmd_part(conn, arr[1])
			else:
				barf("Bad cmd: %s"%arr)
	except KeyboardInterrupt:
		return

if __name__ == "__main__":
	testbed()
