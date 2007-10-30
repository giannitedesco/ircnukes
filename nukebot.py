#!/usr/bin/python

import nukes,irclib,random,time,os
from ircnukes import ircnukes

nick = '[skynet]'
name = 'ircnukes'
svr = ('irc.quakenet.eu.org', 6667)
chan = '#nukes'
game = None
log = None
irc = irclib.IRC()

def cmd_priv(conn, nick, cmd):
	global chan
	global game
	global log

	if log != None:
		log.write("priv %s %s\n"%(nick, cmd))
		log.flush()

	arg = cmd.split()
	if not len(arg):
		return

	if arg[0] == "help":
		tmp = ircnukes(None, None)
		h = tmp.irc_list_pcmds()
		conn.privmsg(nick, "Commands: %s"%(' '.join(h)))
		return

	if game == None:
		conn.privmsg(nick, "No game, join %s..."%chan)
		return

	try:
		p = game.get_player(nick)
		game.irc_pcmd(nick, arg[0], arg[1:])
	except nukes.GameOverMan, e:
		if e.winner == None:
			conn.privmsg(chan, "GameOver: MAD, noone wins")
		else:
			conn.privmsg(chan, "GameOver: winner is %s "
				"with %u million population"%(e.winner.name,
				e.winner.population))
		game = None
	except nukes.IllegalMoveError, e:
		conn.privmsg(nick, "%s: Illegal Move: %s"%(e.player, e.desc))
	except nukes.GameLogicError, e:
		if e.player == None:
			conn.privmsg(nick, "%s: Bad Command: %s"%(nick, e.desc))
		else:
			conn.privmsg(nick, "%s: %s"%(e.player, e.desc))
	return

def cmd_pub(conn, nick, chan, cmd, logit=True):
	global game
	global log

	if log != None:
		log.write("chan %s %s\n"%(nick, cmd))
		log.flush()

	arg = cmd.split()
	if not len(arg):
		return

	if arg[0] == "creategame":
		game = ircnukes(conn, chan)
		conn.privmsg(chan, "Game started: %s"%game)
		if logit == True:
			randomseed = int(time.time())
			random.seed(randomseed)
			log = open("nukebot.log", "w")
			log.write("randomseed %u\n"%randomseed)
			log.write("chan %s creategame\n"%chan)
			log.flush()
		return
	elif arg[0] == "help":
		tmp = ircnukes(None, None)
		h = tmp.irc_list_cmds()
		h.append("creategame")
		conn.privmsg(chan, "Commands: %s"%(' '.join(h)))
		return

	if game == None:
		conn.privmsg(chan, "No game, try !creategame")
		return

	try:
		game.irc_cmd(nick, arg[0], arg[1:])
	except nukes.GameOverMan, e:
		if e.winner == None:
			conn.privmsg(chan, "GameOver: MAD, noone wins")
		else:
			conn.privmsg(chan, "GameOver: winner is %s "
				"with %u million population"%(e.winner.name,
				e.winner.population))
		game = None
	except nukes.IllegalMoveError, e:
		conn.privmsg(chan, "%s: Illegal Move: %s"%(e.player, e.desc))
	except nukes.GameLogicError, e:
		if e.player == None:
			conn.privmsg(chan, "%s: Bad Command: %s"%(nick, e.desc))
		else:
			conn.privmsg(chan, "%s: %s"%(e.player, e.desc))
	return

def get_nick(str):
	return str.split('!')[0]

def irc_msg_priv(conn, ev):
	print "[priv] <%s> %s"%(get_nick(ev.source()),
				ev.arguments()[0])
	cmd_priv(conn, get_nick(ev.source()), ev.arguments()[0])

def irc_msg_pub(conn, ev):
	print "[%s] <%s> %s"%(ev.target(),
				get_nick(ev.source()),
				ev.arguments()[0])
	if ev.arguments()[0][0] != '!':
		return
	cmd_pub(conn, get_nick(ev.source()),
		ev.target(), ev.arguments()[0][1:], logit=True)

def irc_msg_action(conn, ev):
	print "[%s] * %s %s"%(ev.target(),
				get_nick(ev.source()),
				ev.arguments()[0])

def irc_msg_nick(conn, ev):
	global game
	print "%s is now known as %s"%(get_nick(ev.source()), ev.target())
	try:
		game.rename_player(game.get_player(get_nick(ev.source())),
					ev.target())
	except nukes.GameLogicError:
		return

def get_gamelist(limit):
	list = os.listdir(".")
	list = filter((lambda x: os.path.isfile(x) and x[:8] == 'nukebot-' and x[-4:] == '.log'), list)
	list.sort()
	return list[:limit]

def irc_msg_umode(conn, ev):
	print "Connected: joinging %s"%chan
	conn.join(chan)

def irc_msg_join(conn, ev):
	if get_nick(ev.source()) != conn.get_nickname():
		return
	conn.privmsg(ev.target(), "Would you like to play a game?")

def irc_disconnect(conn, ev):
	print "Disconnected: (%s) Reconnecting in 15..."%ev.arguments()[0]
	time.sleep(15)
	s = irc.server()
	s.connect(svr[0], svr[1], nick, ircname=name, username=name)

if __name__ == "__main__":
	#irclib.DEBUG = True
	irc.add_global_handler('umode', irc_msg_umode)
	irc.add_global_handler('join', irc_msg_join)
	irc.add_global_handler('privmsg', irc_msg_priv)
	irc.add_global_handler('pubmsg', irc_msg_pub)
	irc.add_global_handler('action', irc_msg_action)
	irc.add_global_handler('nick', irc_msg_nick)
	irc.add_global_handler('disconnect', irc_disconnect)


	s = irc.server()
	s.connect(svr[0], svr[1], nick, ircname=name, username=name)

	try:
		irc.process_forever()
	except KeyboardInterrupt:
		s.quit("Mutually Assured Destruction")
		del s
