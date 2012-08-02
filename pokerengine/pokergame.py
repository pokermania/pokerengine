#
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2008 Bradley M. Kuhn <bkuhn@ebb.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep
#
# Mekensleep
# 26 rue des rosiers
# 75004 Paris
# licensing@mekensleep.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#  Loic Dachary <loic@dachary.org>
#  Bradley M. Kuhn <bkuhn@ebb.org>
#  Henry Precheur <henry@precheur.org> (2004)
#

import sys
import re
import struct
import random
import platform

import pokereval

from pokerengine import log as engine_log
log = engine_log.getChild('pokergame')

from pokerengine.pokercards import *
from pokerengine.pokerengineconfig import Config
from pokerengine.pokerchips import PokerChips
from pokerengine import pokerrake

import locale
import gettext

from pprint import pformat

from copy import deepcopy
from collections import defaultdict

gettext.bind_textdomain_codeset('poker-engine', 'UTF-8')


def init_i18n(locale_dir, overrideTranslationFunction=None):

    global _

    # If we've been fed the function that we know will work to translate
    # text, then we just set _() to that.  This is to support the scenario
    # where users of this library want to provide their own setup for
    # gettext() (i.e., to switch languages on the fly, as
    # pokernetwork.pokeravatar does).

    # Note that we return the _() that is being replaced.  This is done so
    # that the function can be restored by the caller, should it chose to do
    # so.

    # First, if our _() has never been defined, we simply set it to None
    try:
        oldTranslationFunction = _
    except NameError:
        oldTranslationFunction = None

    if callable(overrideTranslationFunction):
        _ = overrideTranslationFunction
        return oldTranslationFunction

    lang = ''

    if platform.system() == "Windows":
        lang = locale.getdefaultlocale()[0][:2]
        if locale_dir is None:
            locale_dir = './../../locale'

    try:
        t = gettext.translation('poker-engine', localedir=locale_dir, languages=[lang])
        _ = t.gettext
    except IOError:
        _ = lambda text: text
        return oldTranslationFunction

init_i18n(None)

ABSOLUTE_MAX_PLAYERS = 10

LEVELS_CACHE = {}


def uniq(elements):
    temp = {}
    for element in elements:
        temp[element] = None
    return temp.keys()

def find(fn,seq):
    """Return first item in sequence where f(item) == True."""
    for item in seq:
        if fn(item): return item

class PokerRandom(random.Random):
    def __init__(self, paranoid=False):
        self._file = None
        self._paranoid = paranoid
        self.seed(None)

    def seed(self, ignore):
        if self._file:
            try:
                self._file.close()
            except:
                pass
        self._file = open('/dev/urandom', 'r')

    def getstate(self):
        return None

    def setstate(self, ignore):
        pass

    def jumpahead(self, ignore):
        pass

    def random(self):
        lsize = struct.calcsize('l')
        return abs(struct.unpack('l', self._file.read(lsize))[0]) / (0. + (~(1L << ((8 * lsize) - 1))))

if platform.system() == "Linux":
    random._inst = PokerRandom()

shuffler = random

# muck constants
AUTO_MUCK_NEVER = 0x00
AUTO_MUCK_WIN = 0x01
AUTO_MUCK_LOSE = 0x02
AUTO_MUCK_ALWAYS = AUTO_MUCK_WIN + AUTO_MUCK_LOSE

# auto play constants
AUTO_PLAY_YES = 0x01
AUTO_PLAY_NO = 0x00


AUTO_PLAYER_POLICY_BOT = 'bot'
AUTO_PLAYER_POLICY_SIMPLE_BOT = 'simple_bot'
AUTO_PLAYER_POLICY_FOLD = 'fold'

DEFAULT_AUTOPLAYER_POLICY = AUTO_PLAYER_POLICY_SIMPLE_BOT

class PokerPlayer:
    def __init__(self, serial, name, game):
        self.log = log.getChild(self.__class__.__name__, refs=[
            ('Game', game, lambda game: game.id),
            ('Hand', game, lambda game: game.hand_serial if game.hand_serial > 1 else None),
            ('Player', self, lambda player: player.serial)
        ])
        self.serial = serial
        self.name = name if name else "noname"
        self.game = game
        self.fold = False
        self.remove_next_turn = False
        self.sit_out = True
        self.sit_out_next_turn = False
        self.sit_requested = False
        self.bot = False
        self.auto = False
        self.auto_blind_ante = False
        self.auto_muck = AUTO_MUCK_ALWAYS  # AUTO_MUCK_NEVER, AUTO_MUCK_WIN, AUTO_MUCK_LOSE, AUTO_MUCK_ALWAYS
        self.auto_play = AUTO_PLAY_YES
        self.auto_player_policy = DEFAULT_AUTOPLAYER_POLICY
        self.auto_player_fold_next_turn = False
        self.wait_for = False  # True, False, "late", "big", "first_round" ##
        self.missed_blind = "n/a"  # None, "n/a", "big", "small"
        self.missed_big_blind_count = 0
        self.blind = "late"  # True, False, "late", "big", "small", "big_and_dead"
        self.buy_in_payed = False
        self.ante = False
        self.side_pot_index = 0
        self.all_in = False
        self.seat = -1
        self.hand = PokerCards()
        self.money = 0
        self.rebuy = 0
        self.bet = 0
        self.dead = 0
        self.talked_once = False
        self.user_data = None

    def copy(self):
        other = PokerPlayer(self.serial, self.name, self.game)
        other.fold = self.fold
        other.remove_next_turn = self.remove_next_turn
        other.sit_out = self.sit_out
        other.sit_out_next_turn = self.sit_out_next_turn
        other.sit_requested = self.sit_requested
        other.bot = self.bot
        other.auto = self.auto
        other.auto_blind_ante = self.auto_blind_ante
        other.auto_muck = self.auto_muck
        other.auto_player_policy = self.auto_player_policy
        other.auto_player_fold_next_turn = self.auto_player_fold_next_turn
        other.wait_for = self.wait_for
        other.missed_blind = self.missed_blind
        other.missed_big_blind_count = self.missed_big_blind_count
        other.blind = self.blind
        other.buy_in_payed = self.buy_in_payed
        other.ante = self.ante
        other.side_pot_index = self.side_pot_index
        other.all_in = self.all_in
        other.seat = self.seat
        other.hand = self.hand.copy()
        other.money = self.money
        other.rebuy = self.rebuy
        other.bet = self.bet
        other.dead = self.dead
        other.talked_once = self.talked_once
        other.user_data = self.user_data
        return other

    def __str__(self):
        return (
            "serial = %d, name = %s, fold = %s, "
            "remove_next_turn = %s, "
            "sit_out = %s, "
            "sit_out_next_turn = %s, "
            "sit_requested = %s, "
            "bot = %s, auto = %s, "
            "auto_blind_ante = %s, "
            "wait_for = %s, "
            "auto_muck = %d, "
            "auto_player_policy = %s, "
            "auto_player_fold_next_turn = %s, "
            "missed_blind = %s, "
            "missed_big_blind_count = %d, "
            "blind = %s, "
            "buy_in_payed = %s, "
            "ante = %s, "
            "all_in = %s, "
            "side_pot_index = %d, "
            "seat = %d, "
            "hand = %s, "
            "money = %d, "
            "rebuy = %d, "
            "bet = %d, "
            "dead = %d, "
            "talked_once = %s, "
            "user_data = %s"
        ) % (
            self.serial,
            self.name,
            self.fold,
            self.remove_next_turn,
            self.sit_out,
            self.sit_out_next_turn,
            self.sit_requested,
            self.bot,
            self.auto,
            self.auto_blind_ante,
            self.wait_for,
            self.auto_muck,
            self.auto_player_policy,
            self.auto_player_fold_next_turn,
            self.missed_blind,
            self.missed_big_blind_count,
            self.blind,
            self.buy_in_payed,
            self.ante,
            self.all_in,
            self.side_pot_index,
            self.seat, self.hand,
            self.money,
            self.rebuy,
            self.bet,
            self.dead,
            self.talked_once,
            self.user_data
        )

    def setUserData(self, user_data):
        self.user_data = user_data

    def getUserData(self):
        return self.user_data

    def beginTurn(self):
        self.bet = 0
        self.dead = 0
        self.fold = False
        self.hand = PokerCards()
        self.side_pot_index = 0
        self.all_in = False
        self.blind = False
        self.ante = False

    def isInGame(self):
        return not self.isAllIn() and not self.isFold()

    def isAllIn(self):
        return self.all_in

    def isFold(self):
        return self.fold

    def isNotFold(self):
        return not self.fold

    def isConnected(self):
        return not self.remove_next_turn

    def isDisconnected(self):
        return self.remove_next_turn

    def isSitOut(self):
        return self.sit_out

    def isSit(self):
        return not self.sit_out

    def isSitRequested(self):
        return self.sit_requested

    def isBot(self):
        return self.bot

    def isAuto(self):
        return self.auto

    def isAutoBlindAnte(self):
        return self.auto_blind_ante

    def isWaitForBlind(self):
        return self.wait_for

    def isMissedBlind(self):
        return self.missed_blind and self.missed_blind != "n/a"

    def isBlind(self):
        return self.blind

    def isBuyInPayed(self):
        return self.buy_in_payed

    def getMissedRoundCount(self):
        return self.missed_big_blind_count

    def resetMissedBlinds(self):
        self.missed_blind = None
        self.missed_big_blind_count = 0


def __historyResolve2messages(game, hands, serial2name, serial2displayed, frame):
    messages = []
    best = {
        'hi': 0,
        'low': 0x0FFFFFFF
    }
    for serial in frame['serials']:
        for side in ('hi', 'low'):
            if serial not in hands:
                continue
            hand = hands[serial]
            if side not in hand:
                continue
            if hand[side][1][0] == 'Nothing':
                continue

            hand = hand[side]
            show = False
            if ((side == 'hi' and best['hi'] <= hand[0]) or
                 (side == 'low' and best['low'] >= hand[0])):
                best[side] = hand[0]
                show = True

            if serial in serial2displayed and not serial in frame[side]:
                #
                # If the player already exposed the hand and is not going
                # to win this side of the pot, there is no need to issue
                # a message.
                #
                continue
            if show:
                serial2displayed[serial] = True
                value = game.readableHandValueLong(side, hand[1][0], hand[1][1:])
                messages.append(_("%(name)s shows %(value)s for %(side)s ") % {
                    'name': serial2name(serial),
                    'value': value,
                    'side': _(side)
                })
            else:
                messages.append(_("%(name)s mucks loosing hand") % {
                    'name': serial2name(serial)
                })

    for side in ('hi', 'low'):
        if side not in frame:
            continue
        message = ' '.join(serial2name(serial) for serial in frame[side])
        if len(frame[side]) > 1:
            message += _(" tie for %(side)s ") % {'side': _(side)}
        else:
            message += _(" wins %(side)s ") % {'side': _(side)}
        messages.append(message)

    if len(frame['serial2share']) > 1:
        if 'chips_left' in frame:
            messages.append(
                _("winners share a pot of %(pot)s") % {'pot': PokerChips.tostring(frame['pot'])} +
                _(" (minus %(chips_left)d odd chips)") % {'chips_left': frame['chips_left']}
            )
        else:
            messages.append(_("winners share a pot of %(pot)s") % {'pot': PokerChips.tostring(frame['pot'])})

    for (serial, share) in frame['serial2share'].iteritems():
        messages.append(_("%(name)s receives %(amount)s") % {
            'name': serial2name(serial),
            'amount': PokerChips.tostring(share)
        })

    return messages


def history2messages(game, history, serial2name=str, pocket_messages=False):
    messages = []
    subject = ''
    for event in history:
        event_type = event[0]
        if event_type == "game":
            level, hand_serial, hands_count, time, variant, betting_structure, player_list, dealer, serial2chips = event[1:]
            subject = _("hand #%(hand_serial)d, %(variant)s, %(betting_structure)s") % {
                'hand_serial': hand_serial,
                'variant': _(variant),
                'betting_structure': betting_structure
            }

        elif event_type == "wait_for":
            serial, reason = event[1:]
            messages.append(
                _("%(serial)s waiting for ") % {'serial': serial2name(serial)} +
                ("late blind" if reason == "late" else "big blind")
            )

        elif event_type == "player_list":
            pass

        elif event_type == "round":
            name, board, pockets = event[1:]
            if pockets:
                messages.append(_("%(name)s, %(len_pockets)d players") % {
                    'name': name,
                    'len_pockets': len(pockets)
                })
            else:
                messages.append(name)
            if board and not board.isEmpty():
                messages.append(_("Board: %(board)s") % {
                    'board': game.cards2string(board)
                })
            if pockets and pocket_messages:
                for (serial, pocket) in pockets.iteritems():
                    if not pocket.areAllNocard():
                        messages.append(_("Cards player %(name)s: %(card)s") % {
                            'name': serial2name(serial),
                            'card': game.cards2string(pocket)
                        })
        elif event_type == "showdown":
            board, pockets = event[1:]
            if board and not board.isEmpty():
                messages.append(_("Board: %(cards)s") % {
                    'cards': game.cards2string(board)
                })
            if pockets and pocket_messages:
                for (serial, pocket) in pockets.iteritems():
                    if not pocket.areAllNocard():
                        messages.append(_("Cards player %(name)s: %(cards)s") % {
                            'name': serial2name(serial),
                            'cards': game.cards2string(pocket)
                        })
        elif event_type == "rake":
            amount = event[1]
            messages.append(_("Rake %(amount)s") % {
                'amount': PokerChips.tostring(amount)
            })
        elif event_type == "position":
            pass
        elif event_type == "blind_request":
            pass
        elif event_type == "wait_blind":
            pass
        elif event_type == "rebuy":
            pass
        elif event_type == "blind":
            serial, amount, dead = event[1:]
            if dead:
                messages.append(_("%(name)s pays %(amount)s blind and %(dead)d dead") % {
                    'name': serial2name(serial),
                    'amount': PokerChips.tostring(amount),
                    'dead': dead,
                })
            else:
                messages.append(_("%(name)s pays %(amount)s blind") % {
                    'name': serial2name(serial),
                    'amount': PokerChips.tostring(amount),
                })
        elif event_type == "ante_request":
            pass
        elif event_type == "ante":
            serial, amount = event[1:]
            messages.append(_("%(name)s pays %(amount)s ante") % {
                'name': serial2name(serial),
                'amount': PokerChips.tostring(amount)
            })
        elif event_type == "all-in":
            serial = event[1]
            messages.append(_("%(name)s is all in") % {'name': serial2name(serial)})
        elif event_type == "call":
            serial, amount = event[1:]
            messages.append(_("%(name)s calls %(amount)s") % {
                'name': serial2name(serial),
                'amount': PokerChips.tostring(amount)
            })
        elif event_type == "check":
            serial = event[1]
            messages.append(_("%(name)s checks") % {'name': serial2name(serial)})
        elif event_type == "fold":
            serial = event[1]
            messages.append(_("%(name)s folds") % {'name': serial2name(serial)})
        elif event_type == "raise":
            serial, amount = event[1:]
            messages.append(_("%(name)s raises %(amount)s") % {
                'name': serial2name(serial),
                'amount': PokerChips.tostring(amount)
            })
        elif event_type == "canceled":
            serial, amount = event[1:]
            if serial > 0 and amount > 0:
                messages.append(_("turn canceled") + _(" (%(amount)s returned to %(name)s)") % {
                    'amount': PokerChips.tostring(amount),
                    'name': serial2name(serial)
                })
            else:
                messages.append(_("turn canceled"))
        elif event_type == "end":
            winners, showdown_stack = event[1:]
            if showdown_stack:
                game_state = showdown_stack[0]
                if 'serial2best' not in game_state:
                    serial = winners[0]
                    messages.append(_("%(name)s receives %(amount)s (everyone else folded)") % {
                        'name': serial2name(serial),
                        'amount': PokerChips.tostring(game_state['serial2share'][serial])
                    })
                else:
                    serial2displayed = {}
                    hands = showdown_stack[0]['serial2best']
                    for frame in showdown_stack[1:]:
                        message = None
                        if frame['type'] == 'left_over':
                            message = _("%(name)s receives %(amount)d odd chips") % {
                                'name': serial2name(frame['serial']),
                                'amount': frame['chips_left']
                            }
                        elif frame['type'] == 'uncalled':
                            message = _("returning uncalled bet %(amount)s to %(name)s") % {
                                'amount': PokerChips.tostring(frame['uncalled']),
                                'name': serial2name(frame['serial'])
                            }
                        elif frame['type'] == 'resolve':
                            messages.extend(__historyResolve2messages(game, hands, serial2name, serial2displayed, frame))
                        else:
                            engine_log.warn("history2messages unexpected showdown_stack frame type %s (%s)", frame['type'], str(frame))
                        if message:
                            messages.append(message)
            else:
                engine_log.warn("ERROR history2messages ignored empty showdown_stack")
        elif event_type == "sitOut":
            serial = event[1]
            messages.append(_("%(name)s sits out") % {'name': serial2name(serial)})
        elif event_type == "leave":
            pass
        elif event_type == "finish":
            pass
        elif event_type == "muck":
            pass
        elif event_type == "sit":
            pass
        elif event_type == "AutoPlayPolicy":
            pass
        else:
            engine_log.warn("history2messages: unknown history type %s", event_type)

    return (subject, messages)


# poker game states
GAME_STATE_NULL = "null"
GAME_STATE_BLIND_ANTE = "blindAnte"
GAME_STATE_PRE_FLOP = "pre-flop"
GAME_STATE_FLOP = "flop"
GAME_STATE_THIRD = "third"
GAME_STATE_TURN = "turn"
GAME_STATE_FOURTH = "fourth"
GAME_STATE_RIVER = "river"
GAME_STATE_FIFTH = "fifth"
GAME_STATE_MUCK = "muck"
GAME_STATE_END = "end"

# winning helper states
WON_NULL = -1  # turn not ended yet
WON_ALLIN_BLIND = 0  # turn ended on allin in blind phase
WON_ALLIN = 1  # turn ended on allin
WON_FOLD = 2  # turn ended on fold
WON_REGULAR = 3  # turn ended normally


class PokerGame:
    def __init__(self, url, is_directing, dirs):
        self.log = log.getChild(self.__class__.__name__, refs=[
            ('Game', self, lambda game: game.id),
            ('Hand', self, lambda game: game.hand_serial if game.hand_serial > 1 else None)
        ])
        self.id = 0
        self.name = "noname"
        self.__variant = Config(dirs)
        self.__betting_structure = Config(dirs)
        self.dirs = dirs
        self.url = url

        self.variant = False
        self.variant_name = "unknown"
        self.round_info = False
        self.round_info_backup = False
        self.win_orders = False

        self.betting_structure = False
        self.betting_structure_name = "unknown"
        self.blind_info = False
        self.ante_info = False
        self.bet_info = False
        self.unit = 1
        self.buy_in = 0
        self.max_buy_in = 100000000

        self.max_players = ABSOLUTE_MAX_PLAYERS
        self.is_open = True

        self.hand_serial = 1
        self.time = -1
        self.time_of_first_hand = -1
        self.hands_count = 0
        self.stats = {
            "flops": [],
            "flops_count": 20,
            "percent_flop": 0,
            "pots": [],
            "pots_count": 20,
            "average_pot": 0,
            "hands_per_hour": 0,
            "time": -1,
            "hands_count": 0,
            "frequency": 180  # seconds
            }

        self.is_directing = is_directing

        self.prefix = ""
        self.callbacks = []

        self.first_turn = True

        self.level_skin = ""

        self.eval = pokereval.PokerEval()
        if self.is_directing:
            self.shuffler = shuffler
        self.reset()
        self.rake = None
        self.raked_amount = 0
        self.forced_dealer_seat = -1

    
    def reset(self):
        self.state = GAME_STATE_NULL
        self.win_condition = WON_NULL
        self.current_round = -2
        self.serial2player = {}
        self.player_list = []
        self.resetSeatsLeft()
        self.dealer = -1
        self.dealer_seat = -1
        self.position = 0
        self.last_to_talk = -1
        self.raked_amount = 0
        self.pot = False
        self.board = PokerCards()
        self.round_cap_left = sys.maxint
        self.last_bet = 0
        self.uncalled = 0
        self.uncalled_serial = 0
        self.winners = []
        self.muckable_serials = []
        self.side2winners = {}
        self.serial2best = {}
        self.showdown_stack = []
        self.side_pots = {}
        self.first_betting_pass = True
        self.turn_history = []
        self.turn_history_is_reduced = False
        self.level = 0

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def setMaxPlayers(self, max_players):
        self.max_players = max_players
        if (self.max_players < 2) or (self.max_players > ABSOLUTE_MAX_PLAYERS):
            self.log.warn("The number of players must be between %d and %d", 2, ABSOLUTE_MAX_PLAYERS)
            self.max_players = 0
        self.resetSeatsLeft()
        self.serial2player = {}

    def seatsLeftCount(self):
        return len(self.seats_left)

    def resetSeatsLeft(self):
        if self.max_players == 2:
            self.seats_left = [2, 7]
        elif self.max_players == 3:
            self.seats_left = [2, 7, 5]
        elif self.max_players == 4:
            self.seats_left = [1, 6, 3, 8]
        elif self.max_players == 5:
            self.seats_left = [0, 2, 4, 6, 8]
        elif self.max_players == 6:
            self.seats_left = [0, 2, 4, 5, 7, 8]
        elif self.max_players == 7:
            self.seats_left = [0, 2, 3, 4, 5, 6, 8]
        elif self.max_players == 8:
            self.seats_left = [1, 2, 3, 4, 5, 6, 7, 8]
        elif self.max_players == 9:
            self.seats_left = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        elif self.max_players == 10:
            self.seats_left = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        else:
            self.seats_left = []

        self.seats_all = self.seats_left[:]

    def seatsCount(self):
        return len(self.seats_all)

    def canComeBack(self, serial):
        return \
            serial in self.serial2player and (
                self.serial2player[serial].isDisconnected() or
                self.serial2player[serial].isAuto()
            )

    def canAddPlayer(self, serial):
        if len(self.seats_left) < 1:
            self.log.warn("no seats left for player %d", serial)
            return False
        else:
            return self.is_open

    def isInPosition(self, serial):
        return self.isPlaying(serial) and self.getSerialInPosition() == serial

    def isInTurn(self, serial):
        return \
            not self.isEndOrNull() and \
            serial in self.serial2player and \
            serial in self.player_list

    def isPlaying(self, serial):
        return \
            self.isRunning() and \
            serial in self.serial2player and \
            serial in self.player_list

    def isInGame(self, serial):
        return \
            self.isRunning() and \
            serial in self.serial2player and \
            serial in self.serialsInGame()

    def isSeated(self, serial):
        return serial in self.serial2player

    def isSit(self, serial):
        return \
            serial in self.serial2player and \
            self.serial2player[serial].isSit()

    def isSitOut(self, serial):
        return \
            serial in self.serial2player and \
            self.serial2player[serial].isSitOut()

    def autoPlayerFoldNextTurn(self, serial):
        player = self.serial2player[serial]
        if not player.auto_player_fold_next_turn:
            player.auto_player_fold_next_turn = True

        return True

    def sitOutNextTurn(self, serial):
        player = self.serial2player[serial]
        if self.isInTurn(serial) and not (self.isBlindAnteRound() and self.getSerialInPosition() == serial):
            player.sit_out_next_turn = True
            player.sit_requested = False
            return False
        elif not self.is_directing:
            player.sit_out_next_turn = True
            player.sit_requested = False
            player.wait_for = False
            return False
        else:
            return self.sitOut(serial)

    def sitOut(self, serial):
        player = self.serial2player[serial]
        if player.isSitOut():
            return False
        if self.is_directing and self.isBlindAnteRound() and self.getSerialInPosition() != serial:
            self.log.inform("sitOut for player %d while paying the blinds although not in position", serial)
            return False
        if self.isPlaying(serial):
            self.historyAdd("sitOut", serial)
        player.sit_out = True
        player.sit_out_next_turn = False
        player.sit_requested = False
        player.wait_for = False
        if self.is_directing and self.isBlindAnteRound():
            player.blind = False
            self.updateBlinds()
            if self.getSerialInPosition() == serial:
                self.__talkedBlindAnte()
            # the else is impossible because checked above
        return True

    def sit(self, serial):
        player = self.serial2player[serial]
        
        if player.isSit() and not player.sit_out_next_turn and not player.isAuto():
            self.log.inform("sit: refuse to sit player %d because is already seated.", serial)
            return False
        
        if not player.isBuyInPayed() or self.isBroke(serial):
            self.log.inform(
                "sit: refuse to sit player %d because buy in == %s " \
                "instead of True or broke == %s instead of False",
                serial,
                player.buy_in_payed,
                self.isBroke(serial)
            )
            return False
        player.sit_requested = False
        player.sit_out = False
        if player.wait_for == "big":
            player.wait_for = False
        #
        # Rationale of player.sit_out_next_turn == False
        # This condition happens when the player sitout + sit
        # while not having the position during the blind/ante round it.
        # In this particular case, instead of instructing her to wait
        # for the first round, she sits back. This is important because
        # she was included in the player list at the begining of the turn.
        # If she is marked wait_for = "first_round", she will be removed
        # from the player list at the end of the blind/ante round, which
        # is exactly the opposite of what we want.
        #
        if self.isRunning() and self.isBlindAnteRound() and player.sit_out_next_turn == False:
            player.wait_for = "first_round"
        player.sit_out_next_turn = False
        player.auto = False
        if self.sitCount() < 2:
            self.first_turn = True
            self.dealer_seat = player.seat
        if self.isRunning() and self.isBlindAnteRound():
            self.historyAdd("sit", serial, player.wait_for)
        player.auto_player_fold_next_turn = False
        if player.auto_player_policy != DEFAULT_AUTOPLAYER_POLICY:
            player.auto_player_policy = DEFAULT_AUTOPLAYER_POLICY
            self.historyAdd("autoPlayerPolicy", serial, DEFAULT_AUTOPLAYER_POLICY)
        return True

    def sitRequested(self, serial):
        player = self.getPlayer(serial)
        if player:
            player.sit_out_next_turn = False
            player.sit_requested = True
            player.wait_for = False

    def canceled(self, serial, amount):
        if self.isBlindAnteRound():
            self.acceptPlayersWaitingForFirstRound()
            self.cancelState()
            if self.sitCount() != 1:
                self.log.inform("%d players sit, expected exactly one", self.sitCount())
            elif amount > 0:
                self.bet2pot()
                if self.pot != amount:
                    self.log.inform("pot contains %d, expected %d", self.pot, amount)
                else:
                    self.pot2money(serial)
        else:
            self.log.warn("canceled unexpected while in state %s (ignored)", self.state)

    def returnBlindAnte(self):
        serial = 0
        pot = 0
        for player in self.playersPlaying():
            if player.bet > 0:
                self.bet2pot()
                pot = self.pot
                serial = player.serial
                self.pot2money(serial)
        self.acceptPlayersWaitingForFirstRound()
        self.historyAdd("canceled", serial, pot)

    def getSerialByNameNoCase(self, name):
        name = name.lower()
        for player in self.playersAll():
            if player.name.lower() == name:
                return player.serial
        return 0

    def setPosition(self, position):
        if not self.isRunning():
            self.log.inform("changing position while the game is not running has no effect")
        else:
            self.position = position

    def setDealer(self, seat):
        if self.isRunning():
            self.log.inform("cannot change the dealer during the turn")
        else:
            self.dealer_seat = seat

    def getPlayer(self, serial):
        try:
            return self.serial2player[serial]
        except KeyError:
            self.log.warn("getPlayer(%d) returned None", serial, exc_info=1)
            return None

    def getPlayerMoney(self, serial):
        player = self.getPlayer(serial)
        if player:
            return player.money + player.rebuy

    def getSitOut(self, serial):
        return self.serial2player[serial].sit_out

    def comeBack(self, serial):
        if self.canComeBack(serial):
            player = self.serial2player[serial]
            player.remove_next_turn = False
            player.sit_out_next_turn = False
            player.sit_requested = False
            player.auto = False
            return True
        else:
            return False

    def addPlayer(self, serial, seat=-1, name=None):
        if serial in self.serial2player:
            player = self.serial2player[serial]
            if seat == player.seat:
                # Player already added on this seat
                return True
            else:
                # Player already added on another seat
                return False

        if self.canAddPlayer(serial):
            player = PokerPlayer(serial, name, self)
            if self.is_directing:
                if seat != -1:
                    if seat in self.seats_left:
                        player.seat = seat
                        self.seats_left.remove(seat)
                    else:
                        self.log.inform("the seat %d is not among the remaining seats %s", seat, self.seats_left)
                        return False
                else:
                    player.seat = self.seats_left.pop(0)
            else:
                if seat not in self.seats_left:
                    self.log.inform("the seat %d is not among the remaining seats %s", seat, self.seats_left)
                    return False

                player.seat = seat
                self.seats_left.remove(seat)

            self.log.debug("player %d gets seat %d", serial, player.seat)

            self.serial2player[serial] = player
            return True
        else:
            return False

    def botPlayer(self, serial):
        self.serial2player[serial].bot = True
        self.autoBlindAnte(serial)
        self.autoMuck(serial, AUTO_MUCK_ALWAYS)
        self.autoPlayer(serial)

    def interactivePlayer(self, serial):
        self.serial2player[serial].bot = False
        self.noAutoBlindAnte(serial)
        self.autoMuck(serial, AUTO_MUCK_ALWAYS)
        self.noAutoPlayer(serial)

    def autoPlayer(self, serial):
        self.log.debug("autoPlayer: player %d", serial)
        player = self.getPlayer(serial)
        player.auto = True
        if not self.is_directing:
            return
        if self.isBlindAnteRound():
            # note that we can never get here on tournament tables
            # because blind / antes are payed automatically
            if player.isBot():
                if self.getSerialInPosition() == serial:
                    self.autoPayBlindAnte()
            else:
                self.sitOut(serial)
        elif self.isPlaying(serial):
            self.__autoPlay()

    def noAutoPlayer(self, serial):
        self.log.inform("noAutoPlayer: player %d", serial)
        player = self.getPlayer(serial)
        if player:
            player.auto = False
            return True
        else:
            return False

    def removePlayer(self, serial):
        if self.isInTurn(serial):
            self.serial2player[serial].remove_next_turn = True
            if self.isBlindAnteRound():
                self.sitOut(serial)
            else:
                self.__autoPlay()
            return False
        else:
            self.__removePlayer(serial)
            return True

    def seats(self):
        seats = [0] * ABSOLUTE_MAX_PLAYERS
        for (serial, player) in self.serial2player.iteritems():
            seats[player.seat] = serial
        return seats

    def setSeats(self, seats):
        self.resetSeatsLeft()
        seat = 0
        for serial in seats:
            if serial != 0:
                self.serial2player[serial].seat = seat
                if seat in self.seats_left:
                    self.seats_left.remove(seat)
                else:
                    self.log.inform("setSeats: seat %d not in seats_left %s", seat, self.seats_left)
                    self.serial2player[serial].seat = -1
            seat += 1
        if self.seats() != seats:
            self.log.inform("seatSeats: wanted %s but got %s", seats, self.seats())

    def beginTurn(self, hand_serial):
        if not self.isEndOrNull():
            self.log.warn("beginTurn: turn is not over yet")
            return

        self.hand_serial = hand_serial
        self.log.inform("Dealing %s hand number %d", self.getVariantName(), self.hand_serial)
        self.pot = 0
        self.raked_amount = 0
        self.board = PokerCards()
        self.winners = []
        if self.muckable_serials:
            self.log.warn("beginTurn: muckable_serials not empty %s", self.muckable_serials)
        self.muckable_serials = []
        self.win_condition = WON_NULL
        self.serial2best = {}
        self.showdown_stack = []
        self.turn_history = []
        self.turn_history_is_reduced = False
        
        if self.levelUp():
            self.setLevel(self.getLevel() + 1)

        self.resetRoundInfo()
        self.playersBeginTurn()
        if not self.buildPlayerList(True):
            return

        self.changeState(GAME_STATE_BLIND_ANTE)
        if self.blind_info and self.is_directing and not self.first_turn:
            self.moveDealerLeft()
        elif self.forced_dealer_seat >= 0:
            self.dealer_seat = self.forced_dealer_seat
        self.dealerFromDealerSeat()

        self.historyAdd("game",
            self.getLevel(), self.hand_serial,
            self.hands_count, (self.time - self.time_of_first_hand),
            self.variant, self.betting_structure,
            self.player_list[:], self.dealer_seat,
            self.moneyMap())
        self.resetRound()
        self.side_pots = {
          'contributions': {'total': {}},
          'pots': [[0, 0]],
          'building': 0,
          'last_round': self.current_round,
          }
        self.initBlindAnte()
        if self.is_directing:
            self.deck = self.eval.deck()
            self.shuffler.shuffle(self.deck)
            self.updateBlinds()
            self.autoPayBlindAnte()

        self.log.debug("initialisation turn %d ... finished", self.hand_serial)

    def dealerFromDealerSeat(self):
        self.dealer = -1
        seat2player = [None] * ABSOLUTE_MAX_PLAYERS
        for player in self.playersAll():
            seat2player[player.seat] = player
        previous_player = None
        for seat in range(self.dealer_seat + 1, ABSOLUTE_MAX_PLAYERS) + range(0, self.dealer_seat + 1):
            player = seat2player[seat]
            if player and player.serial in self.player_list:
                if seat == self.dealer_seat:
                    self.dealer = self.player_list.index(player.serial)
                    break
                previous_player = player
            elif seat == self.dealer_seat:
                if previous_player:
                    self.dealer = self.player_list.index(previous_player.serial)
                else:
                    # the impossible has happened
                    self.dealer = len(self.player_list) - 1
                break
        if self.dealer < 0:
            self.log.warn(
                "dealer seat %d cannot be translated in player "
                "position among the %d players willing to join the game",
                self.dealer_seat,
                self.playingCount()
            )

    def moveDealerLeft(self):
        if not self.blind_info:
            return
        seat2player = [None] * ABSOLUTE_MAX_PLAYERS
        for player in self.playersAll():
            seat2player[player.seat] = player
        for seat in range(self.dealer_seat + 1, ABSOLUTE_MAX_PLAYERS) + range(0, self.dealer_seat + 1):
            player = seat2player[seat]
            if player and player.isSit() and not player.isWaitForBlind():
                if self.seatsCount() <= 2:
                    self.dealer_seat = seat
                    break
                elif player.missed_blind == None:
                    self.dealer_seat = seat
                    break

    def isBlindRequested(self, serial):
        return (self.getSerialInPosition() == serial and
                 self.isBlindAnteRound() and
                 self.blind_info and
                 not self.getPlayer(serial).isAutoBlindAnte())

    def isAnteRequested(self, serial):
        return (self.getSerialInPosition() == serial and
                 self.isBlindAnteRound() and
                 self.ante_info and
                 not self.getPlayer(serial).isAutoBlindAnte())

    def sitCountBlindAnteRound(self):
        sit_count = 0
        for player in self.playersSit():
            if player.wait_for != "first_round":
                sit_count += 1
        return sit_count

    def updateBlinds(self):

        if not self.blind_info:
            return

        sit_count = self.sitCountBlindAnteRound()

        if sit_count <= 1:
            #
            # Forget the missed blinds and all when there is less than
            # two players willing to join the game.
            #
            for player in self.playersAll():
                player.resetMissedBlinds()
                player.blind = False
                if player.wait_for != 'first_round':
                    player.wait_for = False
            return

        seat2player = [None] * ABSOLUTE_MAX_PLAYERS
        blind_ok_count = 0
        for player in self.playersAll():
            seat2player[player.seat] = player
            if player.isSit() and player.wait_for != 'first_round' and player.missed_blind == None:
                blind_ok_count += 1

        if self.seatsCount() == 2:
            first = self.dealer_seat
        else:
            first = self.dealer_seat + 1

        players = seat2player[first:] + seat2player[:first]

        #
        # If less than two players did not miss the blind, declare
        # that all missed blinds are forgotten. That solves a special
        # case that would lead to the unability to assign the big blind
        # to someone despite the fact that there would be players willing
        # to pay for it. For instance, if all players are
        # new (missed_blind == "n/a") and only one player is ok with his
        # blind AND is on the button. Another case is when all players
        # save one are waiting for the late blind. This player would have to pay the
        # small blind but then, there would be a need to walk the list
        # of players, starting from the dealer, once more to figure out
        # who has to pay the big blind. Furthermore, this case leads to
        # the awkward result that the person next to the dealer pays the
        # big blind and the dealer pays the small blind.
        #
        if blind_ok_count < 2:
            self.log.debug("Forbid missed blinds")
            for player in players:
                if player and player.isSit():
                    player.resetMissedBlinds()
                    if player.wait_for == "late":
                        player.wait_for = False

        def updateMissed(players, index, what):
            while index < ABSOLUTE_MAX_PLAYERS and (
                not players[index] or 
                not players[index].isSit() or
                players[index].wait_for == 'first_round'
            ):
                player = players[index]
                if player and player.wait_for != 'first_round':
                    if player.missed_blind == None:
                        player.missed_blind = what
                    if player.missed_blind == "big" and what == "big":
                        player.missed_big_blind_count += 1
                    self.log.debug("%d big blind count is now %d because of %s", player.serial, player.missed_big_blind_count, what)
                index += 1
            return index

        #
        # Small blind
        #
        done = False
        index = 0
        while index < ABSOLUTE_MAX_PLAYERS and not done:
            index = updateMissed(players, index, "small")
            if index >= ABSOLUTE_MAX_PLAYERS:
                continue
            player = players[index]
            if player.blind == True:
                done = True
            elif ((not player.wait_for and
                     player.missed_blind == None) or
                   sit_count == 2):
                player.blind = "small"
                done = True
            elif player.missed_blind != None:
                player.wait_for = "late"
            index += 1

        if not done:
            self.log.warn("updateBlinds cannot assign the small blind")

        #
        # Big blind
        #
        index = updateMissed(players, index, "big")
        if index < ABSOLUTE_MAX_PLAYERS:
            player = players[index]
            if player.wait_for:
                player.wait_for = False
            if player.blind == True:
                pass
            else:
                player.blind = "big"
            index += 1
        else:
            self.log.warn("updateBlinds cannot assign big blind")
        #
        #
        # Late blind
        #
        while index < ABSOLUTE_MAX_PLAYERS:
            player = players[index]
            if player:
                if not player.sit_out:
                    if player.wait_for == "big" or player.missed_blind == None:
                        player.blind = False
                    elif player.missed_blind in ('big', 'small'):
                        if sit_count > 5:
                            player.blind = "big_and_dead"
                        else:
                            player.blind = "late"
                        player.wait_for = False
                    elif (player.missed_blind == "n/a" and player.wait_for != "first_round"):
                        player.blind = "late"
                        player.wait_for = False
                    else:
                        self.log.warn(
                            "updateBlinds statement unexpectedly reached while evaluating "
                            "late blind (player: %s, missed_blind: %s, wait_for: %s)",
                            player.serial,
                            player.missed_blind,
                            player.wait_for
                        )
                else:
                    player.blind = False
            index += 1
        showblinds = lambda player: "%02d:%s:%s:%s" % (player.serial, player.blind, player.missed_blind, player.wait_for)
        self.log.debug("updateBlinds: in game (blind:missed:wait): " + ", ".join(map(showblinds, self.playersInGame())))
        players = self.playersAll()
        players.sort(key=lambda i: i.seat)
        self.log.debug("updateBlinds: all     (blind:missed:wait): " + ", ".join(map(showblinds, players)))

    def handsMap(self):
        pockets = {}
        for player in self.playersNotFold():
            pockets[player.serial] = player.hand.copy()
        return pockets

    def moneyMap(self):
        money = dict((player.serial,player.money) for player in self.playersNotFold())
        return money

    def isTournament(self):
        return self.hasLevel()

    def hasLevel(self):
        return (
            (self.blind_info and self.blind_info["change"]) or
            (self.ante_info and self.ante_info["change"])
        )

    def delayToLevelUp(self):
        for what in (self.blind_info, self.ante_info):
            if not what or not what["change"]:
                continue

            if self.level == 0:
                return (0, what["unit"])

            if what["unit"] == "minute" or what["unit"] == "minutes":
                return ((what["frequency"] * 60) - (self.time - what["time"]), "second")

            elif what["unit"] == "hand" or what["unit"] == "hands":
                return (what["frequency"] - (self.hands_count - what["hands"]), "hand")

            else:
                self.log.warn("delayToLevelUp: unknown unit %s ", what["unit"])

        return False

    def levelUp(self):
        if not self.is_directing:
            return False

        delay = self.delayToLevelUp()
        if delay:
            return delay[0] <= 0
        else:
            return False

    def updateStatsFlop(self, fold_before_flop):
        info = self.stats
        if fold_before_flop:
            flop = 0
        else:
            flop = (self.inGameCount() * 100) / self.sitCount()
        info["flops"].append(flop)
        if len(info["flops"]) > info["flops_count"]:
            info["flops"].pop(0)
        info["percent_flop"] = sum(info["flops"]) / min(info["flops_count"], len(info["flops"]))

    def updateStatsEndTurn(self):
        info = self.stats

        #
        # First time thru
        #
        if info["time"] == -1:
            info["hands_count"] = self.hands_count
            info["time"] = self.time
            return

        info["pots"].append(self.getSidePotTotal())
        if len(info["pots"]) > info["pots_count"]:
            info["pots"].pop(0)
        delta = self.time - info["time"]
        if delta > info["frequency"]:
            info["average_pot"] = sum(info["pots"]) / min(info["pots_count"], len(info["pots"]))
            info["hands_per_hour"] = (self.hands_count - info["hands_count"]) * (3600 / info["frequency"])
            info["hands_count"] = self.hands_count
            info["time"] = self.time

    def setHandsCount(self, hands_count):
        self.hands_count = hands_count

    def setTime(self, time):
        if self.time_of_first_hand == -1:
            self.time_of_first_hand = time  # first turn, so we get initial time
        self.time = time

    def initBlindAnte(self):
        self.side_pots['contributions'][self.current_round] = {}

        is_tournament = self.isTournament()

        if is_tournament:
            for player in self.playersAll():
                player.auto_blind_ante = True

        if not self.is_directing:
            return

        if self.blind_info and (self.first_turn or is_tournament):
            for player in self.playersAll():
                player.resetMissedBlinds()

        if self.blind_info:
            if self.seatsCount() == 2:
                self.position = self.dealer
            else:
                self.position = self.indexInGameAdd(self.dealer, 1)
        else:
            self.position = self.dealer

    def isBlindAntePayed(self):
        if self.blind_info:
            for player in self.playersPlaying():
                if player.isSitOut():
                    continue
                if type(player.blind) != bool: # i.e. not True or False
                    return False
        if self.ante_info:
            for player in self.playersPlaying():
                if player.isSitOut():
                    continue
                if not player.ante:
                    return False
        return True

    def blindAmount(self, serial):
        if self.blind_info:
            player = self.getPlayer(serial)
            big = self.blind_info["big"]
            small = self.blind_info["small"]
            if player.blind == "big":
                return (big, 0, player.blind)
            elif player.blind == "late":
                return (big, 0, player.blind)
            elif player.blind == "small":
                return (small, 0, player.blind)
            elif player.blind == "big_and_dead":
                return (big, small, player.blind)
            elif type(player.blind) == bool: # i.e. True or False
                return (0, 0, player.blind)
            else:
                self.log.warn("blindAmount unexpected condition for player %d", player.serial)
        else:
            return (0, 0, False)

    def smallBlind(self):
        return self.blind_info["small"] if self.blind_info else None

    def bigBlind(self):
        return self.blind_info["big"] if self.blind_info else None

    def autoPayBlindAnte(self):
        if not self.is_directing:
            return

        if not self.blind_info and not self.ante_info:
            self.__talkedBlindAnte()
            return

        auto_payed = False
        for self.position in range(self.position, len(self.player_list)) + range(0, self.position):
            serial = self.player_list[self.position]
            player = self.serial2player[serial]
            if player.isSitOut():
                #
                # This case happens when a player refuses to pay the blind/ante
                # He is sit out but will only be removed from the player list when
                # the blind/ante round is over.
                #
                continue
            if self.blind_info:
                (amount, dead, state) = self.blindAmount(serial)
                if amount > 0:
                    self.historyAddNoDuplicate("position", self.position, self.player_list[self.position])
                    if player.isAutoBlindAnte():
                        self.payBlind(serial, amount, dead)
                        auto_payed = True
                    else:
                        self.historyAdd("blind_request", serial, amount, dead, state)
                        auto_payed = False
                        break
            if self.ante_info and player.ante == False:
                self.historyAddNoDuplicate("position", self.position, self.player_list[self.position])
                if player.isAutoBlindAnte():
                    self.payAnte(serial, self.ante_info["value"])
                    auto_payed = True
                else:
                    self.historyAdd("ante_request", serial, self.ante_info["value"])
                    auto_payed = False
                    break
            if self.isBlindAntePayed():
                break

        if auto_payed:
            self.__talkedBlindAnte()

    def acceptPlayersWaitingForFirstRound(self):
        #
        # Players who sit while others are paying the blinds are
        # waiting for the first round so that buildPlayerList
        # does not include them. When the first round starts, this
        # mark can be removed.
        #
        for player in self.playersSit():
            if player.wait_for == "first_round":
                player.wait_for = False

    def initRound(self):
        info = self.roundInfo()
        self.log.debug("new round %s", info["name"])
        if self.isFirstRound():
            if not self.is_directing:
                self.buildPlayerList(False)
                self.dealerFromDealerSeat()
            self.acceptPlayersWaitingForFirstRound()
        self.round_cap_left = self.roundCap()
        self.log.debug("round cap reset to %d", self.round_cap_left)
        self.first_betting_pass = True
        if info["position"] == "under-the-gun":
            #
            # The player under the gun is the first to talk
            #
            count = self.inGameCount()
            if count < 2 and self.betsEqual():
                raise UserWarning("initialization but less than two players in game")
            if self.seatsCount() == 2:
                self.position = self.dealer
            else:
                under_the_gun = self.indexNotFoldAdd(self.dealer, 2)
                self.position = self.indexInGameAdd(under_the_gun, 1)
        elif info["position"] == "next-to-dealer":
            #
            # The player left to the dealer is first to talk
            #
            self.position = self.indexInGameAdd(self.dealer, 1)
            #
            # The dealer is last to talk. However, if the dealer folded,
            # the player before him is last to talk.
            #
            next_to_dealer = self.indexInGameAdd(self.dealer, 1)
            dealer_or_before_him = self.indexInGameAdd(next_to_dealer, -1)
        elif info["position"] == "low" or info["position"] == "high":
            values = []
            for player in self.playersInGame():
                values.append(self.eval.evaln(player.hand.getVisible()))
                self.log.debug("%s : %d", player.hand.getVisible(), values[-1])
            if info["position"] == "low":
                value = min(values)
            else:
                value = max(values)
            index = values.index(value)
            serial = self.serialsInGame()[index]
            self.position = self.player_list.index(serial)
        else:
            raise UserWarning("unknown position info %s" % info["position"])
        #
        # In theory, when there is a live bet from the blind/ant round,
        # last_bet should be set to big_blind - small_blind. However, this
        # is useless in practice because the minimum bet will always be
        # higher than this number. Since the purpose of last_bet is to define
        # the minimum bet when this minimum is a consequence of a bet that
        # is larger than the minimum bet, setting it to zero is equivalent
        # to setting it to the actual difference between the big_blind and
        # the small_blind for all intended purposes.
        #
        self.last_bet = 0
        if self.isFirstRound():
            #
            # The first round takes the live blinds/antes
            # (is there any game with live antes ?)
            #
            self.blindAnteMoveToFirstRound()
        else:
            self.side_pots['contributions'][self.current_round] = {}
            self.uncalled = 0
            self.uncalled_serial = 0
        self.side_pots['last_round'] = self.current_round

        if self.isSecondRound():
            self.updateStatsFlop(False)

        if info["position"] == "under-the-gun":
            self.last_to_talk = self.indexInGameAdd(self.position, -1)
        elif info["position"] == "next-to-dealer":
            self.last_to_talk = dealer_or_before_him
        elif info["position"] == "low" or info["position"] == "high":
            self.last_to_talk = self.indexInGameAdd(self.position, -1)
        else:
            # Impossible case
            # The position value has already been tested at the beginning of the method
            raise UserWarning("unknown position info %s" % info["position"])  # pragma: no cover

        for player in self.playersInGame():
            player.talked_once = False

        self.log.debug("dealer %d, in position %d, last to talk %d", self.dealer, self.position, self.last_to_talk)
        self.historyAdd("round", self.state, self.board.copy(), self.handsMap())
        self.historyAdd("position", self.position, self.player_list[self.position])
        self.__autoPlay()

    def sortPlayerList(self):
        self.player_list.sort(key=lambda i: self.serial2player[i].seat)

    def playersBeginTurn(self):
        for player in self.playersAll():
            player.beginTurn()
        if not self.is_directing:
            for player in self.playersAll():
                if player.wait_for != "first_round":
                    player.wait_for = False

    def buildPlayerList(self, with_wait_for):
        if self.sitCount() < 2:
            self.log.warn("cannot make a consistent player list with less than two players willing to join the game")
            return False
        #
        # The player list is the list of players seated, sorted by seat
        old_player_list = self.player_list
        if with_wait_for:
            self.player_list = [s for s, p in self.serial2player.iteritems() if p.isSit() and p.wait_for != "first_round"]
        else:
            self.player_list = [s for s, p in self.serial2player.iteritems() if p.isSit() and not p.isWaitForBlind()]
        self.sortPlayerList()
        
        # extended logging
        if self.is_directing and \
            self.state not in (GAME_STATE_NULL, GAME_STATE_END, GAME_STATE_BLIND_ANTE) and \
            len(self.player_list) > len(old_player_list):
                self.log.warn(
                    "player_list grew unexpectedly (state=%s): %s -> %s",
                    self.state,
                    old_player_list,
                    self.player_list,
                    exc_info=1
                )

        self.log.debug("player list: %s", self.player_list)
        return True

    def getLevel(self):
        return self.level

    def getLevelValues(self, level):
        info = self.blind_info
        blind_info = None
        if info and info["change"]:
            blind_info = {}
            if info["change"] == "double":
                blind_info["small"] = info["small_reference"] * pow(2, level - 1)
                blind_info["big"] = info["big_reference"] * pow(2, level - 1)
            elif info["change"] == "levels" or info["change"] == "level":
                if level <= len(info["levels"]):
                    level_info = info["levels"][level - 1]
                    blind_info["small"] = level_info["small"]
                    blind_info["big"] = level_info["big"]
                else:
                    self.log.warn("unexpected blind change level %d ", level)
            else:
                blind_info = None
                self.log.warn("unexpected blind change method %s ", info["change"])

        info = self.ante_info
        ante_info = None
        if info and info["change"]:
            ante_info = {}
            if info["change"] == "double":
                ante_info["value"] = info["value_reference"] * pow(2, level - 1)
                ante_info["bring-in"] = info["bring-in_reference"] * pow(2, level - 1)
            elif info["change"] == "levels":
                if level <= len(info["levels"]):
                    level_info = info["levels"][level - 1]
                    ante_info["value"] = level_info["value"]
                    ante_info["bring-in"] = level_info["bring-in"]
                else:
                    self.log.warn("unexpected ante change level %d " % level)
            else:
                ante_info = None
                self.log.warn("unexpected ante change method %s ", info["change"])

        return (blind_info, ante_info)

    def setLevel(self, level):
        if level == self.level:
            return

        (blind_info, ante_info) = self.getLevelValues(level)
        info = self.blind_info
        if blind_info:
            info["hands"] = self.hands_count
            info["time"] = self.time
            info["small"] = blind_info["small"]
            info["big"] = blind_info["big"]

        info = self.ante_info
        if ante_info:
            info["hands"] = self.hands_count
            info["time"] = self.time
            info["value"] = ante_info["value"]
            info["bring-in"] = ante_info["bring-in"]

        self.level = level

    def minMoney(self):
        if self.isTournament():
            return 0
        elif self.blind_info:
            return self.blind_info["big"] + self.blind_info["small"]
        elif self.ante_info:
            return self.ante_info["value"] + self.ante_info["bring-in"]
        else:
            return 0

    def isBroke(self, serial):
        player = self.getPlayer(serial)
        if player:
            money = player.money
            return money <= 0 or (not self.isTournament() and money < self.minMoney())
        else:
            return False

    def endTurn(self):
        self.log.debug("---end turn--")

        self.hands_count += 1
        self.updateStatsEndTurn()

        self.dealer_seat = self.getPlayerDealer().seat

        self.historyAdd("end", self.winners[:], self.showdown_stack)

        for player in self.playersAll():
            if player.rebuy > 0:
                player.money += player.rebuy
                self.historyAdd("rebuy", player.serial, player.rebuy)
                player.rebuy = 0

        #
        # Players who are broke automatically sit out.
        # In live games, one cannot play with less than one big blind + dead.
        #
        for player in self.playersSit():
            if self.isBroke(player.serial):
                player.sit_out_next_turn = True

        #
        # Compute sit_out for all players so that it accurately
        # reflects the players that will not be playing next turn
        # (regardless of the fact that a new player may join later)
        #
        sitting_out = []
        self.log.debug('---- playersALL %r' % self.playersAll())
        for player in self.playersAll():
            self.log.debug(':(%s) %s' % (player.serial, player.auto_player_fold_next_turn))
            if player.sit_out_next_turn:
                self.historyAdd("sitOut", player.serial)
                self.sitOut(player.serial)
                sitting_out.append(player.serial)
            if player.remove_next_turn:
                if player.serial not in sitting_out:
                    self.historyAdd("sitOut", player.serial)
                    self.sitOut(player.serial)
                    sitting_out.append(player.serial)
            if player.auto_player_fold_next_turn:
                self.log.debug(': foldpolicy')
                self.historyAdd("AutoPlayPolicy", player.serial, "fold")
                player.auto_player_fold_next_turn = False
                player.auto_player_policy = 'fold'

        disconnected = self.playersDisconnected()
        if disconnected:
            self.historyAdd("leave",[(player.serial,player.seat) for player in disconnected])
        for player in disconnected:
            self.__removePlayer(player.serial)
        self.historyAdd("finish", self.hand_serial)

    def __removePlayer(self, serial):
        #
        # Get his seat back
        #
        self.log.debug("removing player %d from game", serial)
        if not self.serial2player[serial].seat in self.seats_left:
            self.seats_left.insert(0, self.serial2player[serial].seat)
        else:
            self.log.inform("%d alreay in seats_left", self.serial2player[serial].seat)
        #
        # Forget about him
        #
        if serial in self.player_list:
            self.player_list.remove(serial)
        del self.serial2player[serial]

    def isBlindAnteRound(self):
        return self.current_round == -1

    def isFirstRound(self):
        return self.current_round == 0

    def isSecondRound(self):
        return self.current_round == 1

    def isLastRound(self):
        return self.current_round == len(self.round_info) - 1

    def resetRound(self):
        self.current_round = -1

    def nextRound(self):
        self.current_round += 1
        if self.position != -1:
            self.historyAdd("position", -1, None)
        self.position = -1
        self.changeState(self.roundInfo()["name"])

    def muckState(self, win_condition):
        self.current_round = -2
        if self.position != -1:
            self.historyAdd("position", -1, None)
        self.position = -1

        self.win_condition = win_condition
        self.changeState(GAME_STATE_MUCK)

        if self.is_directing:
            self.distributeMoney()
            to_show, muckable_candidates_serials = self.dispatchMuck()

            self.log.debug("muckState: to_show = %s muckable_candidates = %s ", to_show, muckable_candidates_serials)

            muckable_serials = []
            for serial in to_show:
                self.serial2player[serial].hand.allVisible()
            for serial in muckable_candidates_serials:
                auto_muck = self.serial2player[serial].auto_muck
                if auto_muck == AUTO_MUCK_ALWAYS:
                    pass
                elif auto_muck == AUTO_MUCK_WIN and self.isWinnerBecauseFold():
                    pass
                elif auto_muck == AUTO_MUCK_LOSE and not self.isWinnerBecauseFold():
                    pass
                else:
                    muckable_serials.append(serial)
            self.setMuckableSerials(muckable_serials)
            self.__talked_muck()
        else:
            self.log.debug("muckState: not directing...")

    def setRakedAmount(self, rake):
        if rake > 0:
            self.raked_amount = rake
            self.historyAdd("rake", rake, self.getRakeContributions())

    def getRakedAmount(self):
        return self.raked_amount

    def getRakeContributions(self):
        rake = self.getRakedAmount()

        total = self.getPotAmount() - self.getUncalled()
        uncalled_serial = self.getUncalledSerial()
        side_pots = self.getPots()

        #
        # Uncalled bet is not raked
        #
        serial2share = side_pots['contributions']['total'].copy()
        if uncalled_serial > 0:
            serial2share[uncalled_serial] -= self.getUncalled()

        return self.distributeRake(rake, total, serial2share)

    def distributeRake(self, rake, total, serial2share):
        #
        # Each player contributes to the rake in direct proportion
        # of their contribution to the global pot (uncalled bet does
        # not count).
        #
        total_rake = rake
        serial2rake = {}
        if len(serial2share) == 1:
            #
            # Special case to avoid rounding errors
            #
            serial2rake[serial2share.keys()[0]] = rake
            rake = 0
        else:
            for (serial, contribution) in serial2share.iteritems():
                # in some corner cases the player object is not
                # available anymore so a check has to be made here
                if serial in self.serial2player:
                    raked_player = self.getPlayer(serial)
                    contribution += raked_player.dead
                player_rake = (total_rake * contribution) / total
                serial2rake[serial] = player_rake
                rake -= player_rake

        if rake > 0:
            keys = serial2rake.keys()
            keys.sort(cmp=lambda a, b: cmp(serial2rake[a], serial2rake[b]) or cmp(a, b))
            #
            # rake distribution rounding error benefit the player with the
            # lowest rake participation (with the idea that a player with
            # very little rake participation has a chance to not be raked
            # at all instead of being raked for 1 unit).
            #
            # Note: the rake rounding error can't be greater than the number
            #       of players. But the above distribution is slightly flawed
            #       because the dead blind is not accounted as a contribution
            #       of the player to the pot, therefore the total is not 100%.
            #
            if keys:
                while rake > 0:
                    for serial in keys:
                        serial2rake[serial] += 1
                        rake -= 1
                        if rake <= 0:
                            break
            else:
                self.log.debug("distributeRake: have no keys --> no rake. serial2rake = %s", serial2rake)
        return serial2rake

    def setMuckableSerials(self, muckable_serials):
        self.muckable_serials = list(muckable_serials)
        if muckable_serials:
            self.historyAdd("muck", self.muckable_serials[:])
        self.log.debug("setMuckableSerials: muckable = %s", self.muckable_serials)

    def cancelState(self):
        self.current_round = -2
        if self.position != -1:
            self.historyAdd("position", -1, None)
        self.position = -1
        self.changeState(GAME_STATE_END)
        self.runCallbacks("end_round_last")

    def endState(self):
        self.current_round = -2
        self.changeState(GAME_STATE_END)
        self.runCallbacks("end_round_last")
        self.endTurn()

    def roundInfo(self):
        return self.round_info[self.current_round]

    def betInfo(self):
        return self.bet_info[self.current_round]

    def getChipUnit(self):
        return self.unit

    def willAct(self, serial):
        if self.isRunning() and serial in self.serialsInGame():
            player = self.getPlayer(serial)
            return not player.talked_once or self.canCall(serial)
        else:
            return False

    def canAct(self, serial):
        return (self.isRunning() and
                 self.getSerialInPosition() == serial and
                 self.cardsDealt())

    def canCall(self, serial):
        """
        Can call if the highest bet is greater than the player bet.
        """
        if self.isBlindAnteRound():
            return False
        player = self.serial2player[serial]
        return self.highestBetNotFold() > player.bet

    def canRaise(self, serial):
        """
        Can raise if round cap not reached and the player can at
        least match the highest bet.
        """
        if self.isBlindAnteRound():
            return False
        player = self.serial2player[serial]
        highest_bet = self.highestBetNotFold()
        money = player.money
        bet = player.bet
        #
        # Can raise if the round is not capped and the player has enough money to
        # raise. The player will be given an opportunity to raise if his bet is
        # lower than the highest bet on the table or if he did not yet talk in this
        # betting round (for instance if he payed the big blind or a late blind).
        #
        return (
            self.round_cap_left != 0 and 
            money > highest_bet - bet and 
            (player.talked_once == False or bet < highest_bet)
        )

    def canCheck(self, serial):
        """
        Can check if all bets are equal
        """
        if self.isBlindAnteRound():
            return False
        return self.highestBetNotFold() <= self.getPlayer(serial).bet

    def canFold(self, serial):
        """
        Can fold if in game and not in blind round
        """
        if self.isBlindAnteRound():
            return False
        player = self.getPlayer(serial)
        if not player.isInGame():
            return False
        return True

    def setPlayerBlind(self, serial, blind):
        if self.isBlindAnteRound() and self.isInPosition(serial):
            self.getPlayer(serial).blind = blind

    def getRequestedAction(self, serial):
        if self.isInPosition(serial):
            if self.isBlindAnteRound():
                return "blind_ante"
            else:
                return "play"
        else:
            player = self.getPlayer(serial)
            if not self.isTournament() and player:
                if not player.isBuyInPayed():
                    return "buy-in"
                elif self.isBroke(serial):
                    return "rebuy"
                else:
                    return None
            else:
                return None

    def possibleActions(self, serial):
        actions = []
        if self.canAct(serial) and not self.isBlindAnteRound():
            if self.canCall(serial):
                actions.append("call")
            if self.canRaise(serial):
                actions.append("raise")
            if self.canCheck(serial):
                actions.append("check")
            else:
                actions.append("fold")
        return actions

    def inSmallBlindPosition(self):
        return self.indexInGameAdd(self.dealer, 1) == self.position

    def call(self, serial):
        if self.isBlindAnteRound() or not self.canAct(serial):
            self.log.inform("player %d cannot call. state = %s", serial, self.state)
            return False

        player = self.serial2player[serial]
        amount = min(
            max(
                self.highestBetNotFold(),
                self.bigBlind() if self.state == GAME_STATE_PRE_FLOP and not self.inSmallBlindPosition() else 0
            ) - player.bet,
            player.money
        )
        self.log.debug("player %d calls %d", serial, amount)
        self.historyAdd("call", serial, amount)
        self.bet(serial, amount)
        return True

    def callNraise(self, serial, amount):
        if self.isBlindAnteRound() or not self.canAct(serial):
            self.log.inform("player %d cannot raise. state = %s", serial, self.state)
            return False

        if self.round_cap_left <= 0:
            self.log.inform("round capped, can't raise (ignored)")
            if self.round_cap_left < 0:
                self.log.warn("round cap below zero")
            return False

        (min_bet, max_bet, to_call) = self.betLimits(serial)
        if amount < min_bet:
            amount = min_bet
        elif amount > max_bet:
            amount = max_bet
        self.log.debug("player %d raises %d", serial, amount)
        self.historyAdd("raise", serial, amount)
        highest_bet = self.highestBetNotFold()
        self.money2bet(serial, amount)
        if self.isRunning():
            last_bet = self.highestBetNotFold() - highest_bet
            self.last_bet = max(self.last_bet, last_bet)
            self.round_cap_left -= 1
            self.log.debug("round cap left %d", self.round_cap_left)
            self.runCallbacks("round_cap_decrease", self.round_cap_left)
        self.__talked(serial)
        return True

    def bet(self, serial, amount):
        self.log.debug("player %d bets %s", serial, amount)
        #
        # Transfert the player money from his stack to the bet stack
        #
        self.money2bet(serial, amount)
        self.__talked(serial)

    def check(self, serial):
        if self.isBlindAnteRound() or not self.canAct(serial):
            self.log.inform("player %d cannot check. state = %s (ignored)", serial, self.state)
            return False

        if not self.canCheck(serial):
            self.log.inform("player %d tries to check but should call or raise (ignored)", serial)
            return False

        self.log.debug("player %d checks" % serial)
        self.historyAdd("check", serial)
        #
        # Nothing done: that's what "check" stands for
        #
        self.__talked(serial)
        return True

    def fold(self, serial):
        if self.isBlindAnteRound() or not self.canAct(serial):
            self.log.inform("player %d cannot fold. state = %s (ignored)", serial, self.state)
            return False

        if self.serial2player[serial].fold == True:
            self.log.inform("player %d already folded (presumably autoplay)", serial)
            return True

        self.log.debug("player %d folds", serial)
        self.historyAdd("fold", serial)
        self.serial2player[serial].fold = True
        #
        # His money goes to the pot
        #
        self.bet2pot(serial)
        self.__talked(serial)
        return True

    def waitBigBlind(self, serial):
        if not self.blind_info:
            self.log.inform("no blind due")
            return False
        if not self.isBlindAnteRound():
            self.log.inform("player %d cannot pay blind while in state %s", serial, self.state)
            return False
        if not self.canAct(serial):
            self.log.inform(
                "player %d cannot wait for blind. state = %s, serial in position = %d (ignored)",
                serial,
                self.state,
                self.getSerialInPosition()
            )
            return False
        player = self.serial2player[serial]
        player.wait_for = "big"
        if self.is_directing:
            self.updateBlinds()
            self.historyAdd("wait_blind", serial)
            self.__talkedBlindAnte()
        return True

    def blind(self, serial, amount=0, dead=0):
        if not self.blind_info:
            self.log.inform("no blind due")
            return False
        if not self.isBlindAnteRound():
            self.log.inform("player %d cannot pay blind while in state %s", serial, self.state)
            return False
        if not self.canAct(serial):
            self.log.inform("player %d cannot pay blind. state = %s, serial in position = %d (ignored)", serial, self.state, self.getSerialInPosition())
            return False
        if self.is_directing and amount == 0:
            (amount, dead, state) = self.blindAmount(serial)
        self.payBlind(serial, amount, dead)
        if self.is_directing:
            self.__talkedBlindAnte()

    def payBlind(self, serial, amount, dead):
        player = self.serial2player[serial]
        money = player.money
        if money < amount + dead:
            #
            # If the player does not have enough money to pay the blind,
            # make sure the live blind is payed before putting money into
            # the dead blind.
            #
            if money < amount:
                dead = 0
                amount = money
            else:
                dead = money - amount
        self.log.debug("player %d pays blind %d/%d", serial, amount, dead)
        self.historyAdd("blind", serial, amount, dead)
        if dead > 0:
            #
            # There is enough money to pay the amount, pay the dead, if any
            #
            # Note about uncalled amounts : the dead is always lower than the
            # blind, therefore if self.uncalled is updated (indirectly thru
            # the self.money2bet in the line immediately following this comment)
            # it will *always* be overriden by the self.uncalled
            # self.money2bet of the blind.
            #
            self.money2bet(serial, dead, dead_money=True)
            self.bet2pot(serial=serial, dead_money=True)

        self.money2bet(serial, amount)
        player.blind = True
        player.resetMissedBlinds()
        player.wait_for = False

    def ante(self, serial, amount=0):
        if not self.ante_info:
            self.log.inform("no ante due")
            return False
        if not self.isBlindAnteRound():
            self.log.inform("player %d cannot pay ante while in state %s", serial, self.state)
            return False
        if not self.canAct(serial):
            self.log.inform("player %d cannot pay ante. state = %s, serial in position = %d (ignored)",
                serial,
                self.state,
                self.getSerialInPosition()
            )
            return False
        if self.is_directing and amount == 0:
            amount = self.ante_info['value']
        self.payAnte(serial, amount)
        if self.is_directing:
            self.__talkedBlindAnte()
        return True

    def payAnte(self, serial, amount):
        player = self.serial2player[serial]
        amount = min(amount, player.money)
        self.log.debug("player %d pays ante %d", serial, amount)
        self.historyAdd("ante", serial, amount)
        self.money2bet(serial, amount)
        self.bet2pot(serial)
        self.getPlayer(serial).ante = True

    def blindAnteMoveToFirstRound(self):
        if (self.current_round - 1) not in self.side_pots['contributions']:
            self.log.warn("round %d not found in contributions (state: %s)",
                self.current_round - 1,
                self.state
            )
            raise KeyError(self.current_round - 1)
        else:
            self.side_pots['contributions'][self.current_round] = self.side_pots['contributions'][self.current_round - 1]
            del self.side_pots['contributions'][self.current_round - 1]
        # self.uncalled is kept to what it was set during the blind/ante round with live bets

    def blindAnteRoundEnd(self):
        if self.is_directing:
            return

        if self.inGameCount() < 2 and self.betsEqual():
            #
            # All players are all-in except one, distribute all
            # cards and figure out who wins.
            #
            self.log.debug("less than two players not all-in")
            self.nextRound()
            self.blindAnteMoveToFirstRound()
            self.__makeSidePots()
            self.bet2pot()

            self.log.debug("money not yet distributed, assuming information is missing ...")
        else:
            self.nextRound()

    def muck(self, serial, want_to_muck):
        if not self.is_directing:
            self.log.inform("muck action ignored...")
            return
        if not self.state == GAME_STATE_MUCK:
            self.log.warn("muck: game state muck expected, found %s", self.state)
            return
        if serial not in self.muckable_serials:
            self.log.warn("muck: serial %s not found in muckable_serials", serial)
            return

        self.muckable_serials.remove(serial)
        if not want_to_muck:
            self.serial2player[serial].hand.allVisible()
        self.__talked_muck()

    def __talkedBlindAnte(self):
        if self.sitCountBlindAnteRound() < 2:
            self.returnBlindAnte()
            self.cancelState()
            return

        if self.isBlindAntePayed():
            #
            # Once the blind and antes are payed, it may be necessary to
            # recompute the list of players willing to participate in the
            # turn. Some of them may have declined to pay the blind/ante
            # and thus excluded themselves from the turn.
            #
            player_list = self.player_list[:]
            self.buildPlayerList(False)
            if player_list != self.player_list:
                for serial in player_list:
                    player = self.getPlayer(serial)
                    if player.wait_for:
                        self.historyAdd("wait_for", serial, player.wait_for)
                self.historyAdd("player_list", self.player_list)
            self.dealerFromDealerSeat()
            self.first_turn = False
            if self.inGameCount() < 2 and self.betsEqual():
                #
                # All players are all-in (except one, maybe), distribute all
                # cards and figure out who wins.
                #
                self.log.debug("less than two players not all-in")
                self.nextRound()
                self.blindAnteMoveToFirstRound()
                self.__makeSidePots()
                self.bet2pot()
                self.dealCards()

                while not self.isLastRound():
                    self.nextRound()
                    self.dealCards()

                self.muckState(WON_ALLIN_BLIND)
            else:
                self.nextRound()
                self.dealCards()
                if self.is_directing:
                    self.initRound()
        else:
            self.updateBlinds()
            self.position = self.indexInGameAdd(self.position, 1)
            self.historyAdd("position", self.position, self.player_list[self.position])
            self.autoPayBlindAnte()

    def __talked(self, serial):
        self.getPlayer(serial).talked_once = True
        if self.__roundFinished(serial):
            self.log.debug("round finished")

            self.__makeSidePots()
            self.bet2pot()

            if self.notFoldCount() < 2:
                self.position = self.indexNotFoldAdd(self.position, 1)
                self.historyAdd("position", self.position, self.player_list[self.position])
                self.log.debug("last player in game %d", self.getSerialInPosition())
                if self.isFirstRound():
                    self.updateStatsFlop(True)

                self.muckState(WON_FOLD)

            elif self.inGameCount() < 2:
                #
                # All players are all-in except one, distribute all
                # cards and figure out who wins.
                #
                self.log.debug("less than two players not all-in")
                while not self.isLastRound():
                    self.nextRound()
                    self.dealCards()

                self.muckState(WON_ALLIN)
            else:
                #
                # All bets equal, go to next round
                #
                self.log.debug("next state")
                if self.isLastRound():
                    self.muckState(WON_REGULAR)
                else:
                    self.nextRound()
                    if self.is_directing:
                        self.dealCards()
                        self.initRound()
                    else:
                        self.runCallbacks("end_round")
                        self.log.debug("round not initialized, waiting for more information ... ")

        else:
            self.position = self.indexInGameAdd(self.position, 1)
            self.historyAdd("position", self.position, self.player_list[self.position])
            self.log.debug("new position (%d)" % self.position)
            self.__autoPlay()

    def __talked_muck(self):
        if not self.is_directing:
            # Test impossible, at this point the game can not be a client game
            # This method is called from muckstate and muck functions where this test is already done
            return  # pragma: no cover

        if not self.state == GAME_STATE_MUCK:
            # Test impossible, at this point the game state can not be something else than GAME_STATE_MUCK
            # This method is called from :
            # - muckstate where the game state is set to the right state
            # - muck where this test is already done
            self.log.warn("muck: game state muck expected, found %s", self.state)
            return  # pragma: no cover
        if not self.muckable_serials:
            self.showdown()
            self.endState()

    def __botEval(self, serial):
        ev = self.handEV(serial, 10000, True)

        if self.state == GAME_STATE_PRE_FLOP:
            if ev < 100:
                action = "check"
            elif ev < 500:
                action = "call"
            else:
                action = "raise"
        elif self.state == GAME_STATE_FLOP or self.state == GAME_STATE_THIRD:
            if ev < 200:
                action = "check"
            elif ev < 600:
                action = "call"
            else:
                action = "raise"
        elif self.state == GAME_STATE_TURN or self.state == GAME_STATE_FOURTH:
            if ev < 300:
                action = "check"
            elif ev < 700:
                action = "call"
            else:
                action = "raise"
        else:
            if ev < 400:
                action = "check"
            elif ev < 800:
                action = "call"
            else:
                action = "raise"

        return (action, ev)

    def __autoPlay(self):
        if not self.is_directing:
            return
        player = self.getPlayerInPosition()
        serial = player.serial

        self.log.inform("Player(%s) isBot(%s) isSitOut(%s) isAuto(%s) APPolicy(%s) foldNext(%s)" \
            % (
                serial, player.isBot(), player.isSitOut(), player.isAuto(),
                player.auto_player_policy, player.auto_player_fold_next_turn
            )
        )
        if player.isBot():
            actions = self.possibleActions(serial)
        elif (player.isSitOut() or player.isAuto()):
            if player.auto_play:
                actions = self.possibleActions(serial)
                if player.auto_player_policy == AUTO_PLAYER_POLICY_SIMPLE_BOT:
                    #
                    # A player who is sitting but not playing (sitOut) is played by a bot
                    # but should never raise.
                    #
                    actions = list(set(actions) - set(['raise']))
                elif player.auto_player_policy == AUTO_PLAYER_POLICY_FOLD:
                    actions = ["fold"]
            else:
                actions = ["fold"]
        else:
            return

        if actions:
            (desired_action, ev) = self.__botEval(serial)
            self.log.inform("__autoPlay desired action %s" % desired_action)
            while not desired_action in actions:
                self.log.inform(" autoPlay: desired action (%s) is not available %s" %(desired_action, actions))
                if desired_action == "check":
                    desired_action = "fold"
                elif desired_action == "call":
                    desired_action = "check"
                elif desired_action == "raise":
                    desired_action = "call"

            if desired_action == "fold":
                self.fold(serial)
            elif desired_action == "check":
                self.check(serial)
            elif desired_action == "call":
                self.call(serial)
            elif desired_action == "raise":
                self.callNraise(serial, 0)
            else:
                # Test impossible
                # The actions returned by the possibleActions method can not be somethin else than fold, chack, call or raise
                self.log.warn("__autoPlay: unexpected actions = %s", actions)  # pragma: no cover

    def hasLow(self):
        return "low" in self.win_orders

    def hasHigh(self):
        return "hi" in self.win_orders

    def isLow(self):
        return self.win_orders == ["low"]

    def isHigh(self):
        return self.win_orders == ["hi"]

    def isHighLow(self):
        return self.win_orders == ["hi", "low"]

    def getVariantName(self):
        return self.variant_name

    def setVariant(self, variant):
        self.__variant.load(self.url % variant)
        self.variant = variant
        self.variant_name = self.getParam("/poker/variant/@name")
        self.round_info = []
        self.round_info_backup = []
        self.win_orders = []
        for win_order in self.getParamList("/poker/variant/wins/winner/@order"):
            if win_order == "low8":
                self.win_orders.append("low")
            elif win_order == "high":
                self.win_orders.append("hi")
            else:
                self.log.inform("unexpected win order: %s for variant %s", win_order, variant)
        if not self.win_orders:
            raise UserWarning("failed to read win orders from %s" % self.__variant.path)

        board_size = 0
        hand_size = 0
        for name in self.getParamList("/poker/variant/round/@name"):
            board = self.getParamList("/poker/variant/round[@name='%s']/deal[@card='board']" % (name,))
            board_size += len(board)
            cards = self.getParamList("/poker/variant/round[@name='%s']/deal[@card='up' or @card='down']/@card" % (name,))
            hand_size += len(cards)
            position = self.getParam("/poker/variant/round[@name='%s']/position/@type" % (name,))
            info = {
                "name": name,
                "position": position,
                "board": board,
                "board_size": board_size,
                "hand_size": hand_size,
                "cards": cards,
            }
            self.round_info.append(info)
            self.round_info_backup.append(info.copy())
        self.rake = pokerrake.get_rake_instance(self)

    def resetRoundInfo(self):
        """
        The roundInfo() data structure may be altered during the round, for
        instance to cope with a lack of cards in stud7. resetRoundInfo() reset
        the roundInfo structure to match the information that was initialy
        read from the betting structure description file.
        """
        for i in xrange(len(self.round_info)):
            self.round_info[i] = self.round_info_backup[i].copy()

    def getBettingStructureName(self):
        return self.betting_structure_name

    def setBettingStructure(self, betting_structure):
        self.__betting_structure.load(self.url % betting_structure)
        self.betting_structure = betting_structure
        self.betting_structure_name = self.getParam("/bet/description")
        self.buy_in = int(self.getParam('/bet/@buy-in') or "0")
        self.max_buy_in = int(self.getParam('/bet/@max-buy-in') or sys.maxint)
        self.best_buy_in = int(self.getParam('/bet/@best-buy-in') or "0")
        self.unit = int(self.getParam('/bet/@unit'))

        self.bet_info = self.getParamProperties('/bet/variants[contains(@ids,"' + self.variant + '")]/round')
        for bet_info in self.bet_info:
            if 'cap' not in bet_info:
                bet_info["cap"] = sys.maxint
            else:
                bet_info["cap"] = int(bet_info["cap"])
            if bet_info["cap"] < 0:
                bet_info["cap"] = sys.maxint

        self.blind_info = False
        blind_info = self.getParamProperties("/bet/blind")
        if len(blind_info) > 0:
            blinds = blind_info[0]
            self.blind_info = {
                "change": 'change' in blinds and blinds["change"]
            }

            if self.blind_info["change"] != False:
                self.blind_info["frequency"] = int(blinds["frequency"])
                self.blind_info["unit"] = blinds["unit"]
                if self.blind_info["change"] == "levels":
                    self.blind_info["levels"] = self.loadTournamentLevels(self.getParam('/bet/blind/@levels'))
                elif self.blind_info["change"] == "double":
                    self.blind_info["small"] = int(blinds["small"])
                    self.blind_info["small_reference"] = self.blind_info["small"]
                    self.blind_info["big"] = int(blinds["big"])
                    self.blind_info["big_reference"] = self.blind_info["big"]
            else:
                self.blind_info["small"] = int(blinds["small"])
                self.blind_info["big"] = int(blinds["big"])

        self.ante_info = False
        ante_info = self.getParamProperties("/bet/ante")
        if len(ante_info) > 0:
            antes = ante_info[0]
            self.ante_info = {
                "change": 'change' in antes and antes["change"]
                }

            if self.ante_info["change"]:
                self.ante_info["frequency"] = int(antes["frequency"])
                self.ante_info["unit"] = antes["unit"]
                if self.ante_info["change"] == "levels":
                    self.ante_info["levels"] = self.loadTournamentLevels(self.getParam('/bet/ante/@levels'))
                elif self.ante_info["change"] == "double":
                    self.ante_info["value"] = int(antes["value"])
                    self.ante_info["value_reference"] = self.ante_info["value"]
                    self.ante_info["bring-in"] = int(antes["bring-in"])
                    self.ante_info["bring-in_reference"] = self.ante_info["bring-in"]
            else:
                self.ante_info["value"] = int(antes["value"])
                self.ante_info["bring-in"] = int(antes["bring-in"])
        self.rake = pokerrake.get_rake_instance(self)

    def loadTournamentLevels(self, levels_file):
        if levels_file not in LEVELS_CACHE:
            config = Config(self.dirs)
            config.load(levels_file)
            levels = []
            nodes = config.header.xpathEval('/levels/level')
            for node in nodes:
                level = map(lambda (key, value): (key, int(value)), config.headerNodeProperties(node).iteritems())
                levels.append(dict(level))
            config.free()
            LEVELS_CACHE[levels_file] = levels
        return LEVELS_CACHE[levels_file]

    def getBoardLength(self):
        return len(self.board.tolist(True))

    def cardsDealtThisRoundCount(self, criterion=lambda x: True):
        if not self.isRunning():
            return -1

        if self.isBlindAnteRound():
            return 0

        round_info = self.roundInfo()
        return len(filter(criterion, round_info["cards"]))

    def upCardsDealtThisRoundCount(self):
        return self.cardsDealtThisRoundCount(lambda x: x == "up")

    def downCardsDealtThisRoundCount(self):
        return self.cardsDealtThisRoundCount(lambda x: x == "down")

    def getMaxHandSize(self):
        return len(self.getParamList("/poker/variant/hand/position"))

    def getMaxBoardSize(self):
        if self.getParam("/poker/variant/@type") == "community":
            return len(self.getParamList("/poker/variant/community/position"))
        else:
            return 0

    def cardsDealt(self):
        if self.isBlindAnteRound():
            return True
        hand_size = self.roundInfo()["hand_size"]
        for player in self.playersInGame():
            if player.hand.len() != hand_size:
                return False
        return self.getBoardLength() == self.roundInfo()["board_size"]

    def dealCards(self):
        if not self.is_directing:
            return

        info = self.roundInfo()

        number_of_players = len(self.playersNotFold())

        def number_to_deal():
            return len(info["board"]) + len(info["cards"]) * number_of_players

        if number_to_deal() > len(self.deck):
            cards = info["cards"]
            cards.reverse()
            while number_to_deal() > len(self.deck):
                if "up" in cards:
                    cards.remove("up")
                elif "down" in cards:
                    cards.remove("down")
                else:
                    raise UserWarning("unable to deal %d cards" % number_to_deal())
                info["hand_size"] -= 1

                info["board"].append("board")
                info["board_size"] += 1
            cards.reverse()

        for card in info["board"]:
            self.board.add(self.deck.pop(), True)
        for card in info["cards"]:
            for player in self.playersNotFold():
                player.hand.add(self.deck.pop(), card == "up")
        if len(info["cards"]):
            for serial in self.serialsNotFold():
                self.log.debug("player %d cards: %s", serial, self.getHandAsString(serial))
        if len(info["board"]):
            self.log.debug("board: " + self.getBoardAsString())

    def __roundFinished(self, serial):
        #
        # The round finishes when there is only one player not fold ...
        #
        if self.notFoldCount() < 2:
            self.log.debug("only one player left in the game")
            return True

        #
        # ... or when all players are all-in.
        #
        if self.inGameCount() < 1:
            self.log.debug("all players are all-in")
            return True

        if self.first_betting_pass:
            if serial != self.getSerialLastToTalk():
                if self.inGameCount() < 2:
                    #
                    # If there is only one player left to talk, it is
                    # meaningless to ask for his action, unless he has
                    # something to call.
                    #
                    return self.betsEqual()
                else:
                    return False
            else:
                self.first_betting_pass = False
        return self.betsEqual()

    def moneyDistributed(self):
        return len(self.showdown_stack) > 0

    def isWinnerBecauseFold(self):
        return (self.win_condition == WON_FOLD)

    #
    # Split the pots
    #
    def distributeMoney(self):
        if self.moneyDistributed():
            self.log.inform("distributeMoney must be called only once per turn")
            return

        pot_backup = self.pot
        side_pots = self.getPots()

        serial2delta = {}
        for (serial, share) in side_pots['contributions']['total'].iteritems():
            player_dead = self.getPlayer(serial).dead
            serial2delta[serial] = -(share + player_dead)

        if self.isWinnerBecauseFold():
            serial2rake = {}
            #
            # Special and simplest case : the winner has it because
            # everyone folded. Don't bother to evaluate.
            #
            (serial,) = self.serialsNotFold()

            self.setRakedAmount(self.rake.getRake(self.getPotAmount(), self.getUncalled(), self.isTournament()))
            self.pot -= self.getRakedAmount()

            serial2rake[serial] = self.getRakedAmount()
            serial2delta[serial] += self.pot
            self.showdown_stack = [
                {
                    'type': 'game_state',
                    'player_list': self.player_list,
                    'side_pots': side_pots,
                    'pot': pot_backup,
                    'foldwin': True,
                    'serial2share': {serial: self.pot},
                    'serial2delta': serial2delta,
                    'serial2rake': serial2rake
                },
                {
                    'type': 'resolve',
                    'serial2share': {serial: pot_backup},
                    'serials': [serial],
                    'pot': pot_backup
                }
            ]
            self.log.debug("%s", pformat(self.showdown_stack))
            self.pot2money(serial)
            self.setWinners([serial])
            if not self.is_directing:
                self.updateHistoryEnd(self.winners, self.showdown_stack)
            return

        serial2side_pot = {}
        for player in self.playersNotFold():
            serial2side_pot[player.serial] = side_pots['pots'][player.side_pot_index][1]
        self.log.debug("distribute a pot of %d", self.pot)
        #
        # Keep track of the best hands (high and low) for information
        # and for the showdown.
        #
        self.serial2best = self.bestHands(self.serialsNotFold())
        #
        # Every player that received a share of the pot and the
        # amount.
        #
        serial2share = {}
        #
        # List of winners for each side of the pot (hi or low),
        # regardless of the fact that low hands matter for this
        # particular variant. Warning: a winner may show more
        # than once in these lists (when he is tie for two side pots,
        # for instance).
        #
        self.side2winners = {'hi': [], 'low': []}
        #
        # Complete showdown information, starting with the lowest side pot.
        #
        showdown_stack = []
        #
        # The chips that can't be divided evenly among winners
        #
        chips_left = 0
        #
        # While there is some money left at the table
        #
        while True:
            potential_winners = filter(lambda player: serial2side_pot[player.serial] > 0, self.playersNotFoldShowdownSorted())
            #
            # Loop ends when there is no more money, i.e. no more
            # players with a side_pot greater than 0
            #
            if len(potential_winners) == 0:
                break
            #
            # All information relevant to this distribution round
            #
            frame = {}
            #
            # This happens only for the potential winner that has the
            # highest pot (all other players are all-in but none matched
            # his bet).
            #
            # This last potential winner reaches this stage and wins not
            # because of his hand but because of the size of his stacks.
            # He only wins back what he bet.
            #
            # Let him have his money back and don't register him as a
            # winner (winners are registered in self.side2winners).
            #
            if len(potential_winners) == 1:
                winner = potential_winners[0]
                frame['type'] = 'uncalled'
                frame['serial'] = winner.serial
                frame['uncalled'] = serial2side_pot[winner.serial]
                #
                # Special case : a player folds on the turn and the only other player left in the game
                # did not bet. There is no reason for the player to fold : he forfeits a pot that
                # he may win. Nevertheless, it can happen. In this case, and only if there is at least
                # one player allin, the only other player left is awarded what looks like an uncalled
                # bet.
                # In this case the uncalled_serial is zero.
                #
                if self.uncalled_serial != 0 and winner.serial != self.uncalled_serial:
                    self.log.warn("%", pformat(self.showdown_stack))
                    raise UserWarning("distributeMoney: unexpected winner.serial != uncalled_serial / %d != %d" % (
                        winner.serial,
                        self.uncalled_serial
                    ))
                showdown_stack.insert(0, frame)
                serial2share.setdefault(winner.serial, 0)
                if self.uncalled_serial != 0 and \
                    side_pots and \
                    'last_round' in side_pots and \
                    side_pots['last_round'] >= 0:
                        if serial2side_pot[winner.serial] < self.uncalled:
                            self.log.warn("%s", pformat(self.showdown_stack))
                            raise UserWarning("serial2side_pot[winner.serial] < self.uncalled (%d != %d)" % (
                                    serial2side_pot[winner.serial],
                                    self.uncalled
                            ))
                serial2share[winner.serial] += serial2side_pot[winner.serial]
                serial2delta[winner.serial] += serial2side_pot[winner.serial]
                serial2side_pot[winner.serial] = 0
                break

            for key in (self.win_orders + ['pot', 'chips_left']):
                frame[key] = None
            frame['type'] = 'resolve'
            frame['serial2share'] = {}
            frame['serials'] = [player.serial for player in potential_winners]

            self.log.debug(
                "looking for winners with boards %s\n%s",
                self.getBoardAsString(),
                "\n".join("  => hand for player %d %s" % (player.serial, self.getHandAsString(player.serial)) for player in potential_winners)
            )
            
            #
            #
            # Ask poker-eval to figure out who the winners actually are
            #
            poker_eval = self.eval.winners(
                game=self.variant,
                pockets=[player.hand.tolist(True) for player in potential_winners],
                board=self.board.tolist(True)
            )
            #
            # Feed local variables with eval results sorted in various
            # forms to ease computing the results.
            #
            winners = []
            self.log.debug("winners:")
            for (side, indices) in poker_eval.iteritems():
                side_winners = [potential_winners[i] for i in indices]
                for winner in side_winners:
                    self.log.debug(" => player %d %s (%s)",
                        winner.serial,
                        self.bestCardsAsString(self.serial2best, winner.serial, side),
                        side
                    )
                    serial2share.setdefault(winner.serial, 0)
                    frame['serial2share'][winner.serial] = 0
                frame[side] = [winner.serial for winner in side_winners]
                self.side2winners[side] += frame[side]
                winners += side_winners

            #
            # The pot to be considered is the lowest side_pot of all
            # the winners. In other words, we must share the pot that
            # was on the table for the winner that was all-in first.
            #
            pot = min([serial2side_pot[player.serial] for player in winners])
            frame['pot'] = pot
            self.log.debug("  and share a pot of %d", pot)
            #
            # If there are no winners for the low hand (either because the
            # game is not hi/low or because there is no qualifying low
            # hand), the pot goes to the high side winner. Otherwise
            # the pot is divided equaly between hi and low winners.
            #
            # A player who scoops (wins high and low) will show twice
            # in the winners_indices list and will therefore get two shares.
            # This is why the following does not take in account the side
            # for which the winner wins.
            #
            (global_share, remainder) = self.divideChips(pot, len(poker_eval.keys()))
            chips_left += remainder
            frame['chips_left'] = remainder
            for winners_indices in poker_eval.values():
                winners = [potential_winners[i] for i in winners_indices]
                (share, remainder) = self.divideChips(global_share, len(winners))
                chips_left += remainder
                frame['chips_left'] += remainder
                for winner in winners:
                    serial2share[winner.serial] += share
                    serial2delta[winner.serial] += share
                    frame['serial2share'][winner.serial] += share
            #
            # The side pot of each winner is lowered by the amount
            # that was shared among winners. It will reduce the number
            # of potential winners (to the very least, the winner(s)
            # with the smallest side pot will be discarded).
            #
            for player in potential_winners:
                serial2side_pot[player.serial] -= pot

            showdown_stack.append(frame)

        #
        # Do not rake the chips that were uncalled
        #
        serial2rackable = serial2share.copy()
        pot_rackable = pot_backup
#
        if showdown_stack[0]['type'] == 'uncalled':
            uncalled = showdown_stack[0]
            serial2rackable[uncalled['serial']] -= uncalled['uncalled']
            pot_rackable -= uncalled['uncalled']
            if serial2rackable[uncalled['serial']] <= 0:
                del serial2rackable[uncalled['serial']]

        #
        # reset raked amount
        #
        self.setRakedAmount(self.rake.getRake(pot_rackable, 0, self.isTournament()))
        serial2rake = self.distributeRake(self.getRakedAmount(), pot_rackable, serial2rackable)

        for serial in serial2rake.keys():
            serial2share[serial] -= serial2rake[serial]
            serial2delta[serial] -= serial2rake[serial]

        for (serial, share) in serial2share.iteritems():
            self.getPlayer(serial).money += share

        #
        # The chips left go to the player next to the dealer,
        # regardless of the fact that this player folded.
        #
        if chips_left > 0:
            next_to_dealer = self.indexAdd(self.dealer, 1)
            player = self.serial2player[self.player_list[next_to_dealer]]
            player.money += chips_left
            serial2share.setdefault(player.serial, 0)
            serial2share[player.serial] += chips_left
            serial2delta[player.serial] += chips_left
            showdown_stack.insert(0, {
                'type': 'left_over',
                 'chips_left': chips_left,
                 'serial': player.serial
            })

        self.pot = 0
        #
        # For convenience, build a single list of all winners, regardless
        # of the side of the pot they won. Remove duplicates in all lists.
        #
        winners_serials = []
        for side in self.side2winners.keys():
            self.side2winners[side] = uniq(self.side2winners[side])
            winners_serials += self.side2winners[side]
        self.setWinners(uniq(winners_serials))
        showdown_stack.insert(0, {
            'type': 'game_state',
            'serial2best': self.serial2best,
            'player_list': self.player_list,
            'side_pots': side_pots,
            'pot': pot_backup,
            'serial2share': serial2share,
            'serial2rake': serial2rake,
            'serial2delta': serial2delta
        })
        self.showdown_stack = showdown_stack
        if not self.is_directing:
            self.updateHistoryEnd(self.winners, showdown_stack)
        self.log.debug("%s", pformat(self.showdown_stack))

    def divideChips(self, amount, divider):
        return (amount / divider, amount % divider)

    def dispatchMuck(self):
        if not self.is_directing:
            self.log.inform("dispatchMuck: not supposed to be called by client")
            return None

        if self.isWinnerBecauseFold():
            return ((), tuple(self.winners))

        #
        # Show the winning cards.
        # Starting left of the dealer, display player cards as if each showed
        # his hand only if the previous hand is not better (either hi or low).
        #
        showing = self.indexNotFoldAdd(self.dealer, 1)
        last_to_show = self.indexNotFoldAdd(showing, -1)
        has_low = len(self.side2winners["low"])
        best_low_value = 0x0FFFFFFF
        has_high = len(self.side2winners["hi"])
        best_hi_value = 0

        muckable = []
        to_show = []

        while True:
            player = self.serial2player[self.player_list[showing]]
            show = False

            if has_low:
                low_value = self.bestHandValue("low", player.serial)
                if low_value < best_low_value:
                    best_low_value = low_value
                    show = True

            if has_high:
                hi_value = self.bestHandValue("hi", player.serial)
                if hi_value > best_hi_value:
                    best_hi_value = hi_value
                    show = True

            #
            # This is deemed necessary because this simplistic but intuitive
            # way to show or muck cards does not take in account the recursive
            # nature of splitting a side pot. A player with a hand lower than
            # a previous hand may need to show his cards if the previous hand
            # belonged to someone who was all-in. Example: player 1 has trips,
            # player 2 has two pairs, player 3 has nothing. Player 1 is left
            # of dealer, shows and win. But player 1 was all-in, therefore
            # player 2 and player 3 compete for the remaining chips. Player 2
            # shows and win. In the end player 1 showed his hand and player 2
            # also showed his hand although he was after player 1 with a
            # weaker hand.
            #
            if player.serial in self.winners:
                show = True

            if show:
                to_show.append(player.serial)
            else:
                muckable.append(player.serial)

            if showing == last_to_show:
                break

            showing = self.indexNotFoldAdd(showing, 1)

        return (tuple(to_show), tuple(muckable))

    def showdown(self):
        self.historyAdd("showdown", self.board.copy(), self.handsMap())

    def handEV(self, serial, iterations, self_only=False):
        pocket_size = self.getMaxHandSize()
        pockets = []
        serials = self.serialsNotFold()
        if self_only:
            #
            # Pretend that the pocket cards of other players are unknown
            #
            pockets = [[PokerCards.NOCARD] * pocket_size] * len(serials)
            if serial in serials:
                my_cards = self.getPlayer(serial).hand.tolist(True)
                pockets[serials.index(serial)] = my_cards
        else:
            for pocket in [player.hand.tolist(True) for player in self.playersNotFold()]:
                if len(pocket) < pocket_size:
                    pocket.extend([PokerCards.NOCARD] * (pocket_size - len(pocket)))
                pockets.append(pocket)
        board = self.board.tolist(True)
        board_size = self.getMaxBoardSize()
        if len(board) < board_size:
            board.extend([PokerCards.NOCARD] * (board_size - len(board)))
        poker_eval = self.eval.poker_eval(
            game=self.variant,
            pockets=pockets,
            board=board,
            fill_pockets=1,
            iterations=iterations
        )
        if serial in serials:
            player_index = serials.index(serial)
            return poker_eval["eval"][player_index]["ev"]
        else:
            self.log.warn("handEV: player %d is not holding cards in the hand", serial)
            return None

    def readableHandValueLong(self, side, value, cards):
        cards = self.eval.card2string(cards)
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return _("The wheel")
                else:
                    return ", ".join(card[0] for card in cards)
            else:
                return _("High card %(card)s") % {'card': _(letter2name[cards[0][0]])}
        elif value == "OnePair":
            return _("A pair of %(card)s") % {
                'card': _(letter2names[cards[0][0]])
            } + _(", %(card)s kicker") % {
                'card': _(letter2name[cards[2][0]])
            }
        elif value == "TwoPair":
            return _("Two pairs %(card1)s and %(card2)s") % {
                'card1': _(letter2names[cards[0][0]]),
                'card2': _(letter2names[cards[2][0]])
            } + _(", %(card)s kicker") % {
                'card': _(letter2name[cards[4][0]])
            }
        elif value == "Trips":
            return _("Three of a kind %(card)s") % {
                'card': _(letter2names[cards[0][0]])
            } + _(", %(card)s kicker") % {
                'card': _(letter2name[cards[3][0]])
            }
        elif value == "Straight":
            return _("Straight %(card1)s to %(card2)s") % {
                'card1': _(letter2name[cards[0][0]]),
                'card2': _(letter2name[cards[4][0]])
            }
        elif value == "Flush":
            return _("Flush %(card)s high") % {
                'card': _(letter2name[cards[0][0]])
            }
        elif value == "FlHouse":
            return _("%(card1)ss full of %(card2)ss") % {
                'card1': _(letter2name[cards[0][0]]),
                'card2': _(letter2name[cards[3][0]])
            }
        elif value == "Quads":
            return _("Four of a kind %(card)s") % {
                'card': _(letter2names[cards[0][0]])
            } + _(", %(card)s kicker") % {
                'card': _(letter2name[cards[4][0]])
            }
        elif value == "StFlush":
            if letter2name[cards[0][0]] == 'Ace':
                return _("Royal flush")
            else:
                return _("Straight flush %(card)s high") % {'card': _(letter2name[cards[0][0]])}
        return value

    def readableHandValueShort(self, side, value, cards):
        cards = self.eval.card2string(cards)
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return _("The wheel")
                else:
                    return ", ".join(card[0] for card in cards)
            else:
                return _("High card %(card)s") % {'card': _(letter2name[cards[0][0]])}
        elif value == "OnePair":
            return _("Pair of %(card)s") % {'card': _(letter2names[cards[0][0]])}
        elif value == "TwoPair":
            return _("Pairs of %(card1)s and %(card2)s") % {
                'card1': _(letter2names[cards[0][0]]),
                'card2': _(letter2names[cards[2][0]])
            }
        elif value == "Trips":
            return _("Trips %(card)s") % {
                'card': _(letter2names[cards[0][0]])
            }
        elif value == "Straight":
            return _("Straight %(card)s high") % {
                'card': _(letter2name[cards[0][0]])
            }
        elif value == "Flush":
            return _("Flush %(card)s high") % {
                'card': _(letter2name[cards[0][0]])
            }
        elif value == "FlHouse":
            return _("%(card1)ss full of %(card2)ss") % {
                'card1': _(letter2name[cards[0][0]]),
                'card2': _(letter2name[cards[3][0]])
            }
        elif value == "Quads":
            return _("Quads %(card)s") % {
                'card': _(letter2names[cards[0][0]])
            } + ", %(card)s kicker" % {
                'card': _(letter2name[cards[4][0]])
            }
        elif value == "StFlush":
            if letter2name[cards[0][0]] == 'Ace':
                return _("Royal flush")
            else:
                return _("Straight flush")
        return value

    def bestHands(self, serials):
        results = {}
        for serial in serials:
            #
            # Cannot figure out the best hand for a player with
            # a placeholder.
            #
            if self.serial2player[serial].hand.hasCard(PokerCards.NOCARD):
                continue
            result = {}
            for side in self.win_orders:
                result[side] = self.bestHand(side, serial)
            results[serial] = result
        return results

    def bestCardsAsString(self, bests, serial, side):
        return " ".join(self.eval.card2string(bests[serial][side][1][1:]))

    def bestHand(self, side, serial):
        if self.variant == "omaha" or self.variant == "omaha8":
            hand = self.serial2player[serial].hand.tolist(True)
            board = self.board.tolist(True)
        else:
            hand = self.serial2player[serial].hand.tolist(True) + self.board.tolist(True)
            board = []
        return self.eval.best(side, hand, board)

    def bestHandValue(self, side, serial):
        return self.bestHand(side, serial)[0]

    def bestHandCards(self, side, serial):
        return self.bestHand(side, serial)[1]

    def readablePlayerBestHands(self, serial):
        results = []
        if self.hasHigh():
            results.append(self.readablePlayerBestHand('hi', serial))
        if self.hasLow():
            results.append(self.readablePlayerBestHand('low', serial))
        return "\n".join(results)

    def readablePlayerBestHand(self, side, serial):
        cards = self.bestHandCards(side, serial)
        result = self.readableHandValueLong(side, cards[0], cards[1:])
        result += ": " + ", ".join(self.eval.card2string(cards[1:]))
        return result

    def cards2string(self, cards):
        return " ".join(self.eval.card2string(cards.tolist(True)))

    def getHandAsString(self, serial):
        return self.cards2string(self.serial2player[serial].hand)

    def getBoardAsString(self):
        return self.cards2string(self.board)

    def betsNull(self):
        if self.isRunning():
            return sum([player.bet for player in self.playersNotFold()]) == 0
        else:
            return False

    def setWinners(self, serials):
        self.log.debug("player(s) %s win", serials)
        self.winners = serials

    def bet2pot(self, serial=0, dead_money=False):
        if serial == 0:
            serials = self.player_list
        else:
            serials = [serial]
        for serial in serials:
            player = self.serial2player[serial]
            bet = player.bet
            self.pot += bet
            if dead_money:
                player.dead += bet
            player.bet = 0
            self.runCallbacks("bet2pot", serial, bet)

    def money2bet(self, serial, amount, dead_money=False):
        player = self.serial2player[serial]

        if amount > player.money:
            self.log.inform("money2bet: %d > %d", amount, player.money)
            amount = player.money
        player.money -= amount
        player.bet += amount
        self.runCallbacks("money2bet", serial, amount)
        if dead_money:
            self.side_pots['building'] += amount
        else:
            self.__updateUncalled()
            self.updatePots(serial, amount)
        if player.money == 0:
            self.historyAdd("all-in", serial)
            player.all_in = True

    def __updateUncalled(self):
        highest_bet = 0
        highest_bet_players_count = 0
        for player in self.playersNotFold():
            if player.bet > highest_bet:
                highest_bet = player.bet
                highest_bet_players_count = 1
            elif player.bet == highest_bet:
                highest_bet_players_count += 1

        if highest_bet_players_count == 0:
            raise UserWarning("there should be at least one player in the game")  # pragma: no cover

        if highest_bet_players_count > 1:
            self.uncalled = 0
            self.uncalled_serial = 0
            return

        self.uncalled = highest_bet
        for player in self.playersNotFold():
            if player.bet != highest_bet and highest_bet - player.bet < self.uncalled:
                self.uncalled = highest_bet - player.bet
            if player.bet == highest_bet:
                self.uncalled_serial = player.serial

    def updatePots(self, serial, amount):
        pot_index = len(self.side_pots['pots']) - 1
        self.side_pots['building'] += amount
        contributions = self.side_pots['contributions']
        contributions['total'].setdefault(serial, 0)
        contributions['total'][serial] += amount
        round_contributions = contributions[self.current_round]
        round_contributions.setdefault(pot_index, {})
        pot_contributions = round_contributions[pot_index]
        pot_contributions.setdefault(serial, 0)
        pot_contributions[serial] += amount

    def playersInPotCount(self, side_pots):
        pot_index = len(side_pots['pots']) - 1

        if side_pots['last_round'] not in side_pots['contributions']:
            return 0
        contributions = side_pots['contributions'][side_pots['last_round']]
        if pot_index not in contributions:
            return 0
        return len(contributions[pot_index])

    def isSingleUncalledBet(self, side_pots):
        return self.playersInPotCount(side_pots) == 1

    def getUncalled(self):
        return self.uncalled

    def getUncalledSerial(self):
        return self.uncalled_serial

    def getPotAmount(self):
        if self.isRunning():
            return self.pot
        else:
            if self.moneyDistributed():
                return self.showdown_stack[0]['pot']
            else:
                return self.pot

    def pot2money(self, serial):
        player = self.serial2player[serial]
        player.money += self.pot
        self.pot = 0

    def highestBetNotFold(self):
        return max([player.bet for player in self.playersNotFold()])

    def highestBetInGame(self):
        return max([player.bet for player in self.playersInGame()])

    def betsEqual(self):
        if self.notFoldCount() > 1 and self.inGameCount() > 0:
            #
            # If a player that is all-in placed a bet that is higher
            # than any of the bets of the players still in game, the
            # bets are not equal.
            #
            if self.highestBetNotFold() > self.highestBetInGame():
                return False
            #
            # If one of the players still in game placed a bet that
            # is different from the others, the bets are not equal.
            #
            players = self.playersInGame()
            bet = players[0].bet
            for player in players:
                player_bet = player.bet
                if bet != player_bet:
                    return False
        return True

    def __makeSidePots(self):
        amount_index = 0
        total_index = 1
        last_pot_index = -1
        round_contributions = self.side_pots['contributions'][self.current_round]
        pots = self.side_pots['pots']
        pots[last_pot_index][amount_index] += self.side_pots['building']  # amount
        pots[last_pot_index][total_index] += self.side_pots['building']  # total
        self.side_pots['building'] = 0
        current_pot_index = len(pots) - 1
        players = filter(lambda player: player.side_pot_index == current_pot_index, self.playersAllIn())
        if not players:
            return
        players.sort(key=lambda i: i.bet)
        for player in players:
            pot_contributions = round_contributions[len(pots) - 1]
            if player.serial not in pot_contributions:
                #
                # This may happen if two players are all in for exactly
                # the same amount.
                #
                continue
            if len(pot_contributions) == 1:
                #
                # This may happen when a player goes all in and
                # has more chips than all other players
                #
                break
            new_pot_contributions = {}
            pot = pots[last_pot_index]
            new_pot = [0, 0]
            new_pot_index = len(pots)
            contribution = pot_contributions[player.serial]
            for serial in pot_contributions.keys():
                other_contribution = pot_contributions[serial]
                pot_contributions[serial] = min(contribution, other_contribution)
                remainder = other_contribution - pot_contributions[serial]
                pot[amount_index] -= remainder
                pot[total_index] -= remainder
                other_player = self.getPlayer(serial)
                if other_contribution > contribution:
                    new_pot_contributions[serial] = remainder
                    new_pot[amount_index] += remainder
                    other_player.side_pot_index = new_pot_index
                elif (other_contribution == contribution and
                       not other_player.isAllIn()):
                    other_player.side_pot_index = new_pot_index
            round_contributions[new_pot_index] = new_pot_contributions
            new_pot[total_index] = new_pot[amount_index] + pot[total_index]
            pots.append(new_pot)

    def getPots(self):
        return self.side_pots

    def getSidePotTotal(self):
        return self.side_pots['pots'][-1][1]

    def getLatestPotContributions(self):
        contributions = self.side_pots['contributions']
        last_round = max(filter(lambda x: x != 'total', contributions.keys()))
        return contributions[last_round]

    def indexInGameAdd(self, position, increment):
        return self.playerListIndexAdd(position, increment, PokerPlayer.isInGame)

    def indexNotFoldAdd(self, position, increment):
        return self.playerListIndexAdd(position, increment, PokerPlayer.isNotFold)

    def indexAdd(self, position, increment):
        return self.playerListIndexAdd(position, increment, lambda x: True)

    #
    # Increment the "index" (relative to self.player_list knowing
    # that self.player_list is not modified during a turn) for a
    # total of "increment", skipping the players for which "predicate"
    # is false.
    #
    def playerListIndexAdd(self, index, increment, predicate):
        round_trip = range(0, len(self.player_list)) \
            if increment >= 0 \
            else range(len(self.player_list), 0, -1)

        player_list_ordered = [(x + index) % len(self.player_list) for x in round_trip]
        player_list_filtered = [p for p in player_list_ordered if predicate(self.serial2player[self.player_list[p]])]

        # If the player itself did not succeed in the predicate test, he is not
        # in the player_list_filtered --> his index is now occupied by another
        # player. instead of recalculating, we can simply subtract the (now missing)
        # position from the increment.
        # The absolute value is used for the increment, since we reversed the order already
        # if the value is negative
        increment = abs(increment) \
            if predicate(self.serial2player[self.player_list[index]]) \
            else abs(increment) - 1

        return player_list_filtered[increment % len(player_list_filtered)]

    def getSerialDealer(self):
        return self.player_list[self.dealer]

    def getSerialInPosition(self):
        if self.position >= 0:
            return self.player_list[self.position]
        else:
            return 0

    def getSerialLastToTalk(self):
        return self.player_list[self.last_to_talk]

    def getPlayerDealer(self):
        return self.serial2player[self.player_list[self.dealer]]

    def getPlayerInPosition(self):
        return self.serial2player[self.player_list[self.position]]

    def getPlayerLastToTalk(self):
        return self.serial2player[self.player_list[self.last_to_talk]]

    def disconnectedCount(self):
        return len(self.serialsDisconnected())

    def serialsDisconnected(self):
        return [s for s, p in self.serial2player.iteritems() if p.isDisconnected()]

    def playersDisconnected(self):
        return [p for p in self.serial2player.itervalues() if p.isDisconnected()]

    def connectedCount(self):
        return len(self.serialsConnected())

    def serialsConnected(self):
        return [s for s, p in self.serial2player.iteritems() if p.isConnected()]

    def playersConnected(self):
        return [p for p in self.serial2player.itervalues() if p.isConnected()]

    def sitOutCount(self):
        return len(self.serialsSitOut())

    def serialsSitOut(self):
        return [s for s, p in self.serial2player.iteritems() if p.isSitOut()]

    def playersSitOut(self):
        return [p for p in self.serial2player.itervalues() if p.isSitOut()]

    def brokeCount(self):
        return len(self.serialsBroke())

    def serialsBroke(self):
        return [s for s in self.serial2player.iterkeys() if self.isBroke(s)]

    def playersBroke(self):
        return [p for s, p in self.serial2player.iteritems() if self.isBroke(s)]

    def sitCount(self):
        return len(self.serialsSit())

    def serialsSit(self):
        return [s for s, p in self.serial2player.iteritems() if p.isSit()]

    def playersSit(self):
        return [p for p in self.serial2player.itervalues() if p.isSit()]

    def notPlayingCount(self):
        if not self.isRunning():
            return len(self.serial2player)
        return len(self.serialsNotPlaying())

    def serialsNotPlaying(self):
        if not self.isRunning():
            return self.serial2player.keys()
        return [s for s in self.serial2player.iterkeys() if s not in self.player_list]

    def playersNotPlaying(self):
        if not self.isRunning():
            return self.serial2player.values()
        return [p for s, p in self.serial2player.iteritems() if s not in self.player_list]

    def playingCount(self):
        if not self.isRunning():
            return 0
        return len(self.player_list)

    def serialsPlaying(self):
        if not self.isRunning():
            return []
        return [s for s in self.serial2player.iterkeys() if s in self.player_list]

    def playersPlaying(self):
        if not self.isRunning():
            return []
        return [p for s, p in self.serial2player.iteritems() if s in self.player_list]

    def allCount(self):
        return len(self.serial2player)

    def serialsAllSorted(self):
        if self.dealer < 0 or self.dealer >= len(self.player_list):
            player_list = self.serial2player.keys()
            player_list.sort()
            return player_list
        else:
            #
            # The list of serials, sort from worst position to best
            # position (i.e. the dealer)
            #
            player_list = self.serial2player.keys()
            player_list.sort(key=lambda i: self.serial2player[i].seat)
            #
            # The dealer is at the beginning of the list, followed by
            # all the players that would be dealers if he left, in order.
            #
            dealers = self.player_list[self.dealer:] + self.player_list[:self.dealer]
            #
            # If the dealer left, switch to the next one
            #
            while len(dealers) > 0 and dealers[0] not in player_list:
                dealers.pop(0)
            #
            # If at least one player that participated in the last
            # hand is still registered in the game, it is the dealer.
            # We use him as a reference point of the best position in
            # game.
            #
            if len(dealers) > 0:
                dealer_index = player_list.index(dealers[0])
                player_list = player_list[dealer_index:] + player_list[:dealer_index]
                player_list.append(player_list.pop(0))
            return player_list

    def serialsAll(self):
        return self.serial2player.keys()

    def playersAll(self):
        return self.serial2player.values()

    def inGameCount(self):
        return len(self.serialsInGame())

    def serialsInGame(self):
        return [s for s, p in self.serial2player.iteritems() if s in self.player_list and p.isInGame()]

    def playersInGame(self):
        return [p for s, p in self.serial2player.iteritems() if s in self.player_list and p.isInGame()]

    def allInCount(self):
        return len(self.serialsAllIn())

    def serialsAllIn(self):
        return filter(lambda x: self.serial2player[x].isAllIn(), self.player_list)

    def playersAllIn(self):
        return [self.serial2player[serial] for serial in self.serialsAllIn()]

    def serialsNotFoldShowdownSorted(self):
        next_to_dealer = self.indexAdd(self.dealer, 1)
        player_list = self.player_list[next_to_dealer:] + self.player_list[:next_to_dealer]
        return filter(lambda x: not self.serial2player[x].isFold(), player_list)

    def playersNotFoldShowdownSorted(self):
        return [self.serial2player[serial] for serial in self.serialsNotFoldShowdownSorted()]

    def notFoldCount(self):
        return len(self.serialsNotFold())

    def serialsNotFold(self):
        return [serial for serial in self.player_list if not self.serial2player[serial].isFold()]

    def playersNotFold(self):
        return [self.serial2player[serial] for serial in self.serialsNotFold()]

    def playersWinner(self):
        return map(lambda serial: self.serial2player[serial], self.winners)

    def isGameEndInformationValid(self):
        #
        # Only relevant for a game that has ended and for which we want to know
        # if all players involved in the last hand are still seated.
        #
        if self.state != GAME_STATE_END or len(self.winners) <= 0:
            return False
        if filter(lambda serial: serial not in self.serial2player, self.winners):
            return False
        return True

    #
    # Game Parameters.
    #
    def roundCap(self):
        if self.isRunning():
            return self.betInfo()["cap"]
        return 0

    def betLimits(self, serial):
        if not self.isRunning():
            return 0
        info = self.betInfo()
        highest_bet = self.highestBetNotFold()
        player = self.serial2player[serial]
        money = player.money
        bet = player.bet
        to_call = highest_bet - bet
        if self.round_cap_left <= 0:
            return (0, 0, to_call)
        #
        # Figure out the theorical max/min bet, regarless of the
        # player[serial] bet/money status
        #
        if 'fixed' in info:
            fixed = int(info["fixed"])
            (min_bet, max_bet) = (fixed, fixed)
        elif 'pow_level' in info:
            fixed = int(info["pow_level"]) * pow(2, self.getLevel() - 1)
            (min_bet, max_bet) = (fixed, fixed)
        else:
            if 'min' in info:
                if info["min"] == "big":
                    min_bet = self.bigBlind()
                else:
                    min_bet = int(info["min"])
            elif 'min_pow_level' in info:
                min_bet = int(info["min_pow_level"]) * pow(2, self.getLevel() - 1)
            else:
                min_bet = 0

            min_bet = max(min_bet, self.last_bet)

            if 'max' in info:
                if re.match("[0-9]+$", info["max"]):
                    max_bet = int(info["max"])
                elif info["max"] == "pot":
                    max_bet = max(self.potAndBetsAmount() + to_call, min_bet)
            else:
                max_bet = money
        #
        # A player can't bet more than he has
        #
        min_bet = min(money, min_bet + to_call)
        max_bet = min(money, max_bet + to_call)
        return (min_bet, max_bet, to_call)

    def potAndBetsAmount(self):
        pot = self.pot
        for player in self.playersPlaying():
            pot += player.bet
        return pot

    def autoBlindAnte(self, serial):
        self.getPlayer(serial).auto_blind_ante = True
        if self.isBlindAnteRound() and self.getSerialInPosition() == serial:
            self.autoPayBlindAnte()

    def noAutoBlindAnte(self, serial):
        self.getPlayer(serial).auto_blind_ante = False

    def autoPlay(self, serial, auto_play):
        self.getPlayer(serial).auto_play = auto_play

    def autoMuck(self, serial, auto_muck):
        self.getPlayer(serial).auto_muck = auto_muck

    def payBuyIn(self, serial, amount):
        if not self.isTournament() and amount > self.maxBuyIn():
            self.log.inform("payBuyIn: maximum buy in is %d and %d is too much", self.maxBuyIn(), amount)
            return False
        player = self.getPlayer(serial)
        player.money = amount
        if self.isTournament() or player.money >= self.buyIn():
            player.buy_in_payed = True
            return True
        else:
            self.log.inform("payBuyIn: minimum buy in is %d but %d is not enough", self.buyIn(), player.money)
            return False

    def rebuy(self, serial, amount):
        player = self.getPlayer(serial)
        if not player:
            return False
        if player.money + amount + player.rebuy > self.maxBuyIn():
            return False
        if self.isPlaying(serial):
            player.rebuy += amount
        else:
            player.money += amount
        return True

    def buyIn(self):
        return self.buy_in

    def maxBuyIn(self):
        return self.max_buy_in

    def bestBuyIn(self):
        return self.best_buy_in

    def getParamList(self, name):
        if name[:4] == "/bet":
            return self.__betting_structure.headerGetList(name)
        else:
            return self.__variant.headerGetList(name)

    def getParam(self, name):
        if name[:4] == "/bet":
            return self.__betting_structure.headerGet(name)
        else:
            return self.__variant.headerGet(name)

    def getParamProperties(self, name):
        if name[:4] == "/bet":
            return self.__betting_structure.headerGetProperties(name)
        else:
            return self.__variant.headerGetProperties(name)

    def full(self):
        return self.allCount() == self.max_players

    def empty(self):
        return self.allCount() == 0

    def changeState(self, state):
        self.log.debug("changing state %s => %s", self.state, state)
        self.state = state

    def isRunning(self):
        return not (self.isEndOrNull() or self.state == GAME_STATE_MUCK)

    def isEndOrNull(self):
        return self.state == GAME_STATE_NULL or self.state == GAME_STATE_END

    def registerCallback(self, callback):
        if not callback in self.callbacks:
            self.callbacks.append(callback)

    def unregisterCallback(self, callback):
        self.callbacks.remove(callback)

    def runCallbacks(self, *args):
        for callback in self.callbacks:
            callback(self.id, *args)

    def historyAddNoDuplicate(self, *args):
        if len(self.turn_history) < 1 or self.turn_history[-1] != args:
            self.historyAdd(*args)
        else:
            self.log.debug("ignore duplicate history event %s", args)

    def historyAdd(self, *args):
        self.runCallbacks(*args)
        self.turn_history.append(args)

    def updateHistoryEnd(self, winners, showdown_stack):
        for index in range(-1, -len(self.turn_history), -1):
            if self.turn_history and self.turn_history[index][0] == "end":
                self.turn_history[index] = ("end", winners, showdown_stack)
                break

    def historyGet(self):
        return self.turn_history
    
    
    def historyCanBeReduced(self):
        return bool(not self.turn_history_is_reduced and find(PokerGame._historyFinalEvent,self.turn_history))
     
    def historyReduce(self):
        if self.historyCanBeReduced():
            self.turn_history = PokerGame._historyReduce(self.turn_history,self.moneyMap())
            self.turn_history_is_reduced = True
        else:
            self.log.inform("History cannot be reduced.")
        
    @staticmethod
    def _historyFinalEvent(event):
        return event[0] in ("showdown","muck") or (event[0]=="round" and event[1] != GAME_STATE_BLIND_ANTE)
    
    @staticmethod
    def _historyReduce(turn_history,money_map,in_place=False):
        player_list_index = 7
        serial2chips_index = 9
        
        if not in_place: turn_history = deepcopy(turn_history)
            
        game_event = None
        player_list_new = None
        #
        # parse events
        remove_indexes = []
        sitouts_for_player = defaultdict(list)
        sits_for_player = defaultdict(list)
        index = 0
        for index,event in enumerate(turn_history):
            event_type = event[0]
            if PokerGame._historyFinalEvent(event):
                break
            elif event_type == 'game':
                game_event = turn_history[index]
            elif event_type == 'sit':
                remove_indexes.append(index)
                sits_for_player[event[1]].append(index)
            elif event_type in ('blind_request','ante_request'):
                remove_indexes.append(index)
            elif event_type in ('sitOut','wait_blind'):
                remove_indexes.append(index)
                sitouts_for_player[event[1]].append(index)
            elif event_type == 'wait_for':
                remove_indexes.append(index)
                sitouts_for_player[event[1]].append(index)
            elif event_type == 'player_list':
                remove_indexes.append(index)
                player_list_new = event[1]
        #
        # recreate playerlist.
        # either use the player list, if their is some
        if player_list_new is not None:
            for serial in set(game_event[player_list_index]) - set(player_list_new):
                del game_event[serial2chips_index][serial]
            for serial in set(player_list_new) - set(game_event[player_list_index]):
                game_event[serial2chips_index][serial] = money_map[serial]
            game_event[player_list_index][:] = player_list_new
        #
        # recreate and mark positions if needed
        for p_index in range(0,index):
            if (
                not turn_history[p_index][0] == "position" or 
                not turn_history[p_index][1] >= 0 
                or p_index in remove_indexes
            ):
                continue
            event_type, position, serial = turn_history[p_index]
            position_reduced = game_event[player_list_index].index(serial) \
                if serial is not None and serial in game_event[player_list_index] \
                else None
            if position == position_reduced:
                pass # no need to replace if it's already equal
            elif position_reduced is not None and position: 
                turn_history[p_index] = (event_type, position_reduced, serial)
            else:
                remove_indexes.append(p_index)
        #
        # actually delete all obsolete elements
        for index in sorted(remove_indexes,reverse=True):
            del turn_history[index]
        
        if not in_place:
            return turn_history


class PokerGameServer(PokerGame):
    def __init__(self, url, dirs):
        PokerGame.__init__(self, url, True, dirs)  # is_directing == True


class PokerGameClient(PokerGame):
    def __init__(self, url, dirs):
        PokerGame.__init__(self, url, False, dirs)  # is_directing == False
