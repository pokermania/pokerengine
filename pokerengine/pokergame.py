#
# Copyright (C) 2004 Mekensleep
#
# Mekensleep
# 24 rue vieille du temple
# 75004 Paris
#       licensing@mekensleep.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#  Loic Dachary <loic@gnu.org>
#  Henry Precheur <henry@precheur.org>
#
from string import split, join, lower
from pprint import pprint
import re
import struct

from pokereval import PokerEval

from pokerengine.pokercards import *
from pokerengine.pokerchips import PokerChips
from pokerengine.config import Config

ABSOLUTE_MAX_PLAYERS = 10

class PokerRandom:

  def __init__(self):
    self._file = open("/dev/urandom", 'r')

  def __del__(self):
    self._file.close()
      
  def random(self):
    lsize = struct.calcsize('l')
    return abs(struct.unpack('l', self._file.read(lsize))[0])/(0.+(~(1L<<(8*lsize))))

  def shuffle(self, deck):
    for i in xrange(len(deck)-1, 0, -1):
        # pick an element in deck[:i+1] with which to exchange deck[i]
        j = int(self.random() * (i+1))
        deck[i], deck[j] = deck[j], deck[i]

class PokerPlayer:
    def __init__(self, serial, game):
        self.serial = serial
        self.name = "noname"
        self.game = game
        self.fold = False
        self.remove_next_turn = False
        self.sit_out = True
        self.sit_out_next_turn = False
        self.bot = False
        self.auto = False
        self.auto_blind_ante = False
        self.wait_for = False # False, "late", "big"
        self.missed_blind = "n/a" # None, "n/a", "big", "small"
        self.blind = "late" # True, None, "late", "big", "small", "big_and_dead"
        self.buy_in_payed = False
        self.ante = False
        self.side_pot_index = 0
        self.all_in = False
        self.seat = None
        self.hand = PokerCards()
        self.money = False
        self.rebuy = 0
        self.bet = False
        self.dead = False
        self.talked_once = False

    def copy(self):
        other = PokerPlayer(self.serial, self.game)
        other.name = self.name
        other.fold = self.fold
        other.remove_next_turn = self.remove_next_turn
        other.sit_out = self.sit_out
        other.sit_out_next_turn = self.sit_out_next_turn
        other.bot = self.bot
        other.auto = self.auto
        other.auto_blind_ante = self.auto_blind_ante
        other.wait_for = self.wait_for
        other.missed_blind = self.missed_blind
        other.blind = self.blind
        other.buy_in_payed = self.buy_in_payed
        other.ante = self.ante
        other.side_pot_index = self.side_pot_index
        other.all_in = self.all_in
        other.seat = self.seat
        other.hand = self.hand.copy()
        other.money = self.money and self.money.copy()
        other.rebuy = self.rebuy
        other.bet = self.bet and self.bet.copy()
        other.dead = self.pot and self.dead.copy()
        other.talked_once = self.talked_once
        return other

    def __str__(self):
        return "serial = %d, name= %s, fold = %s, remove_next_turn = %s, sit_out = %s, sit_out_next_turn = %s, bot = %s, auto = %s, auto_blind_ante = %s, wait_for = %s, missed_blind = %s, blind = %s, buy_in_payed = %s, ante = %s, all_in = %s, side_pot_index = %d, seat = %d, hand = %s, money = %s, rebuy = %d, bet = %s, dead = %s, talked_once = %s" % (self.serial, self.name, self.fold, self.remove_next_turn, self.sit_out, self.sit_out_next_turn, self.bot, self.auto, self.auto_blind_ante, self.wait_for, self.missed_blind, self.blind, self.buy_in_payed, self.ante, self.all_in, self.side_pot_index, self.seat, self.hand, self.money, self.rebuy, self.bet, self.dead, self.talked_once)

    def beginTurn(self):
        self.bet.reset()
        self.dead.reset()
        self.fold = False
        self.hand = PokerCards()
        self.side_pot_index = 0
        self.all_in = False
        self.blind = None
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

    def isBot(self):
        return self.bot

    def isAuto(self):
        return self.auto

    def isAutoBlindAnte(self):
        return self.auto_blind_ante

    def isWaitForBlind(self):
        return self.wait_for

    def isMissedBlind(self):
        return self.missed_blind

    def isBlind(self):
        return self.blind

    def isBuyInPayed(self):
        return self.buy_in_payed

class PokerGame:
    def __init__(self, url, is_directing, dirs):
        self.id = 0
        self.name = "noname"
        self.__variant = Config(dirs)
        self.__betting_structure = Config(dirs)
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
        self.chips_values = False
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
            "frequency": 180 # seconds
            }
        
        self.is_directing = is_directing
        
        self.prefix = ""
        self.verbose = 0
        self.callbacks = []

        self.first_turn = True
        
        self.eval = PokerEval()
        if self.is_directing:
          self.shuffler = PokerRandom()
        self.reset()
#        print "__init__ PokerGame %s" % self

    def reset(self):
        self.state = "null"
        self.current_round = -2
        self.serial2player = {}
        self.player_list = []
        self.resetSeatsLeft()
        self.dealer = -1
        self.dealer_seat = -1
        self.position = 0
        self.last_to_talk = -1
        self.pot = False
        self.board = PokerCards()
        self.round_cap_left = 0
        self.last_bet = 0
        self.winners = []
        self.side2winners = {}
        self.winner2share = {}
        self.serial2best = {}
        self.showdown_stack = []
        self.side_pots = {}
        self.first_betting_pass = True
        self.turn_history = []
        self.level = 0

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False
        
    def setMaxPlayers(self, max_players):
        self.max_players = max_players
        self.resetSeatsLeft()

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
            self.seats_left = [0, 2, 4, 5, 7, 9]
        elif self.max_players == 7:
            self.seats_left = [0, 2, 3, 5, 6, 8, 9]
        elif self.max_players == 8:
            self.seats_left = [1, 2, 3, 4, 5, 6, 7, 8]
        elif self.max_players == 9:
            self.seats_left = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        elif self.max_players == 10:
            self.seats_left = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.seats_all = self.seats_left[:]

    def seatsCount(self):
        return len(self.seats_all)
    
    def canComeBack(self, serial):
        return ( self.serial2player.has_key(serial) and
                 ( self.serial2player[serial].isDisconnected() or
                   self.serial2player[serial].isAuto() ) )
        
    def canAddPlayer(self, serial):
        if len(self.seats_left) < 1:
            self.error("no seats left for player %d" % serial)
            return False
        else:
            return self.is_open

    def isInPosition(self, serial):
        return self.isPlaying() and self.getSerialInPosition() == serial
      
    def isPlaying(self, serial):
        return ( self.isRunning() and
                 self.serial2player.has_key(serial) and
                 serial in self.player_list )

    def isInGame(self, serial):
        return ( self.isRunning() and
                 self.serial2player.has_key(serial) and
                 serial in self.serialsInGame() )

    def isSeated(self, serial):
        return serial in self.serial2player.keys()

    def isSit(self, serial):
        return ( self.serial2player.has_key(serial) and
                 self.serial2player[serial].isSit() )
        
    def isSitOut(self, serial):
        return ( self.serial2player.has_key(serial) and
                 self.serial2player[serial].isSitOut() )
        
    def sitOutNextTurn(self, serial):
        player = self.serial2player[serial]
        if ( self.isPlaying(serial) and
             not ( self.isBlindAnteRound() and
                   self.getSerialInPosition() == serial ) ):
            player.sit_out_next_turn = True
            return False
        else:
            return self.sitOut(serial)
        
    def sitOut(self, serial):
        player = self.serial2player[serial]
        if player.isSitOut():
            return False
        if self.isPlaying(serial):
            self.historyAdd("sitOut", serial)
        player.sit_out = True
        player.sit_out_next_turn = False
        player.wait_for = False
        if self.is_directing and self.isBlindAnteRound():
            player.blind = None
            self.updateBlinds()
            if self.getSerialInPosition() == serial:
                self.__talkedBlindAnte()
            else:
                self.message("sitOut for player %d while paying the blinds although not in position", serial)
        if self.sitCount() < 2:
            self.first_turn = True
            self.dealer_seat = self.playersAll()[0].seat
        return True

    def canceled(self, serial, amount):
        if self.isBlindAnteRound():
            self.endState()
            if self.sitCount() != 1:
                self.error("%d players sit, expected exactly one" % self.sitCount())
            elif amount > 0:
                self.bet2pot()
                if self.pot.toint() != amount:
                    self.error("pot contains %d, expected %d" % ( self.pot.toint(), amount ))
                else:
                    self.pot2money(serial)
        else:
            self.error("canceled unexpected while in state %s (ignored)" % self.state)
        
    def returnBlindAnte(self):
        self.historyAdd("canceled", serial, pot)
        serials = self.serialsSit()
        if serials:
            serial = serials[0]
            self.bet2pot()
            pot = self.pot.toint()
            self.pot2money(serial)
        else:
            serial = 0
            pot = 0
            
    def sit(self, serial):
        player = self.serial2player[serial]
        if not player.isBuyInPayed() or self.isBroke(serial):
            if self.verbose: self.error("sit: refuse to sit player %d because buy in == %s or broke == %s" % ( serial, player.buy_in_payed, self.isBroke(serial) ))
            return False
        player.sit_out_next_turn = False
        player.sit_out = False
        if player.wait_for == "big":
            player.wait_for = False
        player.auto = False
        if self.sitCount() < 2:
            self.dealer_seat = player.seat
        return True

    def getSerialByNameNoCase(self, name):
        name = lower(name)
        for player in self.playersAll():
            if lower(player.name) == name:
                return player.serial
        return 0

    def setPosition(self, position):
        if not self.isRunning():
            self.error("changing position while the game is not running has no effect")
        self.position = position
        
    def setDealer(self, seat):
        if self.isRunning():
            self.error("cannot change the dealer during the turn")
        self.dealer_seat = seat
        
    def getPlayer(self, serial):
        return self.serial2player.get(serial, None)

    def getPlayerMoney(self, serial):
        player = self.getPlayer(serial)
        if player:
            return player.money.toint() + player.rebuy
        
    def getSitOut(self, serial):
        return self.serial2player[serial].sit_out
        
    def comeBack(self, serial):
        if self.canComeBack(serial):
            player = self.serial2player[serial]
            player.remove_next_turn = False
            player.sit_out_next_turn = False
            player.auto = False
            return True
        else:
            return False
        
    def addPlayer(self, serial, seat = 255):
        if self.canAddPlayer(serial):
            player = PokerPlayer(serial, self)
            player.bet = PokerChips(self.chips_values)
            player.dead = PokerChips(self.chips_values)
            player.money = PokerChips(self.chips_values)
            if self.is_directing:
                if seat != 255 and seat in self.seats_left:
                    player.seat = seat
                    self.seats_left.remove(seat)
                else:
                    player.seat = self.seats_left.pop(0)
                if self.verbose >= 1: self.message("player %d get seat %d" % (serial, player.seat))
            self.serial2player[serial] = player
            return True
        else:
            return False

    def botPlayer(self, serial):
        self.serial2player[serial].bot = True
        self.autoBlindAnte(serial)
        self.autoPlayer(serial)
        
    def autoPlayer(self, serial):
        if self.verbose >= 2: self.message("autoPlayer: player %d" % serial)
        player = self.getPlayer(serial)
        player.auto = True
        if self.isBlindAnteRound():
            if player.isBot():
                if self.getSerialInPosition() == serial: self.autoPayBlindAnte()
            else:
                self.sitOut(serial)
        elif self.isPlaying(serial):
            self.__autoPlay()
        
    def removePlayer(self, serial):
        if self.isPlaying(serial):
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
        seats = [ 0 ] * ABSOLUTE_MAX_PLAYERS
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
                    self.error("setSeats: seat %d not in seats_left %s" % ( seat, self.seats_left ))
            seat += 1
        if self.seats() != seats:
            self.error("seatSeats: wanted %s but got %s" % ( seats, self.seats() ))
    
    def beginTurn(self, hand_serial):
        if self.isRunning():
            self.error("beginTurn: already running")
            return

        self.hand_serial = hand_serial
        if self.verbose >= 1: self.message("Dealing %s hand number %d" % ( self.getVariantName(), self.hand_serial ) )
        self.pot = PokerChips(self.chips_values)
        self.board = PokerCards()
        self.winners = []
        self.winner2share = {}
        self.serial2best = {}
        self.side_pots = {
            'contributions': {},
            'pots': [[0, 0]]
            }
        self.showdown_stack = []
        self.turn_history = []

        if self.levelUp():
            self.setLevel(self.getLevel() + 1)
        
        self.resetRoundInfo()
        self.playersBeginTurn()
        if not self.buildPlayerList(True):
            return

        self.changeState("blindAnte")
        if self.blind_info and self.is_directing and not self.first_turn:
            self.moveDealerLeft()
        self.dealerFromDealerSeat()

        self.historyAdd("game", self.getLevel(), self.hand_serial,
                        self.hands_count, (self.time - self.time_of_first_hand),
                        self.variant, self.betting_structure,
                        self.player_list[:], self.dealer_seat,
                        self.chipsMap())
        self.resetRound()
        self.initBlindAnte()
        if self.is_directing:
            self.deck = self.eval.deck()
            self.shuffler.shuffle(self.deck)
            self.updateBlinds()
            self.autoPayBlindAnte()
        
        if self.verbose >= 2: self.message("initialisation turn %d ... finished" % self.hand_serial)

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
                    break
                else:
                    # the impossible has happened
                    self.dealer = len(self.player_list) - 1
                break
        if self.dealer < 0:
            self.error("dealer seat %d cannot be translated in player position among the %d players willing to join the game" % ( self.dealer_seat, self.playingCount() ))
        
    def moveDealerLeft(self):
        if not self.blind_info:
            return

        seat2player = [None] * ABSOLUTE_MAX_PLAYERS
        for player in self.playersAll():
            seat2player[player.seat] = player

        for seat in range(self.dealer_seat + 1, ABSOLUTE_MAX_PLAYERS) + range(0, self.dealer_seat + 1):
            player = seat2player[seat]
            if ( player and player.isSit() and not player.isWaitForBlind() ):
                if self.seatsCount() <= 2:
                    self.dealer_seat = seat
                    break
                elif player.missed_blind == None:
                    self.dealer_seat = seat
                    break
        
    def updateBlinds(self):
        if not self.blind_info:
            return

        if self.sitCount() <= 1:
            #
            # Forget the missed blinds and all when there is less than
            # two players willing to join the game.
            #
            for player in self.playersAll():
                player.missed_blind = None
                player.blind = None
                player.wait_for = False
            return

        seat2player = [None] * ABSOLUTE_MAX_PLAYERS
        blind_ok_count = 0
        for player in self.playersAll():
            seat2player[player.seat] = player
            if player.isSit() and not player.isMissedBlind():
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
        # blind AND is on the button. This player would have to pay the
        # small blind but then, there would be a need to walk the list
        # of players, starting from the dealer, once more to figure out
        # who has to pay the big blind. Furthermore, this case leads to
        # the awkward result that the person next to the dealer pays the
        # big blind and the dealer pays the small blind.
        #
        if blind_ok_count < 2:
            if self.verbose > 2:
                print "Forbid missed blinds"
            for player in players:
                if player and player.isSit():
                    player.missed_blind = None
                
        def updateMissed(players, index, what):
            while ( index < ABSOLUTE_MAX_PLAYERS and
                    ( not players[index] or
                      not players[index].isSit() ) ):
                if players[index] and players[index].missed_blind == None:
                    players[index].missed_blind = what
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
            elif ( ( not player.wait_for and
                     player.missed_blind == None ) or
                   self.sitCount() == 2 ):
                player.blind = "small"
                done = True
            elif player.missed_blind != None:
                player.wait_for = "late"
            index += 1

        if not done:
            self.error("updateBlinds cannot assign the small blind")

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
            self.error("updateBlinds cannot assign big blind")
        #
        #
        # Late blind
        #
        while index < ABSOLUTE_MAX_PLAYERS:
            player = players[index]
            if player:
                if not player.sit_out:
                    if ( player.wait_for == "big" or
                         player.missed_blind == None ):
                        player.blind = None
                    elif ( player.missed_blind == "big" or
                           player.missed_blind == "small" ):
                        if self.sitCount() > 5:
                            player.blind = "big_and_dead"
                        else:
                            player.blind = "big"
                        player.wait_for = False
                    elif player.missed_blind == "n/a":
                        player.blind = "late"
                        player.wait_for = False
                    elif player.blind == True:
                        pass
                    else:
                        self.error("updateBlinds statement unexpectedly reached while evaluating late blind")
                else:
                    player.blind = None
            index += 1
        if self.verbose > 2:
            showblinds = lambda player: "%02d:%s:%s:%s" % ( player.serial, player.blind, player.missed_blind, player.wait_for )
            self.message("updateBlinds: in game (blind:missed:wait) " + join(map(showblinds, self.playersInGame())))
            players = self.playersAll()
            players.sort(lambda a,b: int(a.seat - b.seat))
            self.message("updateBlinds: all     (blind:missed:wait) " + join(map(showblinds, players)))
        
    def handsMap(self):
        pockets = {}
        for player in self.playersNotFold():
            pockets[player.serial] = player.hand.copy()
        return pockets

    def chipsMap(self):
        chips = {}
        chips['values'] = self.chips_values
        for player in self.playersNotFold():
            chips[player.serial] = player.money.chips[:]
        return chips

    def isTournament(self):
        return self.hasLevel()
    
    def hasLevel(self):
        return ( (self.blind_info and self.blind_info["change"]) or
                 (self.ante_info and self.ante_info["change"]) )

    def delayToLevelUp(self):
        for what in (self.blind_info, self.ante_info): 
            if not what or not what["change"]:
                continue

            if self.level == 0:
                return (0, what["unit"])

            if what["unit"] == "minute":
                return ( ( what["frequency"] * 60 ) - ( self.time - what["time"] ), "second" )

            elif what["unit"] == "hand":
                return ( what["frequency"] - ( self.hands_count - what["hands"] ), "hand" )

            else:
                self.error("delayToLevelUp: unknown unit %s " % what["unit"])

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
            flop = (self.inGameCount() * 100) / self.sitCount();
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
            self.time_of_first_hand = time # first turn, so we get initial time
        self.time = time

    def initBlindAnte(self):
        self.side_pots['contributions'][self.current_round] = {}
        if not self.is_directing:
            return
        
        if self.blind_info and self.first_turn:
            for player in self.playersAll():
                player.missed_blind = None

        if self.isTournament():
            for player in self.playersAll():
                player.auto_blind_ante = True
                
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
                if ( player.blind != True and player.blind != None ):
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
                return (big, 0, False)
            elif player.blind == "late":
                return (big, 0, True)
            elif player.blind == "small":
                return (small, 0, False)
            elif player.blind == "big_and_dead":
                return (big, small, True)
            elif ( player.blind == None or player.blind == True ):
                return (0, 0, False)
            else:
                self.error("blindAmount unexpected condition for player %d" % player.serial)
        else:
            return (0, 0, False)
        
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
                (amount, dead, is_late) = self.blindAmount(serial)
                if amount > 0:
                    self.historyAdd("position", self.position)
                    if player.isAutoBlindAnte():
                        self.payBlind(serial, amount, dead)
                        auto_payed = True
                    else:
                        self.historyAdd("blind_request", serial, amount, dead, is_late)
                        auto_payed = False
                        break
            if self.ante_info and player.ante == False:
                self.historyAdd("position", self.position)
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
        
    def initRound(self):
        info = self.roundInfo()
        if self.verbose >= 2: self.message("new round %s" % info["name"])
        if not self.is_directing and self.isFirstRound():
            self.buildPlayerList(False)
            self.dealerFromDealerSeat()
        self.round_cap_left = self.roundCap()
        self.last_bet = 0
        self.first_betting_pass = True
        if info["position"] == "under-the-gun":
            #
            # The player under the gun is the first to talk
            #
            count = self.inGameCount()
            if count < 2:
                raise UserWarning, "initialization but less than two players in game"
            if self.seatsCount() == 2:
                self.position = self.dealer
            else:
                self.position = self.indexInGameAdd(self.dealer, 3)
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
                print "%s : %d" % ( player.hand.getVisible(), values[-1] )
            if info["position"] == "low":
                value = min(values)
            else:
                value = max(values)
            index = values.index(value)
            serial = self.serialsInGame()[index]
            self.position = self.player_list.index(serial)
        else:
            raise UserWarning, "unknown position info %s" % info["position"]
        if self.isFirstRound():
            #
            # The first round takes the blinds/antes
            #
            self.side_pots['contributions'][self.current_round] = self.side_pots['contributions'][self.current_round - 1]
            del self.side_pots['contributions'][self.current_round - 1]
        else:
            self.side_pots['contributions'][self.current_round] = {}

        if self.isSecondRound():
            self.updateStatsFlop(False)

        #
        # Last to talk may not be computed before the blinds/ante
        # are payed because players may be all-in because they had
        # to pay the blind.
        #
        if info["position"] == "under-the-gun":
            if self.seatsCount() == 2:
                self.last_to_talk = self.indexInGameAdd(self.dealer, 1)
            else:
                self.last_to_talk = self.indexInGameAdd(self.dealer, 2)
        elif info["position"] == "next-to-dealer":
            self.last_to_talk = dealer_or_before_him
        elif info["position"] == "low" or info["position"] == "high":
            self.last_to_talk = self.indexInGameAdd(self.position, -1)
        else:
            raise UserWarning, "unknow position info %s" % info["position"]

        for player in self.playersInGame():
            player.talked_once = False
            
        if self.verbose >= 2: self.message("dealer %d, in position %d, last to talk %d" % (self.dealer, self.position, self.last_to_talk))
        self.historyAdd("round", self.state, self.board.copy(), self.handsMap())
        self.__autoPlay()

    def sortPlayerList(self):
        self.player_list.sort(lambda a,b: int(self.serial2player[a].seat - self.serial2player[b].seat))

    def playersBeginTurn(self):
        map(PokerPlayer.beginTurn, self.playersAll())
        if not self.is_directing:
            for player in self.playersAll():
                player.wait_for = False
        
    def buildPlayerList(self, with_wait_for):
        if self.sitCount() < 2:
            self.error("cannot make a consistent player list with less than two players willing to join the game")
            return False
        #
        # The player list is the list of players seated, sorted by seat
        #
        if with_wait_for:
            self.player_list = self.serialsSit()
        else:
            self.player_list = filter(lambda x: self.serial2player[x].isSit() and not self.serial2player[x].isWaitForBlind(), self.serial2player.keys())
        self.sortPlayerList()
        if self.verbose >= 2: self.message("player list: %s" % self.player_list)
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
            else:
                blind_info = None
                if self.verbose >= 1: self.message("unexpected blind change method %s " % info["change"])

        info = self.ante_info
        ante_info = None
        if info and info["change"]:
            ante_info = {}
            if info["change"] == "double":
                ante_info["value"] = info["value_reference"] * pow(2, level - 1)
                ante_info["bringin"] = info["bringin_reference"] * pow(2, level - 1)
            else:
                ante_info = None
                if self.verbose >= 1: self.message("unexpected ante change method %s " % info["change"])

        return ( blind_info, ante_info )
        
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
            info["bringin"] = ante_info["bringin"]

        self.level = level

    def isBroke(self, serial):
        player = self.getPlayer(serial)
        if player:
          money = player.money.toint()
          return ( money <= 0 or
                   ( not self.isTournament() and
                     self.blind_info and
                     money < ( self.blind_info["big"] + self.blind_info["small"] ) ) )
        else:
          return False
        
    def endTurn(self):
        if self.verbose >= 2: self.message("---end turn--")

        self.hands_count += 1
        self.updateStatsEndTurn()

        self.dealer_seat = self.getPlayerDealer().seat
        
        self.historyAdd("end", self.winners[:], self.winner2share, self.showdown_stack)

        for player in self.playersAll():
            if player.rebuy > 0:
                player.money.add(player.rebuy)
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
        for player in self.playersAll():
            if player.sit_out_next_turn:
                self.historyAdd("sitOut", player.serial)
                self.sitOut(player.serial)
                sitting_out.append(player.serial)
            if player.remove_next_turn:
                if player.serial not in sitting_out:
                    self.historyAdd("sitOut", player.serial)
                    self.sitOut(player.serial)
                    sitting_out.append(player.serial)

        disconnected = self.serialsDisconnected()
        if len(disconnected) > 0:
            self.historyAdd("leave", disconnected)
        for serial in disconnected:
            self.__removePlayer(serial)
        self.historyAdd("finish", self.hand_serial)

    def __removePlayer(self, serial):
        #
        # Get his seat back
        #
        if self.verbose >= 1: self.message("removing player %d from game" % (serial))
        if not self.serial2player[serial].seat in self.seats_left:
            self.seats_left.insert(0, self.serial2player[serial].seat)
        else:
            self.error("%d alreay in seats_left" % self.serial2player[serial].seat)
        #
        # Forget about him
        #
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
        self.position = -1
        self.changeState(self.roundInfo()["name"])

    def endState(self):
        self.current_round = -2
        self.position = -1
        self.changeState("end")
        
    def roundInfo(self):
        return self.round_info[self.current_round]

    def betInfo(self):
        return self.bet_info[self.current_round]
    
    def canPlay(self, serial):
        return ( self.isRunning() and
                 serial in self.serialsInGame() and
                 self.canAct(serial) )
        
    def canAct(self, serial):
        return ( self.isRunning() and
                 self.getSerialInPosition() == serial and
                 self.cardsDealt() )

    def canCall(self, serial):
        """
        Can call if the highest bet is greater than the player bet.
        """
        if self.isBlindAnteRound():
            return False
        player = self.serial2player[serial]
        return self.highestBetNotFold() > player.bet.toint()

    def canRaise(self, serial):
        """
        Can raise if round cap not reached and the player can at
        least match the highest bet.
        """
        if self.isBlindAnteRound():
            return False
        player = self.serial2player[serial]
        highest_bet = self.highestBetNotFold()
        money = player.money.toint()
        bet = player.bet.toint()
        #
        # Can raise if the round is not capped and the player has enough money to
        # raise. The player will be given an opportunity to raise if his bet is
        # lower than the highest bet on the table or if he did not yet talk in this
        # betting round (for instance if he payed the big blind or a late blind).
        #
        return ( self.round_cap_left != 0 and
                 money > highest_bet - bet and
                 ( player.talked_once == False or
                   bet < highest_bet )
                 )

    def canCheck(self, serial):
        """
        Can check if all bets are equal
        """
        if self.isBlindAnteRound():
            return False
        return self.highestBetNotFold() <= self.getPlayer(serial).bet.toint()
        
    def possibleActions(self, serial):
        if self.canAct(serial) and not self.isBlindAnteRound():
            actions = []
            if self.canCall(serial):
                actions.append("call")
            if self.canRaise(serial):
                actions.append("raise")
            if self.canCheck(serial):
                actions.append("check")
            else:
                actions.append("fold")
            return actions
        else:
            return False
        
    def call(self, serial):
        if self.isBlindAnteRound():
            return False
        if not self.canAct(serial):
            self.error("player %d cannot call. state = %s" %
                       (serial, self.state))
            return False

        player = self.serial2player[serial]
        amount = min(self.highestBetNotFold() - player.bet.toint(), player.money.toint())
        if self.verbose >= 2: self.message("player %d calls %d" % (serial, amount))
        self.historyAdd("call", serial, amount)
        self.bet(serial, amount)
        return True

    def callNraise(self, serial, amount):
        if self.isBlindAnteRound():
            return False
        if not self.canAct(serial):
            self.error("player %d cannot raise. state = %s" %
                       (serial, self.state))
            return False

        if self.round_cap_left == 0:
            self.error("round capped, can't raise (ignored)")
            return False

        (min_bet, max_bet, to_call) = self.betLimits(serial)
        amount = PokerChips(self.chips_values, amount)
        if amount.toint() < min_bet:
            amount.set(min_bet)
        elif amount.toint() > max_bet:
            amount.set(max_bet)
        if self.verbose >= 1: self.message("player %d raises %d" % (serial, amount.toint()))
        self.historyAdd("raise", serial, amount.chips[:])
        highest_bet = self.highestBetNotFold()
        self.bet(serial, amount)
        if self.isRunning():
            last_bet = self.highestBetNotFold() - highest_bet
            self.last_bet = max(self.last_bet, last_bet)
            self.round_cap_left -= 1
        return True

    def bet(self, serial, amount):
        if self.verbose >= 1: self.message("player %d bets %s" % ( serial, amount ))
        #
        # Transfert the player money from his stack to the bet stack
        #
        self.money2bet(serial, amount)
        self.__talked(serial)

    def check(self, serial):
        if self.isBlindAnteRound():
            return False
        if not self.canAct(serial):
            self.error("player %d cannot check. state = %s, serial in position = %d (ignored)" % (serial, self.state, self.getSerialInPosition()))
            return False

        if not self.canCheck(serial):
            self.error("player %d tries to check but should call or raise (ignored)" % serial)
            return False

        if self.verbose >= 1: self.message("player %d checks" % serial)
        self.historyAdd("check", serial)
        #
        # Nothing done: that's what "check" stands for
        #
        self.__talked(serial)
        return True

    def fold(self, serial):
        if self.isBlindAnteRound():
            return False
        if not self.canAct(serial):
            self.error("player %d cannot fold. state = %s, serial in position = %d (ignored)" % (serial, self.state, self.getSerialInPosition()))
            return False

        if self.serial2player[serial].fold == True:
            if self.verbose >= 1: self.message("player %d already folded (presumably autoplay)" % serial)
            return True
        
        if self.verbose >= 1: self.message("player %d folds" % serial)
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
            self.error("no blind due")
        if not self.isBlindAnteRound():
            self.error("player %d cannot pay blind while in state %s" % ( serial, self.state ))
            return False
        if not self.canAct(serial):
            self.error("player %d cannot wait for blind. state = %s, serial in position = %d (ignored)" % (serial, self.state, self.getSerialInPosition()))
            return False
        player = self.serial2player[serial]
        player.wait_for = "big"
        if self.is_directing:
            self.updateBlinds()
            self.historyAdd("wait_blind", serial)
            self.__talkedBlindAnte()
        
    def blind(self, serial, amount = 0, dead = 0):
        if not self.blind_info:
            self.error("no blind due")
        if not self.isBlindAnteRound():
            self.error("player %d cannot pay blind while in state %s" % ( serial, self.state ))
            return False
        if not self.canAct(serial):
            self.error("player %d cannot pay blind. state = %s, serial in position = %d (ignored)" % (serial, self.state, self.getSerialInPosition()))
            return False
        if self.is_directing and amount == 0:
            (amount, dead, is_late) = self.blindAmount(serial)
        self.payBlind(serial, amount, dead)
        if self.is_directing:
            self.__talkedBlindAnte()

    def payBlind(self, serial, amount, dead):
        player = self.serial2player[serial]
        money = player.money.toint()
        if money < amount + dead:
            if money < amount:
                dead = 0
                amount = money
            else:
                dead = money - amount
        if self.verbose >= 2: self.message("player %d pays blind %d/%d" % (serial, amount, dead))
        self.historyAdd("blind", serial, amount, dead)
        if dead > 0:
            #
            # There is enough money to pay the amount, pay the dead, if any
            #
            self.money2bet(serial, dead)
            self.bet2pot(serial)

        self.money2bet(serial, amount)
        player.blind = True
        player.missed_blind = None
        player.wait_for = False

    def ante(self, serial, amount = 0):
        if not self.ante_info:
            self.error("no ante due")
        if not self.isBlindAnteRound():
            self.error("player %d cannot pay ante while in state %s" % ( serial, self.state ))
            return False
        if not self.canAct(serial):
            self.error("player %d cannot pay ante. state = %s, serial in position = %d (ignored)" % (serial, self.state, self.getSerialInPosition()))
            return False
        if self.is_directing:
            amount = self.ante_info['value']
        self.payAnte(serial, amount)
        if self.is_directing:
            self.__talkedBlindAnte()

    def payAnte(self, serial, amount):
        player = self.serial2player[serial]
        amount = min(amount, player.money.toint())
        if self.verbose >= 2: self.message("player %d pays ante %d" % (serial, amount))
        self.historyAdd("ante", serial, amount)
        self.money2bet(serial, amount)
        self.bet2pot(serial)
        self.getPlayer(serial).ante = True
    
    def __talkedBlindAnte(self):
        if self.sitCount() < 2:
            self.returnBlindAnte()
            self.endState()
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
            if self.inGameCount() < 2:
                #
                # All players are all-in except one, distribute all
                # cards and figure out who wins.
                #
                if self.verbose >= 2: self.message("less than two players not all-in")
                self.nextRound()
                self.side_pots['contributions'][self.current_round] = self.side_pots['contributions'][self.current_round - 1]
                del self.side_pots['contributions'][self.current_round - 1]
                self.__makeSidePots()
                self.bet2pot()
                self.dealCards()
                
                while not self.isLastRound():
                    self.nextRound()
                    self.dealCards()

                self.endState()
                if self.is_directing:
                    self.distributeMoney()
                    self.showdown()
                    self.endTurn()
                else:
                    if self.verbose >= 2: self.message("money not yet distributed, assuming information is missing ...")
            else:
                self.nextRound()
                self.dealCards()
                if self.is_directing:
                    self.initRound()
        else:
            self.updateBlinds()
            self.position = self.indexInGameAdd(self.position, 1)
            self.autoPayBlindAnte()

    def __talked(self, serial):
        self.getPlayer(serial).talked_once = True
        if self.__roundFinished(serial):
            if self.verbose >= 2: self.message("round finished")

            self.__makeSidePots()
            self.bet2pot()

            if self.notFoldCount() < 2:
                self.position = self.indexNotFoldAdd(self.position, 1)
                if self.verbose >= 2: self.message("last player in game %d" % self.getSerialInPosition())
                if self.isFirstRound():
                    self.updateStatsFlop(True)
                self.endState()
                self.distributeMoney()
                self.endTurn()

            elif self.inGameCount() < 2:
                #
                # All players are all-in except one, distribute all
                # cards and figure out who wins.
                #
                if self.verbose >= 2: self.message("less than two players not all-in")
                while not self.isLastRound():
                    self.nextRound()
                    self.dealCards()

                self.endState()
                if self.is_directing:
                    self.distributeMoney()
                    self.showdown()
                    self.endTurn()
                else:
                    if self.verbose >= 2: self.message("money not yet distributed, assuming information is missing ...")
            else:
                #
                # All bets equal, go to next round
                #
                if self.verbose >= 2: self.message("next state")
                self.nextRound()
                if not self.isLastRound():
                    self.dealCards()
                    if self.is_directing:
                        self.initRound()
                    else:
                      if self.verbose >= 2: self.message("round not initialized, waiting for more information ... ")
                else:
                    self.endState()
                    if self.is_directing:
                        self.distributeMoney()
                        self.showdown()
                        self.endTurn()
                    else:
                        if self.verbose >= 2: self.message("money not yet distributed, assuming information is missing ...")
        else:
            self.position = self.indexInGameAdd(self.position, 1)
            if self.verbose >= 2: self.message("new position (%d)" % self.position)
            self.__autoPlay()

    def __botEval(self, serial):
        ev = self.handEV(serial, 10)

        if self.state == "pre-flop":
            if ev < 100:
                action = "check"
            elif ev < 500:
                action = "call"
            else:
                action = "raise"
        elif self.state == "flop" or self.state == "third":
            if ev < 200:
                action = "check"
            elif ev < 600:
                action = "call"
            else:
                action = "raise"
        elif self.state == "turn" or self.state == "fourth":
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

        if player.isBot():
            (desired_action, ev) = self.__botEval(serial)
            actions = self.possibleActions(serial)
            while not desired_action in actions:
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
                self.error("__autoPlay: unexpected actions = %s" % actions)
          
        elif ( player.isSitOut() or player.isAuto() ):
            #
            # A player who is sitting but not playing (sitOut) automatically
            # folds.
            #
            self.fold(serial)

    def hasLow(self):
        return "low" in self.win_orders

    def hasHigh(self):
        return "hi" in self.win_orders

    def isLow(self):
        return self.win_orders == [ "low" ]

    def isHigh(self):
        return self.win_orders == [ "hi" ]
    
    def isHighLow(self):
        return self.win_orders == [ "hi", "low" ]

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
                self.error("unexpected win order: %s for variant %s" % ( win_order, variant ))
        if not self.win_orders:
            raise UserWarning, "failed to read win orders from %s" % self.__variant.url 

        board_size = 0
        hand_size = 0
        for name in self.getParamList("/poker/variant/round/@name"):
            board = self.getParamList("/poker/variant/round[@name='" + name + "']/deal[@card='board']")
            board_size += len(board)
            down = self.getParamList("/poker/variant/round[@name='" + name + "']/deal[@card='down']")
            hand_size += len(down)
            up = self.getParamList("/poker/variant/round[@name='" + name + "']/deal[@card='up']")
            hand_size += len(up)
            position = self.getParam("/poker/variant/round[@name='" + name + "']/position/@type")
            info = {
                "name": name,
                "position": position,
                "board": board,
                "board_size": board_size,
                "hand_size": hand_size,
                "down": down,
                "up": up,
                }
            self.round_info.append(info)
            self.round_info_backup.append(info)

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
        self.buy_in = int(self.getParam('/bet/@buy-in'))
        self.max_buy_in = int(self.getParam('/bet/@max-buy-in'))

        chips_values = self.getParam("/bet/chips/@values")
        self.chips_values = [ int(x) for x in split(chips_values) ]
        
        self.bet_info = self.getParamProperties('/bet/variants[contains(@ids,"' + self.variant + '")]/round')

        self.blind_info = False
        blind_info = self.getParamProperties("/bet/blind");
        if len(blind_info) > 0:
            blinds = blind_info[0]
            self.blind_info = {
                "small": int(blinds["small"]),
                "small_reference": int(blinds["small"]),
                "big": int(blinds["big"]),
                "big_reference": int(blinds["big"]),
                "change": blinds.has_key("change") and blinds["change"]
                }

            if self.blind_info["change"] != False:
                self.blind_info["frequency"] = int(blinds["frequency"])
                self.blind_info["unit"] = blinds["unit"]

        self.ante_info = False
        ante_info = self.getParamProperties("/bet/ante");
        if len(ante_info) > 0:
            antes = ante_info[0]
            self.ante_info = {
                "value": int(antes["fixed"]),
                "value_reference": int(antes["fixed"]),
                "bringin": int(antes["bring-in"]),
                "bringin_reference": int(antes["bring-in"]),
                "change": antes.has_key("change") and antes["change"]
                }

            if self.ante_info["change"] != False:
                self.ante_info["frequency"] = int(antes["frequency"])
                self.ante_info["unit"] = antes["unit"]

    def getBoardLength(self):
        return len(self.board.tolist(True))

    def cardsDealtThisRoundCount(self):
        if not self.isRunning():
            return -1
        
        if self.isBlindAnteRound():
            return 0
        
        round_info = self.roundInfo()
        return len(round_info["up"]) + len(round_info["down"])
        
    def upCardsDealtThisRoundCount(self):
        if not self.isRunning():
            return -1
        
        if self.isBlindAnteRound():
            return 0
        
        round_info = self.roundInfo()
        return len(round_info["up"])
        
    def downCardsDealtThisRoundCount(self):
        if not self.isRunning():
            return -1
        
        if self.isBlindAnteRound():
            return 0
        
        round_info = self.roundInfo()
        return len(round_info["down"])
        
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
            return len(info["board"]) + len(info["up"]) * number_of_players + len(info["down"]) * number_of_players

        if number_to_deal() > len(self.deck):
            while number_to_deal() > len(self.deck):
                if len(info["up"]) > 0:
                    info["up"].pop()
                elif len(info["down"]) > 0:
                    info["down"].pop()
                else:
                    raise UserWarning, "unable to deal %d cards" % number_to_deal()
                info["hand_size"] -= 1

                info["board"].append("board")
                info["board_size"] += 1
            
            
        for card in info["board"]:
            self.board.add(self.deck.pop(), True)
        for card in info["up"]:
            for player in self.playersNotFold():
                player.hand.add(self.deck.pop(), True)
        for card in info["down"]:
            for player in self.playersNotFold():
                player.hand.add(self.deck.pop(), False)
        if self.verbose >= 1:
          if len(info["up"]) > 0 or len(info["down"]) > 0:
            for serial in self.serialsNotFold():
              self.message("player %d cards: " % serial + self.getHandAsString(serial))
          if len(info["board"]) > 0:
            self.message("board: " + self.getBoardAsString())
          
        
    def __roundFinished(self, serial):
        #
        # The round finishes when there is only one player not fold ...
        #
        if self.notFoldCount() < 2:
            if self.verbose >= 2: self.message("only one player left in the game")
            return True

        #
        # ... or when all players are all-in.
        #
        if self.inGameCount() < 1:
            if self.verbose >= 2: self.message("all players are all-in")
            return True
        
        if self.first_betting_pass:
            if serial != self.getSerialLastToTalk():
                return False
            else:
                self.first_betting_pass = False
        return self.betsEqual()

    def moneyDistributed(self):
        return len(self.showdown_stack) > 0

    def isWinnerBecauseFold(self):
        return moneyDistributed() and self.showdown_stack[0].has_key('foldwin')
    
    #
    # Split the pot
    #
    def distributeMoney(self):
        if self.moneyDistributed():
            self.error("distributeMoney must be called only once per turn")
            return

        pot_backup = self.pot.copy()
        side_pots = self.getPots()
        if self.notFoldCount() < 2:
            #
            # Special and simplest case : the winner has it because 
            # everyone folded. Don't bother to evaluate.
            #
            (serial,) = self.serialsNotFold()
            self.winner2share[serial] = self.pot.toint()
            self.showdown_stack = [ { 'type': 'game_state',
                                      'player_list': self.player_list,
                                      'side_pots': side_pots,
                                      'pot': pot_backup,
                                      'foldwin': True },
                                    { 'type': 'resolve',
                                      'serial2share': { serial: pot_backup.toint() },
                                      'serials': [serial],
                                      'pot': pot_backup.toint() } ]
            if self.verbose > 2: pprint(self.showdown_stack)
            self.pot2money(serial)
            self.setWinners([serial])
            return

        player2side_pot = {}
        for player in self.playersNotFold():
            player2side_pot[player.serial] = side_pots['pots'][player.side_pot_index][1]
        if self.verbose >= 2: self.message("distribute a pot of %d" % self.pot.toint())
        #
        # Keep track of the best hands (high and low) for information
        # and for the showdown.
        #
        self.serial2best = self.bestHands(self.serialsNotFold())
        #
        # Every player that received a share of the pot and the
        # amount.
        #
        winner2share = {}
        #
        # List of winners for each side of the pot (hi or low),
        # regardless of the fact that low hands matter for this
        # particular variant. Warning: a winner may show more
        # than once in these lists (when he is tie for two side pots,
        # for instance).
        #
        self.side2winners = { 'hi': [], 'low': [] }
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
            potential_winners = filter(lambda player: player2side_pot[player.serial] > 0, self.playersNotFoldShowdownSorted())
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
                frame['uncalled'] = player2side_pot[winner.serial]
                showdown_stack.insert(0, frame)
                if not winner2share.has_key(winner):
                    winner2share[winner] = 0
                winner2share[winner] += player2side_pot[winner.serial]
                player2side_pot[winner.serial] = 0
                break
            
            frame.fromkeys(self.win_orders + [ 'pot', 'chips_left' ])
            frame['type'] = 'resolve'
            frame['serial2share'] = {}
            frame['serials'] = [ player.serial for player in potential_winners ]

            if self.verbose >= 2:
              self.message("looking for winners with board %s" % self.getBoardAsString())
              for player in potential_winners:
                self.message("  => hand for player %d %s" % ( player.serial, self.getHandAsString(player.serial)))
            #
            #
            # Ask poker-eval to figure out who the winners actually are
            #
            eval = self.eval.winners(game = self.variant,
                                     pockets = [ player.hand.tolist(True) for player in potential_winners ],
                                     board = self.board.tolist(True))
            #
            # Feed local variables with eval results sorted in various
            # forms to ease computing the results.
            #
            winners = [ ]
            if self.verbose >= 1: self.message("winners:")
            for (side, indices) in eval.iteritems():
                side_winners = [ potential_winners[i] for i in indices ]
                for winner in side_winners:
                    if self.verbose >= 1: self.message(" => player %d %s (%s)" % ( winner.serial, self.bestCardsAsString(self.serial2best, winner.serial, side), side ))
                    if not winner2share.has_key(winner):
                        winner2share[winner] = 0
                    frame['serial2share'][winner.serial] = 0
                frame[side] = [ winner.serial for winner in side_winners ]
                self.side2winners[side] += frame[side]
                winners += side_winners
                
            #
            # The pot to be considered is the lowest side_pot of all
            # the winners. In other words, we must share the pot that
            # was on the table for the winner that was all-in first.
            #
            pot = min([ player2side_pot[player.serial] for player in winners ])
            frame['pot'] = pot
            if self.verbose >= 2: self.message("  and share a pot of %d" % pot)
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
            (global_share, remainder) = self.divideChips(pot, len(eval.keys()))
            chips_left += remainder
            frame['chips_left'] = remainder
            for winners_indices in eval.values():
                winners = [ potential_winners[i] for i in winners_indices ]
                (share, remainder) = self.divideChips(global_share, len(winners))
                chips_left += remainder
                frame['chips_left'] += remainder
                for winner in winners:
                    winner2share[winner] += share
                    frame['serial2share'][winner.serial] += share
            #
            # The side pot of each winner is lowered by the amount
            # that was shared among winners. It will reduce the number
            # of potential winners (to the very least, the winner(s)
            # with the smallest side pot will be discarded).
            #
            for player in potential_winners:
                player2side_pot[player.serial] -= pot

            showdown_stack.append(frame)

        if len(winner2share) == 1:
            #
            # Special case that is the most frequent (single winner)
            # and where we can avoid arithmethic on the chips
            #
            player = winner2share.keys()[0]
            player.money.add(self.pot)
        else:
            #
            # Divide and share the chips
            #
            for (player, share) in winner2share.iteritems():
                player.money.add(share)

        #
        # The chips left go to the player next to the dealer,
        # regardless of the fact that this player folded.
        #
        if chips_left > 0:
            next_to_dealer = self.indexAdd(self.dealer, 1)
            player = self.serial2player[self.player_list[next_to_dealer]]
            player.money.add(chips_left)
            if winner2share.has_key(player):
                winner2share[player] += chips_left
            else:
                winner2share[player] = chips_left
            showdown_stack.insert(0, { 'type': 'left_over',
                                       'chips_left': chips_left,
                                       'serial': player.serial })

        self.pot.reset()
        #
        # For convenience, build a single list of all winners, regardless
        # of the side of the pot they won. Remove duplicates in all lists.
        #
        winners_serials = []
        uniq = {}
        for side in self.side2winners.keys():
            self.side2winners[side] = uniq.fromkeys(self.side2winners[side]).keys()
            winners_serials += self.side2winners[side]
        self.winner2share = dict([ ( winner.serial, share ) for ( winner, share ) in winner2share.iteritems() ])
        self.setWinners(uniq.fromkeys(winners_serials).keys())
        showdown_stack.insert(0, { 'type': 'game_state',
                                   'serial2best': self.serial2best,
                                   'player_list': self.player_list,
                                   'side_pots': side_pots,
                                   'pot': pot_backup })
        self.showdown_stack = showdown_stack
        if self.verbose > 2: pprint(self.showdown_stack)

    def divideChips(self, amount, divider):
        unit = self.chips_values[0]
        in_units = amount / unit
        if amount % unit != 0:
            self.error("divideChips: %d is not a multiple of %d" % ( amount, unit ))
        result = in_units / divider
        remainder = in_units % divider
        return (result * unit, remainder * unit)
    
    def showdown(self):
        if self.notFoldCount() < 2:
            #
            # When everyone folds, there is no such thing as a showdown
            #
            return

        if not self.is_directing:
            #
            # A game instance that does not know the cards of each player
            # can't compute a showdown
            #
            return
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
            if self.player_list[showing] in self.winners:
                show = True

            if show:
                player.hand.allVisible()
                
            if showing == last_to_show:
                break
            
            showing = self.indexNotFoldAdd(showing, 1)

        self.historyAdd("showdown", self.board.copy(), self.handsMap())

    def handEV(self, serial, iterations):
        pocket_size = self.getMaxHandSize()
        pockets = []
        for pocket in [ player.hand.tolist(True) for player in self.playersNotFold() ]:
            if len(pocket) < pocket_size:
                pocket.extend([PokerCards.NOCARD] * (pocket_size - len(pocket)))
            pockets.append(pocket)
        board = self.board.tolist(True)
        board_size = self.getMaxBoardSize()
        if len(board) < board_size:
            board.extend([PokerCards.NOCARD] * (board_size - len(board)))
        eval = self.eval.poker_eval(game = self.variant,
                                    pockets = pockets,
                                    board = board,
                                    fill_pockets = 1,
                                    iterations = iterations)
        player_index = self.serialsNotFold().index(serial)
        return eval["eval"][player_index]["ev"]

    def readableHandValueLong(self, side, value, cards):
        cards = self.eval.card2string(cards)
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return "The wheel"
                else:
                    return join(map(lambda card: card[0], cards), ", ")
            else:
                return "High card %s" % letter2name[cards[0][0]]
        elif value == "OnePair":
            return "A pair of %s, %s kicker" % ( letter2names[cards[0][0]], letter2name[cards[2][0]] )
        elif value == "TwoPair":
            return "Two pairs %s and %s, %s kicker" % ( letter2names[cards[0][0]], letter2names[cards[2][0]], letter2name[cards[4][0]] )
        elif value == "Trips":
            return "Three of a kind %s, %s kicker" % ( letter2names[cards[0][0]], letter2name[cards[3][0]] )
        elif value == "Straight":
            return "Straight %s to %s" % ( letter2name[cards[0][0]], letter2name[cards[4][0]] )
        elif value == "Flush":
            return "Flush %s high" % letter2name[cards[0][0]] 
        elif value == "FlHouse":
            return "Full house, %s over %s" % ( letter2name[cards[0][0]], letter2name[cards[3][0]] )
        elif value == "Quads":
            return "Four of a kind %s, %s kicker" % ( letter2names[cards[0][0]], letter2name[cards[4][0]] )
        elif value == "StFlush":
            if letter2names[cards[0][0]] == 'A':
                return "Royal flush"
            else:
                return "Straight flush %s high" % letter2name[cards[0][0]]
        return value
        
    def readableHandValueShort(self, side, value, cards):
        cards = self.eval.card2string(cards)
        if value == "NoPair":
            if side == "low":
                if cards[0][0] == '5':
                    return "The wheel"
                else:
                    return join(map(lambda card: card[0], cards), ", ")
            else:
                return "High card %s" % letter2name[cards[0][0]]
        elif value == "OnePair":
            return "Pair of %s" % letter2names[cards[0][0]]
        elif value == "TwoPair":
            return "Pairs of %s and %s" % ( letter2names[cards[0][0]], letter2names[cards[2][0]] )
        elif value == "Trips":
            return "Trips %s" % ( letter2names[cards[0][0]] )
        elif value == "Straight":
            return "Straight %s high" % letter2name[cards[0][0]]
        elif value == "Flush":
            return "Flush %s high" % letter2name[cards[0][0]] 
        elif value == "FlHouse":
            return "Full %s over %s" % ( letter2name[cards[0][0]], letter2name[cards[3][0]] )
        elif value == "Quads":
            return "Quads %s, %s kicker" % ( letter2names[cards[0][0]], letter2name[cards[4][0]] )
        elif value == "StFlush":
            if letter2names[cards[0][0]] == 'A':
                return "Royal flush"
            else:
                return "Straight flush"
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
#        print "bestHands: %s" % self.win_orders
#        pprint(results)
        return results

    def bestCardsAsString(self, bests, serial, side):
        return join(self.eval.card2string(bests[serial][side][1][1:]))
        
    def bestHand(self, side, serial):
        if self.variant == "omaha" or self.variant == "omaha8":
            hand = self.serial2player[serial].hand.tolist(True)
            board = self.board.tolist(True)
        else:
            hand = self.serial2player[serial].hand.tolist(True) + self.board.tolist(True)
            board = []
        return self.eval.best(side, hand, board)

    def bestHandValue(self, side, serial):
        (value, cards) = self.bestHand(side, serial)
        return value

    def bestHandCards(self, side, serial):
        (value, cards) = self.bestHand(side, serial)
        return cards

    def readablePlayerBestHands(self, serial):
        results = []
        if self.hasHigh(): results.append(self.readablePlayerBestHand('hi', serial))
        if self.hasLow(): results.append(self.readablePlayerBestHand('low', serial))
        return "\n".join(results)
        
    def readablePlayerBestHand(self, side, serial):
        cards = self.bestHandCards(side, serial)
        result = self.readableHandValueLong(side, cards[0], cards[1:])
        result += ": " + ", ".join(self.eval.card2string(cards[1:]))
        return result
        
    def cards2string(self, cards):
        return join(self.eval.card2string(cards.tolist(True)))
    
    def getHandAsString(self, serial):
        return self.cards2string(self.serial2player[serial].hand)

    def getBoardAsString(self):
        return self.cards2string(self.board)
                    
    def betsNull(self):
        if self.isRunning():
            return sum([ player.bet.toint() for player in self.playersNotFold()]) == 0
        else:
            return False
        
    def setWinners(self, serials):
        if self.verbose >= 2: self.message("player(s) %s win" % serials)
        self.winners = serials

    def bet2pot(self, serial = 0):
        if serial == 0:
            serials = self.player_list
        else:
            serials = [serial]
        for serial in serials:
            player = self.serial2player[serial]
            self.pot.add(player.bet)
            if self.isBlindAnteRound():
                player.dead.add(player.bet)
            player.bet.reset()

    def money2bet(self, serial, amount):
        player = self.serial2player[serial]
        amount = PokerChips(self.chips_values, amount)

        if amount.toint() > player.money.toint():
            self.error("money2bet: %d > %d" % (amount.toint(), player.money.toint()))
            amount.set(player.money)
        player.money.subtract(amount)
        player.bet.add(amount)
        if player.money.toint() < 0:
            self.error("money2bet: %d money dropped under 0" % serial)
        self.updatePots(serial, amount.toint())
        if player.money.toint() == 0:
            self.historyAdd("all-in", serial)
            player.all_in = True

    def updatePots(self, serial, amount):
        pot_index = len(self.side_pots['pots']) - 1
        pot = self.side_pots['pots'][-1]
        pot[0] += amount # pot amount
        pot[1] += amount # pot total
        contributions = self.side_pots['contributions']
        round_contributions = contributions[self.current_round]
        if not round_contributions.has_key(pot_index):
            round_contributions[pot_index] = {}
        pot_contributions = round_contributions[pot_index]
        if not pot_contributions.has_key(serial):
            pot_contributions[serial] = 0
        pot_contributions[serial] += amount

    def playersInPotCount(self, side_pots):
        pot_index = len(side_pots['pots']) - 1
        last_round = max(side_pots['contributions'].keys())
        contributions = side_pots['contributions'][last_round]
        if contributions.has_key(pot_index):
            return len(contributions[pot_index])
        else:
            return 0

    def isSingleUncalledBet(self, side_pots):
        return self.playersInPotCount(side_pots) == 1
        
    def pot2money(self, serial):
        player = self.serial2player[serial]
        player.money.add(self.pot)
        self.pot.reset()

    def highestBetNotFold(self):
        return max([ player.bet.toint() for player in self.playersNotFold() ])

    def highestBetInGame(self):
        return max([ player.bet.toint() for player in self.playersInGame() ])

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
            bet = players[0].bet.toint()
            for player in players:
                player_bet = player.bet.toint()
                if bet != player_bet:
                    return False
        return True

    def __makeSidePots(self):
        round_contributions = self.side_pots['contributions'][self.current_round]
        pots = self.side_pots['pots']
        current_pot_index = len(pots) - 1
        players = filter(lambda player: player.side_pot_index == current_pot_index, self.playersAllIn())
        if not players:
            return
        players.sort(lambda a,b: a.bet.toint() - b.bet.toint())
        for player in players:
            pot_contributions = round_contributions[len(pots) - 1]
            if not pot_contributions.has_key(player.serial):
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
            pot = pots[-1]
            new_pot = [0, 0]
            new_pot_index = len(pots)
            contribution = pot_contributions[player.serial]
            for serial in pot_contributions.keys():
                other_contribution = pot_contributions[serial]
                pot_contributions[serial] = min(contribution, other_contribution)
                remainder = other_contribution - pot_contributions[serial]
                pot[0] -= remainder
                pot[1] -= remainder
                other_player = self.getPlayer(serial)
                if other_contribution > contribution:
                    new_pot_contributions[serial] = remainder
                    new_pot[0] += remainder
                    other_player.side_pot_index = new_pot_index
                elif ( other_contribution == contribution and
                       not other_player.isAllIn() ):
                    other_player.side_pot_index = new_pot_index
            round_contributions[new_pot_index] = new_pot_contributions
            new_pot[1] = new_pot[0] + pot[1]
            pots.append(new_pot)

    def getPots(self):
        return self.side_pots

    def getSidePotTotal(self):
        return self.side_pots['pots'][-1][1]
    
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
        if increment > 0:
            step = 1
        else:
            step = -1
        while increment:
            index = (index + step) % len(self.player_list)
            increment -= step
            while not predicate(self.serial2player[self.player_list[index]]):
                index = (index + step) % len(self.player_list)
        return index
        
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
        return len(self.serialsDisconnectedGame())

    def serialsDisconnected(self):
        return filter(lambda x: self.serial2player[x].isDisconnected(), self.serial2player.keys())

    def playersDisconnected(self):
        return [ self.serial2player[serial] for serial in self.serialsDisconnected() ]

    def connectedCount(self):
        return len(self.serialsConnectedGame())

    def serialsConnected(self):
        return filter(lambda x: self.serial2player[x].isConnected(), self.serial2player.keys())

    def playersConnected(self):
        return [ self.serial2player[serial] for serial in self.serialsConnected() ]

    def sitOutCount(self):
        return len(self.serialsSitOut())

    def serialsSitOut(self):
        return filter(lambda x: self.serial2player[x].isSitOut(), self.serial2player.keys())

    def playersSitOut(self):
        return [ self.serial2player[serial] for serial in self.serialsSitOut() ]

    def brokeCount(self):
        return len(self.serialsBroke())

    def serialsBroke(self):
        return filter(lambda serial: self.isBroke(serial), self.serial2player.keys())

    def playersBroke(self):
        return [ self.serial2player[serial] for serial in self.serialsBroke() ]

    def sitCount(self):
        return len(self.serialsSit())

    def serialsSit(self):
        return filter(lambda x: self.serial2player[x].isSit(), self.serial2player.keys())

    def playersSit(self):
        return [ self.serial2player[serial] for serial in self.serialsSit() ]

    def notPlayingCount(self):
        return len(self.serialsNotPlaying())

    def serialsNotPlaying(self):
        if self.isRunning():
            return filter(lambda x: not x in self.player_list, self.serial2player.keys())
        else:
            return self.serial2player.keys()

    def playersNotPlaying(self):
        return [ self.serial2player[serial] for serial in self.serialsNotPlaying() ]

    def playingCount(self):
        return len(self.serialsPlaying())

    def serialsPlaying(self):
        if self.isRunning():
            return self.player_list
        else:
            return []

    def playersPlaying(self):
        return [ self.serial2player[serial] for serial in self.serialsPlaying() ]

    def allCount(self):
        return len(self.serial2player)

    def serialsAllSorted(self):
        if self.dealer < 0 or self.dealer >= len(self.player_list):
            return self.serial2player.keys()
        else:
            #
            # The list of serials, sort from worst position to best
            # position (i.e. the dealer)
            #
            player_list = self.serial2player.keys()
            player_list.sort(lambda a,b: int(self.serial2player[a].seat - self.serial2player[b].seat))
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
        return filter(lambda x: self.serial2player[x].isInGame(), self.player_list)

    def playersInGame(self):
        return [ self.serial2player[serial] for serial in self.serialsInGame() ]

    def allInCount(self):
        return len(self.serialsAllIn())

    def serialsAllIn(self):
        return filter(lambda x: self.serial2player[x].isAllIn(), self.player_list)

    def playersAllIn(self):
        return [ self.serial2player[serial] for serial in self.serialsAllIn() ]

    def serialsNotFoldShowdownSorted(self):
        next_to_dealer = self.indexAdd(self.dealer, 1)
        player_list = self.player_list[next_to_dealer:] + self.player_list[:next_to_dealer]
        return filter(lambda x: not self.serial2player[x].isFold(), player_list)
    
    def playersNotFoldShowdownSorted(self):
        return [ self.serial2player[serial] for serial in self.serialsNotFoldShowdownSorted() ]
        
    def notFoldCount(self):
        return len(self.serialsNotFold())

    def serialsNotFold(self):
        return filter(lambda x: not self.serial2player[x].isFold(), self.player_list)

    def playersNotFold(self):
        return [ self.serial2player[serial] for serial in self.serialsNotFold() ]

    #
    # Game Parameters.
    #
    def roundCap(self):
        if(self.state == "null" or self.state == "end"):
            return 0
        return int(self.betInfo()["cap"])

    def betLimits(self, serial):
        if(self.state == "null" or self.state == "end"):
            return 0
        info = self.betInfo()
        highest_bet = self.highestBetNotFold()
        player = self.serial2player[serial]
        money = player.money.toint()
        bet = player.bet.toint()
        to_call = highest_bet - bet
        if self.round_cap_left <= 0:
            return (0, 0, to_call)
        #
        # Figure out the theorical max/min bet, regarless of the
        # player[serial] bet/money status
        #
        if info.has_key("fixed"):
            fixed = int(info["fixed"])
            (min_bet, max_bet) = (fixed, fixed)
        elif info.has_key("pow_level"):
            fixed = int(info["pow_level"]) * pow(2, self.getLevel())
            (min_bet, max_bet) = (fixed, fixed)
        else:
            if info.has_key("min"):
                min_bet = int(info["min"])
            elif info.has_key("min_pow_level"):
                min_bet = int(info["min_pow_level"]) * pow(2, self.getLevel())
            else:
                min_bet = 0

            min_bet = max(min_bet, self.last_bet)
            
            if info.has_key("max"):
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
        pot = self.pot and self.pot.toint() or 0
        for player in self.playersPlaying():
            pot += player.bet.toint()
        return pot

    def autoBlindAnte(self, serial):
        self.getPlayer(serial).auto_blind_ante = True
        if self.isBlindAnteRound() and self.getSerialInPosition() == serial:
          self.autoPayBlindAnte()
        
    def noAutoBlindAnte(self, serial):
        self.getPlayer(serial).auto_blind_ante = False
        
    def payBuyIn(self, serial, amount):
        amount = PokerChips(self.chips_values, amount)
        if amount.toint() > self.maxBuyIn():
          if self.verbose: self.error("payBuyIn: maximum buy in is %d and %d is too much" % ( self.maxBuyIn(), amount.toint()  ))
          return False
        player = self.getPlayer(serial)
        player.money.set(amount)
        if self.isTournament() or player.money.toint() >= self.buyIn():
          player.buy_in_payed = True
          return True
        else:
          if self.verbose: self.error("payBuyIn: minimum buy in is %d but %d is not enough" % ( self.buyIn(), player.money.toint() ))
          return False

    def rebuy(self, serial, amount):
        player = self.getPlayer(serial)
        if not player:
          return False
        if player.money.toint() + amount + player.rebuy > self.maxBuyIn():
          return False
        if self.isPlaying(serial):
          player.rebuy += amount
        else:
          player.money.add(amount)
        return True
        
    def buyIn(self):
        return self.buy_in

    def maxBuyIn(self):
        return self.max_buy_in

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
        if self.verbose >= 1: self.message("changing state %s => %s" % (self.state, state))
        self.state = state

    def isRunning(self):
        if self.state == "null" or self.state == "end":
            return False
        else:
            return True

    def registerCallback(self, callback):
        self.callbacks.append(callback)

    def unregisterCallback(self, callback):
        self.callbacks.remove(callback)
        
    def historyAdd(self, *args):
        for callback in self.callbacks:
            callback(*args)
        self.turn_history.append(args)

    def historyGet(self):
        return self.turn_history

    def historyReduce(self):
        index = 0
        game_event = None
        player_list_index = 7
        serial2chips_index = 9
        position2serial = {}
        while index < len(self.turn_history):
            event = self.turn_history[index]
            type = event[0]
            if ( type == "showdown" or
                 ( type == "round" and event[1] != "blindAnte" ) ):
                break
            elif type == "game":
                game_event = self.turn_history[index]
                position = 0
                for serial in game_event[player_list_index]:
                    position2serial[position] = serial
                    position += 1
                index += 1
            elif ( type == "sitOut" or type == "wait_blind" ):
                (type, serial) = event
                #
                # del position + sitOut/wait_blind
                #
                if index < 1 or self.turn_history[index-1][0] != "position":
                    pprint(self.turn_history)
                    print "Ouch again"
                del self.turn_history[index - 1:index + 1]
                #
                # remove references to the player who finally
                # decided to not be part of the turn
                #
                game_event[player_list_index].remove(serial)
                del game_event[serial2chips_index][serial]
            elif ( type == "blind_request" or
                   type == "ante_request" or
                   type == "player_list" ):
                #
                # del, if not the last event
                #
                if index < len(self.turn_history) - 1:
                    if type == "player_list":
                        game_event[player_list_index][:] = event[1]
                    del self.turn_history[index]
                else:
                    index += 1
            elif ( type == "wait_for" ):
                del self.turn_history[index]
            else:
                index += 1
        #
        # Reset the positions of the players to take in account the removed players
        #
        for index in xrange(0, min(index, len(self.turn_history))):
            event = self.turn_history[index]
            if event[0] == "position":
                try:
                    self.turn_history[index] = ( event[0], game_event[player_list_index].index(position2serial[event[1]]) )
                except:
                    pprint(self.turn_history)
                    print "Ouch"

    def error(self, string):
      self.message("ERROR: " + string)
      
    def message(self, string):
      print self.prefix + "[PokerGame " + str(self.id) + "] " + string
      
class PokerGameServer(PokerGame):
    def __init__(self, url, dirs):
        PokerGame.__init__(self, url, True, dirs) # is_directing == True

class PokerGameClient(PokerGame):
    def __init__(self, url, dirs):
        PokerGame.__init__(self, url, False, dirs) # is_directing == False
        
