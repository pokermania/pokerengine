#
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2008, 2009 Bradley M. Kuhn <bkuhn@ebb.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep <licensing@mekensleep.com>
#                                26 rue des rosiers, 75004 Paris
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
#
from math import ceil
from types import StringType
from pprint import pformat
import time, random

def tournament_seconds():
    return time.time()

shuffler = random

from pokerengine.pokergame import PokerGameServer
from pokerengine import pokerprizes
from pokerengine import log as engine_log
log = engine_log.get_child('pokertournament')

TOURNAMENT_STATE_ANNOUNCED = "announced"
TOURNAMENT_STATE_REGISTERING = "registering"
TOURNAMENT_STATE_RUNNING = "running"
TOURNAMENT_STATE_BREAK_WAIT = "breakwait"
TOURNAMENT_STATE_BREAK = "break"
TOURNAMENT_STATE_COMPLETE = "complete"
TOURNAMENT_STATE_CANCELED = "canceled"
TOURNAMENT_STATE_LOADING = "loading"

TOURNAMENT_REBUY_ERROR_TIMEOUT = "timeout"
TOURNAMENT_REBUY_ERROR_USER = "user"
TOURNAMENT_REBUY_ERROR_MONEY = "money"
TOURNAMENT_REBUY_ERROR_OTHER = "other"
            
def equalizeCandidates(games):
    #
    # Games less than 70% full are willing to steal players from other
    # games. Games that are more than 70% full and that are not
    # running are willing to provide players to others.
    #
    want_players = []
    provide_players = []
    for game in games:
        threshold = int(game.max_players * .7)
        count = game.allCount()
        if count < threshold:
            want_players.append([ game.id, game.max_players - count ])
        elif game.isEndOrNull():
            serials = game.serialsAllSorted()
            provide_players.append((game.id, serials[:count - threshold]))
    return ( want_players, provide_players )

def equalizeGames(games, log = None):
    want_players, provide_players = equalizeCandidates(games)

    results = []

    if len(want_players) <= 0:
        return results

    consumer_index = 0
    for (game_id, serials) in provide_players:
        want_players.sort(key=lambda i: i[1])
        if want_players[0][1] == 0:
            #
            # All satisfied, stop looping
            #
            break

        while len(serials) > 0:
            distributed = False
            for _i in xrange(len(want_players)):
                consumer = want_players[consumer_index]
                consumer_index = (consumer_index+1) % len(want_players)
                if consumer[1] > 0:
                    consumer[1] -= 1
                    serial = serials.pop(0)
                    results.append(( game_id, consumer[0], serial ))
                    distributed = True
                    if len(serials) <= 0:
                        break
            if not distributed:
                break

    if log and len(results) > 0:
        log.inform("equalizeGame: %s", lambda: pformat(results))

    return results

def breakGames(games, log=None):
    if len(games) < 2:
        return []

    #
    # Games not running first, then games running.
    # Each is sorted with games that have least players first.
    #
    games = sorted(games, key=lambda game: (not game.isEndOrNull(), game.allCount()))

    to_break = [
        {
            "id": game.id,
            "seats_left": game.max_players-game.allCount(),
            "serials": game.serialsAll(),
            "to_add": [],
            "running": not game.isEndOrNull()
        } for game in games 
    ]

    if log: log.debug("breakGames: %s", to_break)
    results = []
    while True:
        result = breakGame(to_break[0], to_break[1:], log)
        to_break = [game for game in to_break[1:] if game["seats_left"] > 0]
        if result == False:
            break
        results.extend(result)
        if len(to_break) < 2:
            break

    if log and results: log.debug("breakGames: %s", lambda: pformat(results))

    return results

def breakGame(to_break, to_fill, log = None):
    #
    # Can't break a game in which players were moved.
    #
    if len(to_break["to_add"]) > 0 or to_break["running"]:
        return False
    
    seats_left = sum(game["seats_left"] for game in to_fill)
    serials = to_break["serials"]
    game_id = to_break["id"]
    #
    # Don't break a game if there is not enough seats at the
    # other games
    #
    if seats_left < len(serials):
        return False

    #
    # Fill the largest games first, in the hope that the smallest
    # games can be broken later.
    #
    to_fill.reverse()
    result = []
    for game in to_fill:
        if game["seats_left"] > 0:
            count = min(game["seats_left"], len(serials))
            game["to_add"].extend(serials[:count])
            game["seats_left"] -= count
            result.append((game_id, game["id"], serials[:count]))
            serials = serials[count:]
            if len(serials) <= 0:
                break

    return result

class PokerTournamentStats:
    def __init__(self,tourney):
        self._tourney = tourney
        self.chips_avg = 0
        self.chips_max = 0
        self.player_chips_max = {"serial": 0, "name": "noname"}
        self.players_active = 0
        self.players_money_rank = {}
        
    def update(self, game_id):
        active_player_ranks = []
        inactive_players = set(self._tourney.winners)
        for game in self._tourney.games:
            active_player_ranks.extend(
                player for (serial,player) in game.serial2player.iteritems() 
                if serial not in inactive_players
            )
        if not active_player_ranks:
            self._tourney.log.debug("updateStats: need players in games for tourney %d", self._tourney.serial)
            return False
        
        active_player_ranks.sort(key=lambda player: player.money, reverse=True)
        
        players_money_rank = dict(
            (player_serial, rank+1) for (rank,player_serial)
            in enumerate([player.serial for player in active_player_ranks] + self._tourney.winners)
        )
        
        self.chips_avg = sum(player.money for player in active_player_ranks) / len(active_player_ranks)
        self.chips_max = active_player_ranks[0].money
        self.player_chips_max = {
            "serial": active_player_ranks[0].serial, 
            "name": active_player_ranks[0].name
        }
        self.players_active = len(active_player_ranks)
        self.players_money_rank = players_money_rank
        
    def __call__(self,user_serial):
        if self.chips_avg == 0:
            self.update(self._tourney.games[0].id)
        ret = {
            "serial": user_serial,
            "tourney_serial": self._tourney.serial,
            "rank": self.players_money_rank.get(user_serial,0),   
            "chips_avg": self.chips_avg,
            "chips_max": self.chips_max,
            "players_active": self.players_active,
            "player_chips_max_serial": self.player_chips_max["serial"],
            "player_chips_max_name": self.player_chips_max["name"],
            "table_count": len(self._tourney.games),
        }
        return ret
        
class PokerTournament:

    log = log.get_child('PokerTournament')

    def __init__(self, *args, **kwargs):
        self.log = PokerTournament.log.get_instance(self, refs=[
            ('Tournament', self, lambda tournament: tournament.serial)
        ])
        self.name = kwargs.get('name', 'no name')
        self.description_short = kwargs.get('description_short', 'nodescription_short')
        self.description_long = kwargs.get('description_long', 'nodescription_long')
        self.serial = kwargs.get('serial', 1)
        self.players_quota = kwargs.get('players_quota', 10)
        self.players_min = kwargs.get('players_min', 2)
        self.variant = kwargs.get('variant', 'holdem')
        self.betting_structure = kwargs.get('betting_structure', 'level-15-30-no-limit')
        self.skin = kwargs.get('skin', 'default')
        self.dirs = kwargs.get('dirs', [])
        self.seats_per_game = kwargs.get('seats_per_game', 10)
        self.sit_n_go = kwargs.get('sit_n_go', 'y')
        self.register_time = kwargs.get('register_time', 0)
        self.start_time = kwargs.get('start_time', 0)
        self.last_registered = None
        self.breaks_first = kwargs.get('breaks_first', 7200)
        self.breaks_interval = kwargs.get('breaks_interval', 3600)
        self.breaks_duration = kwargs.get('breaks_duration', 300)
        self.breaks_running_since = -1
        self.breaks_since = -1
        self.breaks_count = 0
        self.buy_in = int(kwargs.get('buy_in', 0))
        self.rake = int(kwargs.get('rake', 0))
        self.rebuy_delay = kwargs.get('rebuy_delay', 0)
        self.add_on = kwargs.get('add_on', 0)
        self.add_on_delay = kwargs.get('add_on_delay', 60)
        self.inactive_delay = kwargs.get('inactive_delay', 300)
        self.prize_min = kwargs.get('prize_min', 0)
        self.prizes_specs = kwargs.get('prizes_specs', "table")
        self.rank2prize = None
        self.finish_time = -1
        if type(self.start_time) is StringType:
            self.start_time = int(time.mktime(time.strptime(self.start_time, "%Y/%m/%d %H:%M")))
        self.prefix = ""
        
        self.players = {}
        self.need_balance = False
        self.registered = 0
        self._rebuy_stack = set()
        
        self.winners_dict = {}
        self._winners_dict_tmp = {}
        self.state = kwargs.get("state", TOURNAMENT_STATE_ANNOUNCED)
        self.games = []
        self.id2game = {}
        self.stats = PokerTournamentStats(self)
        self._last_winner_position = 0
        
        self.callback_new_state = lambda tournament, old_state, new_state: True
        self.callback_create_game = lambda tournament: PokerGameServer("poker.%s.xml", tournament.dirs)
        # I think callback_game_filled() is a misnomer because it's not
        # about the table being "filled" (i.e., the table could have less
        # than the max seated at it).  What really happens is that the
        # callback_game_filled() is made when the table is deemed to have
        # the number of players at it the tourney manager has decided
        # belong there (which may or may not be "filled").
        self.callback_game_filled = lambda tournament, game: True
        self.callback_destroy_game = lambda tournament, game: True
        self.callback_move_player = lambda tournament, from_game_id, to_game_id, serial: self.movePlayer(from_game_id, to_game_id, serial)
        self.callback_remove_player = lambda tournament, game_id, serial, now: self.removePlayer(game_id, serial, now)
        self.callback_reenter_game = lambda tourney_serial, serial: True
        self.callback_cancel = lambda tournament: True
        self.callback_rebuy_payment = lambda tournament, serial, game_id, player_chips, tourney_chips: tourney_chips
        self.callback_rebuy = lambda tournament, serial, game_id, success, error: True 
        self.loadPayouts()

        if self.state == TOURNAMENT_STATE_ANNOUNCED:
            self.updateRegistering()
    
    def _getWinners(self):
        """returns a list of serials of players that already lost the game."""
        return [k for (k,_v) in sorted(self.winners_dict.iteritems(), key=lambda (a,b): (b,a), reverse=True)]

    def _setWinners(self, alist):
        """replaces the current winners list. alist is an iterable of player serials"""
        self.winners_dict = {}
        for i,e in enumerate(alist): self.winners_dict[e] = i

    winners = property(_getWinners, _setWinners)

    def _incrementToNextWinnerPosition(self):
        """increments the position to the next 'winner' (i.e. a person who left the game) and returns that position."""
        self._last_winner_position = max((len(self._winners_dict_tmp)+len(self.winners_dict)), (self._last_winner_position+1))
        return self._last_winner_position

    def finallyRemovePlayer(self, serial, now=False):
        """finallyRemovePlayer(serial) should be called right after the user is removed from the game.
        it is importent that it is called after the callback_remove_player was called
        """
        assert serial in self._winners_dict_tmp or now, 'player %d not found in winners_dict_tmp' % serial
        # 
        # pos_info is always (pos, lost_chips, tiebreaker). 
        # if the user was not in the winners_dict_tmp then the last two position don't matter
        pos_info = self._winners_dict_tmp.pop(serial) if serial in self._winners_dict_tmp else (self._incrementToNextWinnerPosition(), 0, 0)
        self.addWinner(serial, pos_info)

    def addWinner(self, serial, pos_info):
        """adds the serial to winnerslist"""
        assert serial not in self.winners_dict, 'player %d already part of the winners_dict' % serial
        self.winners_dict[serial] = pos_info

    def loadPayouts(self):
        self.prizes_object = pokerprizes.__dict__['PokerPrizes' + self.prizes_specs.capitalize()](buy_in_amount = self.buy_in, player_count = self.registered, guarantee_amount = self.prize_min, config_dirs = self.dirs)

    def canRun(self):
        if self.state != TOURNAMENT_STATE_LOADING and self.start_time < tournament_seconds():
            if self.sit_n_go == 'y' and self.registered >= self.players_quota:
                return True
            elif self.sit_n_go == 'n':
                if self.registered >= self.players_min:
                    return True
                else:
                    return None
            else:
                return False
        else:
            return False

    def getRebuyTimeRemaining(self):
        """returns the timeperiod (seconds) in which a user could perform a rebuy"""
        remainingTime = (self.start_time + self.rebuy_delay) - tournament_seconds()
        if remainingTime > 0:
            return int(remainingTime)
        else:
            return 0
        
    def remainingInactiveSeconds(self):
        if self.inactive_delay > 0:
            return int(self.start_time + self.inactive_delay - tournament_seconds())  
        else:
            return 0
        
    def isRebuyAllowed(self, serial="unknown"):
        """
        returns True if a rebuy is possible in this tourney at this moment.
        the optional parameter serial could be used for debug messages in case of an error
        """
        time_remaining = self.getRebuyTimeRemaining()
        if time_remaining > 0:
            return True
        else:
            explain = "start(%s), delay(%s) == remaining(%s)" %(self.start_time, self.rebuy_delay, time_remaining)
            self.log.warn("rebuy during tourney %s not allowed: player %s [%s]" % (self.serial, serial, explain),
                refs=[('User', serial, int)])
            return False

    def isRebuyAllowedForUser(self, serial, game):
        """return True if User could rebuy but ignores if tourney would allow a rebuy"""
        maximum = game.maxBuyIn() - (game.getPlayerMoney(serial) + game.buyIn())
        if maximum < 0:
            self.log.warn("player %d can't bring more money to the table", serial, refs=[('User', serial, int), ('Game', game.id, int)])
            return False
        return True

    def getRank(self, serial):
        try:
            winners_count = len(self.winners)
            rank_first = self.registered - winners_count
            return self.winners.index(serial) + rank_first + 1
        except:
            return -1
        
    def updateRegistering(self):
        if self.state == TOURNAMENT_STATE_ANNOUNCED:
            now = tournament_seconds()
            if now - self.register_time > 0.0:
                self.changeState(TOURNAMENT_STATE_REGISTERING)
                return -1
            else:
                return self.register_time - now
        else:
            self.log.inform("updateRegistering: should not be called while tournament is not in announced state")
            return -1

    def updateRunning(self):
        if self.state == TOURNAMENT_STATE_REGISTERING:
            ready = self.canRun()
            if ready == True:
                self.changeState(TOURNAMENT_STATE_RUNNING)
            elif ready == None:
                self.changeState(TOURNAMENT_STATE_CANCELED)
            elif ready == False:
                pass

    def remainingBreakSeconds(self):
        if self.breaks_since > 0:
            return self.breaks_duration - ( tournament_seconds() - self.breaks_since )
        else:
            return None

    def updateBreak(self, game_id = None):
        if self.breaks_duration <= 0:
            return False

        if self.state == TOURNAMENT_STATE_RUNNING:
            running_duration = tournament_seconds() - self.breaks_running_since
            if self.breaks_count > 0:
                running_max = self.breaks_interval
            else:
                running_max = self.breaks_first

            if running_duration >= running_max:
                self.breaks_games_id = [g.id for g in self.games if g.isEndOrNull() and g.id != game_id]
                self.changeState(TOURNAMENT_STATE_BREAK_WAIT)
                
        if self.state == TOURNAMENT_STATE_BREAK_WAIT:
            #
            # game_id is 0 when updateBreak is called after a table was destroyed
            # as a side effect of balanceGames
            if game_id > 0:
                self.breaks_games_id.append(game_id)
            on_break = True
            for game in self.games:
                #
                # games with a single player must not be taken into account because
                # nothing happens on them. Either it is the last game with a single
                # player and must be considered ready to enter the break. Or there
                # are still other tables playing and the game with a single player
                # may be broken and the player moved to another table when the hand
                # finishes at one of the other tables.
                #
                # If the games with a single player are not ignored, a two game
                # tournament would enter a deadlock in the following situation:
                #        1) table T1 finishes its hand and only has one player left
                #           tournament is not on BREAK_WAIT
                #        2) tournament break time is reached
                #        3) table T2 finishes its hand, no player is busted.
                #           endTurn is called and tournament enters BREAK_WAIT
                #           T2 is added to the list of tables for which there
                #           is not need to wait before declaring the tournament
                #           on break. Because T1 has only one player left and
                #           all other tables are expecting the break (i.e. no
                #           hand will be played), it can be added to the list
                #           of tables ready for the break.
                if game.id not in self.breaks_games_id and len(game.playersAll()) > 1:
                    on_break = False
                    break
            if on_break:
                del self.breaks_games_id
                self.changeState(TOURNAMENT_STATE_BREAK)

        if self.state == TOURNAMENT_STATE_BREAK:
            if self.remainingBreakSeconds() <= 0:
                self.breaks_count += 1
                self.changeState(TOURNAMENT_STATE_RUNNING)

        if self.state not in (TOURNAMENT_STATE_RUNNING, TOURNAMENT_STATE_BREAK_WAIT, TOURNAMENT_STATE_BREAK):
            self.log.inform("updateBreak is not supposed to be called while in state %s", self.state)
            return None
        
        return True

    def changeState(self, state):
        if self.state == state:
            return
        if self.state == TOURNAMENT_STATE_ANNOUNCED and state == TOURNAMENT_STATE_REGISTERING:
            pass
        elif self.state == TOURNAMENT_STATE_RUNNING and state == TOURNAMENT_STATE_BREAK_WAIT:
            pass
        elif self.state == TOURNAMENT_STATE_BREAK_WAIT and state == TOURNAMENT_STATE_BREAK:
            self.breaks_since = tournament_seconds()
        elif self.state == TOURNAMENT_STATE_BREAK and state == TOURNAMENT_STATE_RUNNING:
            self.breaks_since = -1
            self.breaks_running_since = tournament_seconds()
        elif self.state == TOURNAMENT_STATE_REGISTERING and state == TOURNAMENT_STATE_RUNNING:
            self.start_time = tournament_seconds()
            self.breaks_running_since = self.start_time
            self.createGames()
        elif self.state == TOURNAMENT_STATE_REGISTERING and state == TOURNAMENT_STATE_CANCELED:
            self.cancel()
            self.finish_time = tournament_seconds()
        elif self.state in (TOURNAMENT_STATE_RUNNING, TOURNAMENT_STATE_BREAK_WAIT, TOURNAMENT_STATE_BREAK) and state == TOURNAMENT_STATE_COMPLETE:
            self.finish_time = tournament_seconds()
        else:
            self.log.inform("changeState: cannot change from state %s to state %s", self.state, state)
            return
        self.log.debug("state change %s => %s", self.state, state)
        old_state = self.state
        self.state = state
        self.callback_new_state(self, old_state, self.state)

    def isRegistered(self, serial):
        return serial in self.players
        
    def canRegister(self, serial):
        if self.state in (TOURNAMENT_STATE_REGISTERING, TOURNAMENT_STATE_LOADING) and self.registered < self.players_quota:
            return not self.isRegistered(serial)
        else:
            return False

    def canUnregister(self, serial):
        return self.isRegistered(serial) and self.state == TOURNAMENT_STATE_REGISTERING
        
    def register(self, serial, name=None):
        if self.canRegister(serial):
            self.players[serial] = name
            self.registered += 1
            self.rank2prize = None
            self.prizes_object.addPlayer()
            if self.state == TOURNAMENT_STATE_REGISTERING:
                self.updateRunning()
            if self.state == TOURNAMENT_STATE_RUNNING:
                self.sitPlayer(serial)
            self.last_registered = tournament_seconds()
            return True
        else:
            return False

    def unregister(self, serial):
        if self.canUnregister(serial):
            del self.players[serial]
            self.registered -= 1
            if self.registered == 0:
                self.last_registered = None
            self.prizes_object.removePlayer()
            self.rank2prize = None
            return True
        else:
            return False

    def cancel(self):
        if self.state == TOURNAMENT_STATE_REGISTERING:
            self.callback_cancel(self)
            self.players = {}
            self.registered = 0
            return True
        else:
            return False
        
    def sitPlayer(self, serial):
        pass

    def removePlayer(self, game_id, serial, now=False):
        game = self.id2game[game_id]
        game.removePlayer(serial)
        self.finallyRemovePlayer(serial, now=now)

    def movePlayer(self, from_game_id, to_game_id, serial):
        from_game = self.id2game[from_game_id]
        to_game = self.id2game[to_game_id]
        from_game.open()
        to_game.open()
        from_player = from_game.getPlayer(serial)
        to_game.addPlayer(serial,name=from_player.name)
        to_player = to_game.getPlayer(serial)
        to_game.payBuyIn(serial, from_player.money)
        to_game.sit(serial)
        to_game.autoBlindAnte(serial)
        to_player.name = from_player.name
        to_player.auto_policy = from_player.auto_policy
        to_player.setUserData(from_player.getUserData())
        if(from_player.isSitOut()): to_game.sitOut(serial)
        if(from_player.isAuto()): to_game.autoPlayer(serial)
        if(from_player.isBot()): to_game.botPlayer(serial)
        from_game.removePlayer(serial)
        from_game.close()
        to_game.close()
    
    def createGames(self):
        games_count = int(ceil(self.registered / float(self.seats_per_game)))
        self.players_quota = games_count * self.seats_per_game
        players = list(self.players.iteritems()) 
        shuffler.shuffle(players)
        for game_id in xrange(1, games_count + 1):
            game = self.callback_create_game(self)
            game.setTime(0)
            game.setVariant(self.variant)
            game.setBettingStructure(self.betting_structure)
            game.setMaxPlayers(self.seats_per_game)
            if game.id == 0: game.id = game_id

            buy_in = game.buyIn()
            for _seat in xrange(self.seats_per_game):
                if not players: break
                serial, name = players.pop()
                game.addPlayer(serial, name=name)
                game.payBuyIn(serial, buy_in)
                game.sit(serial)
                game.autoBlindAnte(serial)
                
            self.games.append(game)
        self.id2game = dict((game.id,game) for game in self.games)
        # Next, need to call balance games, because the table assignment
        # algorithm above does not account for scenarios where the last
        # few people end up a table too small.
        self.balanceGames()
        # Next, we can now notify via callback that all the games in
        # self.games have been "filled".
        for game in self.games:
            self.callback_game_filled(self, game)
            game.close()
    
    def reenterGame(self, game_id, serial):
        """
        reenterGame(game_id, serial) will be called when a player buys in. So he could reenter the game.
        This function gets called by the table.
        """
        if serial in self._winners_dict_tmp:
            del self._winners_dict_tmp[serial]
        game = self.id2game[game_id]
        game.sit(serial)
        self.callback_reenter_game(self.serial, serial)

    def isRebuying(self, serial):
        return serial in self._rebuy_stack
    
    def serialsRebuying(self, game_id):
        try:
            game = self.id2game[game_id]
            serials_rebuying = set(game.serialsAll()) & self._rebuy_stack
            return serials_rebuying
        except KeyError:
            self.log.warn("serialsRebuying: game_id %d not found", game_id)
            return set()
    
    def rebuyPlayerRequest(self, game_id, serial):
        game = self.id2game[game_id]
        
        if not self.isRebuyAllowed(serial):
            return False, TOURNAMENT_REBUY_ERROR_TIMEOUT
        
        if not self.isRebuyAllowedForUser(serial, game):
            return False, TOURNAMENT_REBUY_ERROR_USER
        
        if serial in self._rebuy_stack:
            return False, TOURNAMENT_REBUY_ERROR_OTHER
        
        if game.isRebuyPossible():
            success, error = self._rebuy(game_id, serial)
            return success, error
        
        self._rebuy_stack.add(serial)
        return True, None
    
    def rebuyAllPlayers(self, game_id):
        serials_rebuying = self.serialsRebuying(game_id)
        
        for serial in serials_rebuying:
            self._rebuy_stack.remove(serial)
            self._rebuy(game_id, serial)
        
    def _rebuy(self, game_id, serial):
        """
        performs a tourney rebuy for the player with the given serial

        returns a tuple (success_state, reason)

        success_state is either True or False
        game_id is the game_id if the success_state is True otherwise None
        reason is None if success_state is True otherwise a short StringType

        e.g. (True, None) # successful returncode
             (False, "money") # unsuccessful, the user has not enough money
        """
        error = None
        game = self.id2game[game_id]

        if not self.isRebuyAllowed(serial):
            error = TOURNAMENT_REBUY_ERROR_TIMEOUT

        elif not self.isRebuyAllowedForUser(serial, game):
            error = TOURNAMENT_REBUY_ERROR_USER

        else:
            amount = self.callback_rebuy_payment(self, serial, game_id, self.buy_in+self.rake, game.buyIn())
        
            if amount == 0:
                self.log.warn("player %d  has not enough money, tourney rebuy denied", serial, refs=[('User', serial, int), ('Game', game_id, int)])
                error = TOURNAMENT_REBUY_ERROR_MONEY
    
            elif not game.rebuy(serial, game.buyIn()):
                # This should never happen! We need to give the user the money back
                # and the winner of the tourney would get too much chips
                self.log.error("rebuy denied for user %s" % serial, refs=[('User', serial, int), ('Game', game_id, int)])
                error = TOURNAMENT_REBUY_ERROR_OTHER
                
            else:
                self.reenterGame(game_id, serial)
                self.prizes_object.rebuy()
        
        success = error is None
        self.callback_rebuy(self, serial, game_id, success, error)
        return success, error


    def removeBrokePlayers(self, game_id, now=False):
        """removeBrokePlayers(game_id) returns amount of broke players"""
        game = self.id2game[game_id]
        loosers = game.serialsBroke()
        pos = self._incrementToNextWinnerPosition()
        new_loosers = [s for s in loosers if s not in self._winners_dict_tmp]
        
        if new_loosers:
            self.log.debug('removeBrokePlayers: serials: %s. game_id: %d. now: %s', new_loosers, game_id, now)
        
        randlist = range(len(new_loosers))
        shuffler.shuffle(randlist)
        
        # the person who had more money before the all in should get a higher rank
        # if the amount is equal, use a 'random card', in this case the tiebreaker
        # as a means to differentiate between positions
        values = dict(
            (serial, (pos, -game.showdown_stack[0]['serial2delta'][serial], tiebreaker)) 
            for (serial,tiebreaker) in zip(new_loosers, randlist)
        )
        
        new_loosers.sort(key=lambda i: values[i])
        
        if not now:
            for serial in new_loosers:
                self._winners_dict_tmp[serial] = values[serial]
                
        for serial in new_loosers:
            self.callback_remove_player(self, game_id, serial, now=now)
            
        if loosers:
            self.need_balance = True

        return len(loosers)

    def removeInactivePlayers(self, game_id):
        game = self.id2game[game_id]
        inactive_players = game.serialsInactive()
        
        # if all players are inactive, the last player will not be removed
        if len(inactive_players) == len(game.serialsAll()):
            inactive_players.pop()
        
        if inactive_players:
            self.log.debug('removeInactivePlayers: serials: %s. game_id: %d.', inactive_players, game_id)
        
        for serial in inactive_players:
            self.callback_remove_player(self, game_id, serial, now=True)
            
        if inactive_players:
            self.need_balance = True
            
        return len(inactive_players)
        
    def endTurn(self, game_id):
        """endTurn(game_id) is called by the game each time a hand ends."""
        players_removed = 0
        
        if self.remainingInactiveSeconds() < 0: 
            players_removed += self.removeInactivePlayers(game_id)

        # if the tourney ended after removing all inactive players, there are no games
        # anymore, so we have to explicitely check this scenario.
        if game_id in self.id2game:
            players_removed += self.removeBrokePlayers(game_id)
        
        return players_removed

    def tourneyEnd(self, game_id):
        if game_id not in self.id2game:
            self.log.error("tourneyEnd: game %d not available. available games: %s",game_id,sorted(self.id2game))
            return
        game = self.id2game[game_id]
        loosers = game.serialsBroke()
        if len(self.winners) + 1 == self.registered:
            game = self.games[0]
            remainingPlayers = game.playersAll()
            player = remainingPlayers[0]
            self.callback_remove_player(self, game.id, player.serial, now=True)
            player.money = 0
            self.log.debug("winners %s", self.winners)
            self.callback_destroy_game(self, game)
            self.games = []
            self.id2game = {}
            self.changeState(TOURNAMENT_STATE_COMPLETE)
            return False
        else:
            if self.need_balance or loosers:
                self.balanceGames()
            if game_id in self.id2game:
                self.updateBreak(game_id)
            else:
                # this happens if game_id was destroyed by the call to balanceGames above
                self.updateBreak(0)
            return True
        
    def balanceGames(self):
        self.need_balance = False
        if len(self.games) < 2: return
        self.log.debug("balanceGames")
        to_break = breakGames(self.games, self.log)
        games_broken = {}
        for (from_id, to_id, serials) in to_break:
            for serial in serials:
                self.log.debug("balanceGames: player %d moved from %d to %d", serial, from_id, to_id)
                if self.state == TOURNAMENT_STATE_REGISTERING:
                    self.movePlayer(from_id, to_id, serial)
                else:
                    self.callback_move_player(self, from_id, to_id, serial)
            games_broken[from_id] = True

        if len(to_break) > 0:
            for game_id in games_broken.keys():
                game = self.id2game[game_id]
                self.callback_destroy_game(self, game)
                self.games.remove(game)
                del self.id2game[game.id]
            self.log.inform("balanceGames: broken tables %s", to_break)
            return True
        
        to_equalize = equalizeGames(self.games, self.log)
        for (from_id, to_id, serial) in to_equalize:
            self.log.debug("balanceGames: player %d moved from %d to %d", serial, from_id, to_id)
            if self.state == TOURNAMENT_STATE_REGISTERING:
                self.movePlayer(from_id, to_id, serial)
            else:
                self.callback_move_player(self, from_id, to_id, serial)

        want_players, provide_players = equalizeCandidates(self.games)
        self.need_balance = bool(want_players and not provide_players)
        if self.need_balance:
            self.log.debug("balanceGames: postponed game equalization")
        
        return len(to_equalize) > 0

    def prizes(self):
        if not self.rank2prize or self.prizes_object.changed:
            self.rank2prize = self.prizes_object.getPrizes()
        return self.rank2prize
