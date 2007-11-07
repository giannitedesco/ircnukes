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

def log_line(str):
	global log
	if log == None:
		return
	log.write(str + "\n")
	log.flush()

def cmd_priv(conn, nick, cmd):
	global chan
	global game
	global log

	log_line("priv %s %s"%(nick, cmd))

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

	log_line("chan %s %s"%(nick, cmd))

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
			log_line("randomseed %u"%randomseed)
			log_line("chan %s creategame"%chan)
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

def cmd_nick(conn, nick, new):
	global game
	if game == None:
		return

	log_line("nick %s %s"%(nick, new))

	try:
		game.rename_player(game.get_player(nick), new)
	except nukes.GameLogicError, e:
		print e.desc
		return

def cmd_quit(conn, nick):
	global game
	if game == None:
		return

	log_line("quit %s"%nick)

	try:
		p = game.get_player(nick)
	except nukes.GameLogicError, e:
		print e.desc
		return

	game.kill_player(p, delete=True)

def cmd_kick(conn, kicker, nick):
	global game
	if game == None:
		return
	log_line("kick %s %s"%(kicker, nick))

def cmd_part(conn, nick):
	if game == None:
		return
	log_line("part %s"%nick)

def cmd_join(conn, nick):
	log_line("join %s"%nick)

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

def irc_msg_quit(conn, ev):
	print "%s quit (%s)"%(get_nick(ev.source()), ev.arguments()[0])
	cmd_quit(conn, get_nick(ev.source()))

def irc_msg_kick(conn, ev):
	print "kick: %s %s %s"%(get_nick(ev.source()), \
				ev.target(), ev.arguments()[0])
	cmd_kick(conn, get_nick(ev.source()), ev.target())

def irc_msg_part(conn, ev):
	print "%s left %s (%s)"%(get_nick(ev.source()), \
				ev.target(), ev.arguments()[0])
	cmd_part(conn, get_nick(ev.source()))

def irc_msg_nick(conn, ev):

	print "%s is now known as %s"%(get_nick(ev.source()), ev.target())

def irc_msg_join(conn, ev):
	if get_nick(ev.source()) != conn.get_nickname():
		cmd_join(conn, get_nick(ev.source()))
	conn.privmsg(ev.target(), "Would you like to play a game?")

def irc_msg_umode(conn, ev):
	print "Connected: joinging %s"%chan
	conn.join(chan)

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
	irc.add_global_handler('quit', irc_msg_quit);
	irc.add_global_handler('kick', irc_msg_kick);
	irc.add_global_handler('part', irc_msg_part);
	irc.add_global_handler('disconnect', irc_disconnect)


	s = irc.server()
	s.connect(svr[0], svr[1], nick, ircname=name, username=name)

	try:
		irc.process_forever()
	except KeyboardInterrupt:
		s.quit("Mutually Assured Destruction")
		del s
