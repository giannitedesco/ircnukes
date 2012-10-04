import nukes
from irclib import irc_lower

class ircnukes(nukes.game):
	def save_prepare(self):
		"Prepare to save the object by removing any references"
		"to non-picklable objects"

		self.__nc = None
		self.__cmd = None
		self.__pcmd = None
		self.__privmsg = None
		self.__chan = None
		self.dirty = False

	def save_done(self, conn, chan):
		"Prepare a freshly loaded/saved game for use by re-adding"
		"references to non-picklable objects and also un-dirty the"
		"game."

		self.__nc = {"join" : self.__joingame,
				"status" : self.__status}
		self.__cmd = {"start" : self.__startgame,
				"suicide" : self.__suicide,
				"flip" : self.__flip,
				"use" : self.__use,
				"done" : self.__done}
		self.__pcmd = {"hand" : self.__get_hand,
				"queue" : self.__get_queue,
				"population" : self.__get_pop,
				"push" : self.__push_card}
		self.__pcmd_alias = {"h" : "hand",
					"p" : "push",
					"q" : "queue",
					"pop" : "population"}
		self.__privmsg = conn
		self.__chan = chan
		self.dirty = False

	def __init__(self, conn, chan, deck=None):
		self.save_done(conn, chan)
		nukes.game.__init__(self, chan, deck)

	def pass_control(self, p):
		assert p.state != nukes.PLAYER_STATE_DEAD
		if p.state == nukes.PLAYER_STATE_ALIVE:
			self.game_msg("%s it's your go!"%p.name)
			return
		self.game_msg("%s, it's time for final retaliation!"%p.name)
		self.game_msg("%s has: %s"%(p.name, p.hand))

	def deal_in_player(self, p):
		nukes.game.deal_in_player(self, p)
		self.__get_pop(p)
		self.__get_hand(p)
		self.__get_queue(p)
		self.dirty = True

	def nick_change(self, old, new):
		if old == new:
			return
		try:
			p = self.get_player(old)
			self.rename_player(p, new)
			self.dirty = True
		except nukes.GameLogicError, e:
			self.game_msg("Error renaming %s to %s: %s"%(old,\
					new, e.desc))

	def add_player(self, p):
		nukes.game.add_player(self, p)

	def war(self):
		self.game_msg("\x02\x034,99WAR DECLARED!\x02\x03")

	def demilitarize(self):
		self.game_msg("\x02\x033,99Peace time\x02\x03, re-create your queues!")

	def player_dead(self, p):
		if self.state() == nukes.GAME_STATE_INIT:
			self.game_msg(
				"%s was deterred and ran home crying"%p.name)
		elif self.state() == nukes.GAME_STATE_WAR:
			self.game_msg("%s reduced to rubble.. loser"%p.name)
		else:
			self.game_msg("%s died from a peace offensive"%p.name)
		nukes.game.player_dead(self, p)

	def player_msg(self, p, msg):
		self.__privmsg(p.name, msg)

	def game_msg(self, msg):
		self.__privmsg(self.__chan, msg)

	def get_player(self, name):
		return nukes.game.get_player(self, irc_lower(name))

	# Private commands
	def __get_pop(self, p, cmd='', arg=[]):
		"View your population"

		self.player_msg(p, "Population %uM"%p.population)

	def __get_hand(self, p, cmd='', arg=[]):
		"View the cards in your hand"

		self.player_msg(p, "Hand: %s"%p.hand)

	def __get_queue(self, p, cmd='', arg=[]):
		"View the contents of your card queue"

		if len(p.card_stack) == 0:
			self.player_msg(p, "Queue: <empty>")
			return
		self.player_msg(p, "Queue: %s"%p.card_stack)

	def __push_card(self, p, cmd='', arg=[]):
		"Push a card in to your queue, eg. push 0 / push warhead(10)"
		if len(arg) < 1:
			return
		c = p.queue_card(arg[0])
		self.__get_queue(p)
		self.dirty = True

	# Channel commands
	def __startgame(self, p, cmd='', arg=[]):
		"Start a new game in the current channel"
		self.commence()
		self.dirty = True

	def __suicide(self, p, cmd='', arg=[]):
		"Leave a game at any time"
		p.kill(suicide = True)
		self.dirty = True

	def __joingame(self, nick, cmd='', args=[]):
		"Join a game that has been created with savegame"

		p = nukes.player(nick)
		self.add_player(p)
		self.game_msg("%s joins the game"%p)
		self.dirty = True

	def __flip(self, p, cmd='', arg=[]):
		"Flip the first card in your queue when it's your turn"

		if len(arg) >= 1:
			tgt = self.get_player(arg[0])
		else:
			tgt = None

		p.flip_card(tgt)

		p.hand.append(self.deal_card())
		self.__get_hand(p)
		self.next_turn()
		self.dirty = True

	def __use(self, p, cmd='', arg=[]):
		"Flip any card in your hand during final retaliation"
		if len(arg) < 1:
			raise nukes.IllegalMoveError(self, p, "No card specified")
		if len(arg) >= 2:
			tgt = self.get_player(arg[1])
		else:
			tgt = None
		p.use_card(arg[0], tgt)
		self.dirty = True
	
	def __done(self, p, cmd='', arg=[]):
		"Finish your retaliation"
		if p != self.cur:
			raise nukes.IllegalMoveError(self, p,
						"Not your turn")

		self.next_turn()
		self.dirty = True

	def __status(self, nick, cmd='', arg=[]):
		"View game or player status"

		str = {nukes.PLAYER_STATE_ALIVE:"alive",
			nukes.PLAYER_STATE_RETALIATE:"retaliating",
			nukes.PLAYER_STATE_DEAD:"dead"}

		if self.state() == nukes.GAME_STATE_PEACE:
			self.game_msg("\x02\x033,99Peace time\x03:\x02")
		elif self.state() == nukes.GAME_STATE_WAR:
			self.game_msg("\x02\x034,99War time\x03:\x02")
		else:
			self.game_msg("Game status:")

		if len(arg) >= 1:
			arr = map(self.get_player, arg)
		else:
			arr = self.get_players()
		for x in arr:
			self.game_msg(" > %s: %s%s%s"%(x.name, str[x.state],
				x.weapon != None and ": %r"%x.weapon or "",
				self.cur == x and " (*)" or ""))
		return

	def irc_cmd(self, nick, cmd, args):
		"Channel commands"
		cmd.lower()

		if self.__nc.has_key(cmd):
			self.__nc[cmd](nick, cmd, args)
			return

		p = self.get_player(nick)

		if self.__cmd.has_key(cmd):
			self.__cmd[cmd](p, cmd, args)
			return

		self.game_msg("%s: command '%s' not known"%(nick, cmd))

	def irc_pcmd(self, nick, cmd, args):
		"Private message commands"

		p = self.get_player(nick)

		cmd = self.__pcmd_alias.get(cmd, cmd)

		if self.__pcmd.has_key(cmd):
			self.__pcmd[cmd](p, cmd, args)
			return

		self.__privmsg(nick,
				"%s: command '%s' not known"%(nick, cmd))

	def irc_list_cmds(self):
		"List channel commands"

		ret = self.__nc.keys()
		ret.extend(self.__cmd.keys())
		return ret

	def irc_list_pcmds(self):
		"List private message commands"
		return self.__pcmd.keys()
