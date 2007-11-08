import nukes

class ircnukes(nukes.game):
	def save_prepare(self):
		self.__nc = None
		self.__cmd = None
		self.__pcmd = None
		self.__conn = None
		self.__chan = None
		self.dirty = False

	def save_done(self, conn, chan):
		self.__nc = {"joingame" : self.__joingame,
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
		self.__conn = conn
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

	def nick_change(self, old, new):
		try:
			p = self.get_player(old)
			self.rename_player(p, new)
			self.dirty = True
		except GameLogicError, e:
			self.game_msg("Error renaming %s to %s: %s"%(old,\
					new, e.desc))

	def add_player(self, p):
		nukes.game.add_player(self, p)

	def demilitarize(self):
		self.game_msg("Peace time, re-create your queues!")
	
	def player_dead(self, p):
		if self.state() == nukes.GAME_STATE_INIT:
			self.game_msg(
				"%s was deterred and ran home crying"%p.name)
			return
		if self.state() == nukes.GAME_STATE_WAR:
			self.game_msg("%s reduced to rubble.. loser"%p.name)
		else:
			self.game_msg("%s died from a peace offensive"%p.name)
		nukes.game.player_dead(self, p)

	def player_msg(self, p, msg):
		self.__conn.privmsg(p.name, msg)
	
	def game_msg(self, msg):
		self.__conn.privmsg(self.__chan, msg)

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
		self.kill_player(p)
		self.dirty = True

	def __joingame(self, nick, cmd='', args=[]):
		"Join a game that has been created with savegame"

		p = nukes.player(nick)
		self.add_player(p)
		self.game_msg("%s joins the game"%p)
		self.__get_pop(p)
		self.__get_hand(p)
		self.__get_queue(p)
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
			raise IllegalMoveError(self, p, "No card specified")
		if len(arg) >= 2:
			tgt = self.get_player(arg[1])
		else:
			tgt = None
		p.use_card(arg[0], tgt)
		self.dirty = True
	
	def __done(self, p, cmd='', arg=[]):
		"Finish your retaliation"
		self.next_turn()
		self.dirty = True

	def __status(self, nick, cmd='', arg=[]):
		str = {nukes.PLAYER_STATE_ALIVE:"alive",
			nukes.PLAYER_STATE_RETALIATE:"retaliating",
			nukes.PLAYER_STATE_DEAD:"dead"}

		if self.state() == nukes.GAME_STATE_PEACE:
			self.game_msg("Peace time:")
		elif self.state() == nukes.GAME_STATE_WAR:
			self.game_msg("War time:")
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
		p = self.get_player(nick)

		if self.__pcmd.has_key(cmd):
			self.__pcmd[cmd](p, cmd, args)
			return

		self.__conn.privmsg(nick,
				"%s: command '%s' not known"%(nick, cmd))

	def irc_list_cmds(self):
		ret = self.__nc.keys()
		ret.extend(self.__cmd.keys())
		return ret

	def irc_list_pcmds(self):
		return self.__pcmd.keys()
