#!/usr/bin/python

import nukes,irclib,random,time,os
from ircnukes import ircnukes
import pickle, gzip, os
import socket

nick = '[skynet]'
name = 'ircnuk0rs'
#svr = ('irc.quakenet.eu.org', 6667)
svr = ('irc.b0rk.co.uk', 6667)
chan = '#nukes'
logdir = './saved-games'
#deck = './decks/original.deck'
deck = './decks/andrew.looney.deck'
game = None
okhash = None
log = None
irc = irclib.IRC()

class TokenBucket:
	from time import sleep, time

	def __init__(self, rate, burst = None):
		'Rate in tokens per second, burst in number of tokens'

		self.rate = float(rate)
		if burst is None:
			burst = self.rate
		self.rate = 1 / self.rate
		self.burst = float(burst) * self.rate
		self.toks = self.burst
		self.last = self.now()
	
	def now(self):
		return self.time()

	def rate_limit(self, tokens = 1.0):
		tokens = float(tokens)

		if self.rate <= 0:
			return

		h = self.now()
		diff = h - self.last
		self.toks += diff
		self.last = h

		if self.toks > self.burst:
			self.toks = self.burst

		if self.toks >= self.rate:
			self.toks -= self.rate

		if self.toks < self.rate:
			self.sleep((self.rate - self.toks))

tbf = TokenBucket(2.0, 5.0)
def privmsg(conn, tgt, msg):
	global tbf
	tbf.rate_limit()
	conn.privmsg(tgt, msg)

def log_line(str):
	global log
	if log == None:
		return
	log.write(str + "\n")
	log.flush()

def ok_char(c):
	"Return true if the character is allowed in a saved game name"

	global okhash
	if okhash == None:
		ok = ['-', '+', '_', '.', '&', '[', ']', '(', ')']
		ok.extend(map(chr, range(ord('0'), ord('9') + 1)))
		ok.extend(map(chr, range(ord('a'), ord('z') + 1)))
		okhash = {}.fromkeys(ok)
	return okhash.has_key(c)
	
def name2path(name):
	"Convert a game-name to a saved-game path"

	global logdir
	name.lower()
	str = filter(ok_char, name)
	if len(str) != len(name):
		return False
	return os.path.join(logdir, "%s.gz"%str)

def path2name(path):
	"Convert a saved-game path to a game-name"

	global logdir

	if len(path) < len(logdir):
		return False

	# first check it's in right dir
	path = path[len(logdir):]
	while path[0] == '/':
		path = path[1:]

	# check it ends with .gz
	if path[-3:] != '.gz':
		return False

	return path[:-3]

def list_games(conn, chan):
	"List all games"

	global logdir
	l = map(lambda x:path2name(os.path.join(logdir, x)),
		os.listdir(logdir))
	if len(l):
		s = ', '.join(l)
		privmsg(conn, chan, "Saved Games: %s"%s)
	else:
		privmsg(conn, chan, "No saved games")


def save_game(conn, chan, game, name):
	"Saves an ircnukes object to a file"

	global logdir

	l = len(map(lambda x:path2name(os.path.join(logdir, x)),
		os.listdir(logdir)))

	if l > 128:
		raise nukes.GameLogicError(game, "Hey, stop fucking around")

	# Calculate path
	path = name2path(name)
	if path == False or path2name(path) == False:
		privmsg(conn, chan, 'bad game-name, try [a-z0-9_-]')
		return

	# open the file and dump the game object, making sure to
	# remove anything that's unpicklable
	game.save_prepare()
	try:
		f = gzip.open(path, 'w')
		pickle.dump(game, f)
		f.close()
	except Exception, e:
		privmsg(conn, chan, "Writing to %s failed: %s"%(path, \
				(e.strerror == None) \
				and e.message or e.strerror))
		game.save_done(conn, chan)
		game.dirty = True
		return
	game.save_done(conn, chan)

	privmsg(conn, chan, "game '%s' saved to %s"%(path2name(path), path))

def load_game(conn, chan, name):
	"Loads an ircnukes object from a file and returns it"

	# Calculate path
	path = name2path(name)
	if path == False or path2name(path) == False:
		privmsg(conn, chan, 'bad game-name, try [a-z0-9_-]')
		return

	# open the file, load up the game object, and restore the stuff
	# we didn't pickle, such as irc conn object and channel name
	try:
		f = gzip.open(path, 'r')
		ret = pickle.load(f)
		f.close()
	except Exception, e:
		privmsg(conn, chan, "Reading from %s failed: %s"%(path, \
				(e.strerror == None) \
				and e.message or e.strerror))
		return
	ret.save_done(conn, chan)

	privmsg(conn, chan, "game '%s' loaded from %s"%(path2name(path), path))
	return ret

# cmd_XXX() handles each type of irc message once the relevant arguments
# have been stripped out by the lower level handlers
def cmd_priv(conn, nick, cmd):
	"Private message"

	global chan
	global game
	global log

	log_line("priv %s %s"%(nick, cmd))

	arg = cmd.split()
	if not len(arg):
		return

	if arg[0] == "help":
		def closure(tgt, msg):
			return
		tmp = ircnukes(closure, None)
		h = tmp.irc_list_pcmds()
		privmsg(conn, nick, "Commands: %s"%(' '.join(h)))
		return

	if game == None:
		#privmsg(conn, nick, "No game, join %s..."%chan)
		return

	try:
		p = game.get_player(nick)
		game.irc_pcmd(nick, arg[0], arg[1:])
	except nukes.GameOverMan, e:
		if e.winner == None:
			privmsg(conn, chan, "GameOver: MAD, noone wins")
		else:
			privmsg(conn, chan, "GameOver: winner is %s "
				"with %u million population"%(e.winner.name,
				e.winner.population))
		game = None
	except nukes.IllegalMoveError, e:
		privmsg(conn, nick, "%s: Illegal Move: %s"%(e.player, e.desc))
	except nukes.GameLogicError, e:
		if e.player is None:
			privmsg(conn, nick, "%s: Bad Command: %s"%(nick, e.desc))
		else:
			privmsg(conn, nick, "%s: %s"%(e.player, e.desc))
	return

def cmd_pub(conn, nick, chan, cmd, logit=True):
	"Channel message"

	global game
	global log
	global deck

	log_line("chan %s %s"%(nick, cmd))

	arg = cmd.split()
	if not len(arg):
		return

	if arg[0] == "create":
		def closure(tgt, msg):
			privmsg(conn, tgt, msg)
		try:
			game = ircnukes(closure, chan, deck)
		except nukes.GameLogicError, e:
			privmsg(conn, chan, "error: %s: %s"%(deck, e.desc))
			return
		privmsg(conn, chan, "Game created: %s"%game)
		if logit == True:
			randomseed = int(time.time())
			random.seed(randomseed)
			log = open("nukebot.log", "w")
			log_line("randomseed %u"%randomseed)
			log_line("chan %s create"%chan)
			log.flush()
		return
	elif arg[0] == "savegame":
		if game == None:
			privmsg(conn, chan, "No game to save")
		elif len(arg) < 2:
			privmsg(conn, chan, "games need names baby")
		else:
			save_game(conn, chan, game, arg[1])
		return
	elif arg[0] == "listgames":
		list_games(conn, chan)
		return
	elif arg[0] == "loadgame":
		if game != None and game.dirty:
			privmsg(conn, chan, "Game in progress, save it first")
		elif len(arg) < 2:
			privmsg(conn, chan, "!listgames to find one to load")
		else:
			game = load_game(conn, chan, arg[1])
		return
	elif arg[0] == "help":
		tmp = ircnukes(None, None)
		h = tmp.irc_list_cmds()
		h.extend(["creategame", "savegame", "loadgame", "listgames"])
		privmsg(conn, chan, "Commands: %s"%(' '.join(h)))
		return

	if game == None:
		privmsg(conn, chan, "No game, try !create")
		return

	try:
		game.irc_cmd(nick, arg[0], arg[1:])
	except nukes.GameOverMan, e:
		if e.winner == None:
			privmsg(conn, chan, "GameOver: MAD, noone wins")
		else:
			privmsg(conn, chan, "GameOver: winner is %s "
				"with %u million population"%(e.winner.name,
				e.winner.population))
		game = None
	except nukes.IllegalMoveError, e:
		privmsg(conn, chan, "%s: Illegal Move: %s"%(e.player, e.desc))
	except nukes.GameLogicError, e:
		if e.player is None:
			privmsg(conn, chan, "%s: %s"%(nick, e.desc))
		else:
			privmsg(conn, chan, "%s: %s"%(e.player, e.desc))
	return

def cmd_nick(conn, nick, new):
	"Nickname changed message"

	global game
	if game == None:
		return

	log_line("nick %s %s"%(nick, new))
	game.nick_change(nick, new)

def cmd_quit(conn, nick):
	"Quit message"

	global game
	if game == None:
		return

	log_line("quit %s"%nick)

	try:
		p = game.get_player(nick)
		p.kill(suicide = True)
	except nukes.GameLogicError, e:
		print "quit: %s"%e.desc
	except nukes.GameOverMan, e:
		print "quit: Game Over"
	return

def cmd_kick(conn, kicker, nick):
	"Kick message"

	global game
	if game == None:
		return
	log_line("kick %s %s"%(kicker, nick))

def cmd_part(conn, nick):
	"Part message"

	global game
	if game == None:
		return
	log_line("part %s"%nick)

def cmd_join(conn, nick):
	"Join message"

	global game
	if game == None:
		return
	log_line("join %s"%nick)

def get_nick(str):
	"Returns a nickname from an IRC nick!user@host"
	return irclib.irc_lower(str.split('!')[0])

# irc_msg_XXX() functions are irclib event handlers
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
		ev.target(), ev.arguments()[0][1:])

def irc_msg_action(conn, ev):
	print "[%s] * %s %s"%(ev.target(),
				get_nick(ev.source()),
				ev.arguments()[0])

def irc_msg_quit(conn, ev):
	print "%s quit (%s)"%(get_nick(ev.source()), ev.arguments()[0])
	cmd_quit(conn, get_nick(ev.source()))

def irc_msg_kick(conn, ev):
	print "%s kicks %s from %s (%s)"%(get_nick(ev.source()), \
				ev.target(), ev.arguments()[0], \
				ev.arguments()[1])
	cmd_kick(conn, get_nick(ev.source()), ev.arguments()[0])

def irc_msg_part(conn, ev):
	try:
		arg = ev.arguments()[0]
	except:
		arg = ''
	print "%s left %s (%s)"%(get_nick(ev.source()), \
				ev.target(), arg)
	cmd_part(conn, get_nick(ev.source()))

def irc_msg_nick(conn, ev):

	print "%s is now known as %s"%(get_nick(ev.source()), ev.target())
	cmd_nick(conn, get_nick(ev.source()), irclib.irc_lower(ev.target()))

def irc_msg_join(conn, ev):
	if get_nick(ev.source()) == conn.get_nickname():
		print "Joined: %s"%ev.target()
		privmsg(conn, ev.target(), "Would you like to play a game?")
		return
	print "%s joined %s"%(get_nick(ev.source()), chan)
	cmd_join(conn, get_nick(ev.source()))

def irc_msg_umode(conn, ev):
	print "Connected: joining %s"%chan
	conn.join(chan)

def irc_disconnect(conn, ev):
	print "Disconnected: (%s) Reconnecting in 15..."%ev.arguments()[0]
	time.sleep(15)
	s = irc.server()
	s.connect(svr[0], svr[1], nick, ircname=name, username=name)
	s.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)

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
	s.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)

	try:
		irc.process_forever()
	except KeyboardInterrupt:
		s.quit("Mutually Assured Destruction")
