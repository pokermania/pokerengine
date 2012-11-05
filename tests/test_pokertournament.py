#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2009 Bradley M. Kuhn <bkuhn@ebb.org>
# Copyright (C) 2006 Mekensleep <licensing@mekensleep.com>
#                    26 rue des rosiers, 75004 Paris
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
#  Pierre-Andre (05/2006)
#  Loic Dachary <loic@dachary.org>
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

import time

class ConstantPlayerShuffler:
    def shuffle(self, what):
        what.sort()

from tests.testmessages import get_messages, clear_all_messages

from pokerengine import pokertournament
from pokerengine import pokerprizes
pokertournament.shuffler = ConstantPlayerShuffler()

import reflogging
log = reflogging.root_logger.get_child('test-pokertournament')

class PokerTournamentTestCase(unittest.TestCase):
    
    TestConfDirectory = path.join(TESTS_PATH, '../conf')
        
    # ---------------------------------------------------------
    def setUp(self):
        self.dirs = [PokerTournamentTestCase.TestConfDirectory]
    
    # -------------------------------------------------------
    def tearDown(self):
        pass
        
    # -------------------------------------------------------
    def testTournamentDefaultInitialisation(self):
        """Test Poker Tournament : Default initialisation"""
        
        arguments = {
            'dirs': self.dirs,
            'name': 'no name',
            'description_short': 'nodescription_short',
            'description_long': 'nodescription_long',
            'serial': 1,
            'players_quota': 10,
            'variant': 'holdem',
            'betting_structure': 'level-15-30-no-limit',
            'seats_per_game': 10,
            'sit_n_go': 'y',
            'register_time': 0,
            'start_time': 0,
            'breaks_interval': 60,
            'rebuy_delay': 0,
            'add_on': 0,
            'add_on_delay': 60,
            'prizes_specs': 'table'
        }
        
        tournament = pokertournament.PokerTournament(**arguments)
        for attribute, value in arguments.items():
            self.failUnlessEqual(getattr(tournament,attribute), value)
            
        self.failUnlessEqual(tournament.players, {})
        self.failUnlessEqual(tournament.winners, [])
        self.failIf(tournament.need_balance)
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        self.failUnlessEqual(tournament.registered, 0)
        
            
    # -------------------------------------------------------
    def testTournamentInitialisation(self):
        """Test Poker Tournament : Initialisation"""
        
        arguments = {
            'dirs': self.dirs,
            'name': 'Test',
            'description_short': 'ShortDescription',
            'description_long': 'LongDescription',
            'serial': 3,
            'players_quota': 20,
            'variant': 'variant',
            'betting_structure': 'config',
            'seats_per_game': 2,
            'sit_n_go': 'n',
            'register_time': time.time() + 60,
            'start_time': '2006/04/22 12:00',
            'breaks_interval': 120,
            'rebuy_delay': 30,
            'add_on': 10,
            'add_on_delay': 120,
            'prizes_specs': 'table'
        } 
            
        tournament = pokertournament.PokerTournament(**arguments)
        for attribute, value in arguments.items():
            if attribute == 'start_time':
                value = int(time.mktime(time.strptime(value, "%Y/%m/%d %H:%M")))
            self.failUnlessEqual(getattr(tournament,attribute), value)
            
        self.failUnlessEqual(tournament.players, {})
        self.failUnlessEqual(tournament.winners, [])
        self.failIf(tournament.need_balance)
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_ANNOUNCED)
        self.failUnlessEqual(tournament.registered, 0)
        
        # TODO Payout
        
    # -------------------------------------------------------
    def testUpdateRegistering(self):
        """Test Poker Tournament : Update registering"""
        
        arguments = {
            'dirs': self.dirs,
            'register_time': time.time() + 3,
        }                                
        
        tournament = pokertournament.PokerTournament(**arguments)
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_ANNOUNCED)
        self.failUnless((tournament.register_time - time.time()) > 0.0)
        self.failUnless(tournament.updateRegistering() > 0.0)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_ANNOUNCED)
        
        time.sleep(4)
        self.failIf((tournament.register_time - time.time()) > 0.0)
        self.failUnlessEqual(tournament.updateRegistering(), -1)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        self.failUnlessEqual(tournament.updateRegistering(), -1)
        
    # -------------------------------------------------------
    def testRegister(self):
        """Test Poker Tounament : Register"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 25,
            'players_min': 20,
            'start_time': time.time() + 20000,
            'sit_n_go': 'n', 
        }                                
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # The tournament has been created and players can be regsitered
        self.failUnlessEqual(tournament.players, {})
        self.failUnlessEqual(tournament.registered, 0)
        
        # The player 1 can be registered
        self.failIf(tournament.isRegistered(1))
        self.failUnless(tournament.canRegister(1))
        
        # Register the player
        self.failUnless(tournament.register(1))
        self.failUnlessEqual(tournament.players, {1:None})
        self.failUnlessEqual(tournament.registered, 1)
        self.failUnless(tournament.isRegistered(1))
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        # The player 1 can be registered
        self.failIf(tournament.isRegistered(2))
        self.failUnless(tournament.canRegister(2))
        
        # Register the player
        self.failUnless(tournament.register(2,'player2'))
        self.failUnlessEqual(tournament.players, {1:None, 2:'player2'})
        self.failUnlessEqual(tournament.registered, 2)
        self.failUnless(tournament.isRegistered(2))
        
        # Change the tournament state
        tournament.changeState(pokertournament.TOURNAMENT_STATE_RUNNING)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_RUNNING)
        # Players can not be regsitered
        self.failIf(tournament.canRegister(3))
        self.failIf(tournament.register(3))

    # -------------------------------------------------------
    def testChangeState(self):
        """Test Poker Tournament : Change state"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 5,
            'sit_n_go': 'n', 
        }                                
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Iniitalize state to TOURNAMENT_STATE_ANNOUNCED
        tournament.state = pokertournament.TOURNAMENT_STATE_ANNOUNCED
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_ANNOUNCED)
        
        # Go to state TOURNAMENT_STATE_REGISTERING
        tournament.changeState(pokertournament.TOURNAMENT_STATE_REGISTERING)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        # Try to go return to TOURNAMENT_STATE_ANNOUNCED
        tournament.changeState(pokertournament.TOURNAMENT_STATE_ANNOUNCED)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        # Go to state TOURNAMENT_STATE_RUNNING
        tournament.changeState(pokertournament.TOURNAMENT_STATE_RUNNING)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_RUNNING)
        
        # Go to state TOURNAMENT_STATE_COMPLETE
        tournament.changeState(pokertournament.TOURNAMENT_STATE_COMPLETE)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_COMPLETE)
        
        
    # -------------------------------------------------------
    def testCanUnregister(self):
        """Test Poker Tounament : Can unregister"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 2,
            'sit_n_go': 'y',
        }                                
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        self.failIf(tournament.canUnregister(1))
        
        self.failUnless(tournament.register(1))
        self.failUnless(tournament.canUnregister(1))
        
        self.failUnless(tournament.register(2))
        
        self.failIfEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        self.failIf(tournament.canUnregister(1))
        
    # -------------------------------------------------------
    def testUnregister(self):
        """Test Poker Tounament : Unregister"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 2,
            'sit_n_go': 'y',
        }                                
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        self.failUnless(tournament.register(1))
        self.failUnlessEqual(tournament.players, {1:None})
        self.failUnlessEqual(tournament.registered, 1)
        
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        self.failUnless(tournament.unregister(1))
        self.failUnlessEqual(tournament.players, {})
        self.failUnlessEqual(tournament.registered, 0)
        
        self.failUnless(tournament.register(1))
        self.failUnless(tournament.register(2))
        self.failIfEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        self.failIf(tournament.unregister(1))
        
    # -------------------------------------------------------
    def testCreateGames(self):
        """Test Poker Tournament : Create games"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 10,
            'players_min': 10,
            'start_time': time.time() + 20000,
            'seats_per_game': 3,
            'sit_n_go': 'n',
            'variant': 'holdem',
            'betting_structure': 'level-15-30-no-limit',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        nplayers = 9
        for player in xrange(1,nplayers+1):
            self.failUnless(tournament.register(player))
            
        self.failUnlessEqual(tournament.registered, nplayers)
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_REGISTERING)
        
        self.failUnlessEqual(tournament.id2game, {})
        
        tournament.createGames()
        self.failUnlessEqual(len(tournament.id2game), nplayers / tournament.seats_per_game)
        self.failUnlessEqual(len(tournament.games), nplayers / tournament.seats_per_game)
        
        id = 1
        for game in tournament.games:
            self.failUnlessEqual(game.max_players, tournament.seats_per_game)
            self.failUnlessEqual(game.allCount(), tournament.seats_per_game)
            self.failUnlessEqual(game.variant, 'holdem')
            self.failUnlessEqual(game.id, id)
            id += 1
            
            for serial in game.serial2player:
                self.failUnless(game.serial2player[serial].isSit())
                self.failUnless(game.serial2player[serial].isBuyInPayed())
                self.failUnless(game.serial2player[serial].isAutoBlindAnte())

            self.failIf(game.is_open)
            
    # -------------------------------------------------------
    def testPrizesSnG(self):
        """Test Poker Tournament : Prizes for SnG tournaments"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'buy_in': 100,
            'seats_per_game': 2,
            'sit_n_go': 'y',
            'prizes_specs': 'table',
        }

        tournament = pokertournament.PokerTournament(**arguments)
        prizes = tournament.prizes()
        self.failUnless(tournament.register(1))
        self.assertNotEquals(prizes, tournament.prizes())
        self.failUnless(tournament.unregister(1))
        self.assertEquals(prizes, tournament.prizes())

    # -------------------------------------------------------
    def testPrizesGuaranteeAmount(self):
        """Test Poker Tournament : Prizes for tournaments with guarantee amount"""

        prize_min = 1000
        arguments = {
            'dirs': self.dirs,
            'players_quota': 2,
            'buy_in': 100,
            'seats_per_game': 2,
            'prize_min': prize_min,
            'start_time': time.time() + 20000,
            'sit_n_go': 'n',
            'prizes_specs': 'table',
        }

        tournament = pokertournament.PokerTournament(**arguments)
        self.assertEquals(prize_min, tournament.prizes()[0])

    # -------------------------------------------------------
    def testPrizesRegular(self):
        """Test Poker Tournament : Prizes for regular tournaments"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 40,
            'buy_in': 100,
            'start_time': time.time() + 20000,
            'seats_per_game': 2,
            'sit_n_go': 'n',
            'prizes_specs': 'table',
        }

        #
        # PrizesTable
        #
        tournament = pokertournament.PokerTournament(**arguments)
        for player in range(1, 21):
            self.failUnless(tournament.register(player))
        self.failUnlessEqual(tournament.registered, 20)
        p = pokerprizes.__dict__['PokerPrizesTable'](buy_in_amount = 100, player_count = 20, config_dirs = self.dirs)
        self.failUnlessEqual(tournament.prizes_object.player_count, p.player_count)
        self.failUnlessEqual(tournament.prizes_object.buy_in, p.buy_in)
        self.failUnlessEqual(tournament.prizes(), p.getPrizes())

        #
        # register/unregister updates the prizes a new player
        #
        self.assertEquals(True, tournament.register(21))
        self.failUnlessEqual(tournament.registered, 21)
        self.failIfEqual(tournament.prizes(), p.getPrizes())
        tournament.unregister(21)
        self.failUnlessEqual(tournament.prizes(), p.getPrizes())
        
        #
        # PrizesAlgorithm
        #
        arguments['prizes_specs'] = 'algorithm'
        tournament = pokertournament.PokerTournament(**arguments)
        for player in range(20):
            self.failUnless(tournament.register(player))
        p = pokerprizes.__dict__['PokerPrizesAlgorithm'](buy_in_amount = 100, player_count = 20)
        self.failUnlessEqual(tournament.prizes_object.player_count, p.player_count)
        self.failUnlessEqual(tournament.prizes_object.buy_in, p.buy_in)
        self.failUnlessEqual(tournament.prizes(), p.getPrizes())

        #
        # Invalid prizes_specs
        #
        arguments['prizes_specs'] = 'invalid'
        caught = False
        try:
            tournament = pokertournament.PokerTournament(**arguments)
        except Exception, e:
            caught = True
            self.failUnless('PokerPrizesInvalid' in str(e))
        self.assertTrue(caught)

        return

    # -------------------------------------------------------
    def testMovePlayer(self):
        """Test Poker Tournament : Move player"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 25,
            'players_min': 20,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        for player in range(12):
            self.failUnless(tournament.register(player))
            
        tournament.createGames()
        tournament.removePlayer(tournament.games[0].id, tournament.games[0].serialsAll()[0], now=True)
        move = pokertournament.equalizeGames(tournament.games)
        self.failUnlessEqual(move, [(2, 1, 3), (3, 1, 0), (3, 1, 1)])
        
        from_game = tournament.id2game[move[0][0]]
        to_game = tournament.id2game[move[0][1]]
        
        player = from_game.getPlayer(move[0][2])
        player.name = 'Player'
        player.setUserData('UserData')
        player.sit_out = True
        player.bot = True
        
        self.failUnlessEqual(from_game.allCount(), 4)
        self.failUnlessEqual(to_game.allCount(), 2)
        
        tournament.movePlayer(from_game.id, to_game.id, player.serial)
        
        self.failUnlessEqual(from_game.allCount(), 3)
        self.failUnlessEqual(to_game.allCount(), 3)
        
        player = to_game.getPlayer(move[0][2])
        self.failUnlessEqual(player.name, 'Player')
        self.failUnlessEqual(player.getUserData(), 'UserData')
        self.failUnless(player.isSitOut())
        self.failUnless(player.isBot())
        
    # -------------------------------------------------------
    def testEqualizeCandidates(self):
        """Test Poker Tournament : Equalize candidates"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'players_min': 15,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        for player in range(12):
            self.failUnless(tournament.register(player))
            
        tournament.createGames()
            
        want, provide = pokertournament.equalizeCandidates(tournament.games)
        
        # Since balanceGames() is called by createGames(), we should find
        # these results.

        self.failUnlessEqual(len(want), 0)
        self.failUnlessEqual(len(provide), 3)
        self.failUnlessEqual(want, [])
        self.failUnlessEqual(provide,  [(1, []), (2, [3]), (3, [0, 1])])

        # Remove one from three and he should have one fewer to provide
        tournament.removePlayer(tournament.games[2].id, tournament.games[2].serialsAll()[0], now=True)

        want, provide = pokertournament.equalizeCandidates(tournament.games)
        self.failUnlessEqual(len(want), 0)
        self.failUnlessEqual(len(provide), 3)
        self.failUnlessEqual(provide,  [(1, []), (2, [3]), (3, [1])])
    # -------------------------------------------------------
    def testEqualizeGames(self):
        """Test Poker Tournament : Equalize games"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 25,
            'players_min': 20,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        # Tournament => 2 complete games (6 players)
        tournament = pokertournament.PokerTournament(**arguments)
        for player in range(10):
            self.failUnless(tournament.register(player))
            
        # Create games
        tournament.createGames()

        # Check games
        self.failUnlessEqual(len(tournament.games), 2) 
        self.failUnlessEqual(tournament.games[0].allCount(), 5)
        self.failUnlessEqual(tournament.games[1].allCount(), 5)
        
        # No need to equalize game
        self.failUnlessEqual(pokertournament.equalizeGames(tournament.games), [])
        
        # Tournament => 3 , has two tables of 3, then two tables of 5 
        tournament = pokertournament.PokerTournament(**arguments)
        for player in range(16):
            self.failUnless(tournament.register(player))
            
        # Create games
        tournament.createGames()

        # Check games
        self.failUnlessEqual(len(tournament.games), 4) 
        self.failUnlessEqual(tournament.games[0].allCount(), 3)
        self.failUnlessEqual(tournament.games[1].allCount(), 3)
        self.failUnlessEqual(tournament.games[2].allCount(), 5)
        self.failUnlessEqual(tournament.games[3].allCount(), 5)
        
        # Nothing to equalize at first
        self.failUnlessEqual(pokertournament.equalizeGames(tournament.games), [])

        # Remove one player from first table, means players from 3 must be redistributed
        tournament.removePlayer(tournament.games[0].id, tournament.games[0].serialsAll()[0], now=True)
        self.failUnlessEqual(pokertournament.equalizeGames(tournament.games), [(3, 1, 1), (3, 1, 2), (4, 1, 0)])
        
    # -------------------------------------------------------
    def testBreakGame(self):
        """Test Poker Tournament : Break game"""
        
        to_break = {
            'id': 1,
            'to_add': [],
            'running': True,
            'seats_left': 0,
            'serials': [1, 2]
        }
                                
        to_fill_1 = {
            'id': 2,
            'to_add': [],
            'running': False,
            'seats_left': 2,
            'serials': [3, 4]
        }
                        
        to_fill_2 = {
            'id': 3,
            'to_add': [],
            'running': False,
            'seats_left': 2,
            'serials': [5, 6]
        }
                            
        self.failIf(pokertournament.breakGame(to_break, [to_fill_1]))
        
        to_break['to_add'] = [2]
        to_break['running'] = False
        self.failIf(pokertournament.breakGame(to_break, [to_fill_1]))
        
        to_break['to_add'] = []
        to_break['running'] = True
        self.failIf(pokertournament.breakGame(to_break, [to_fill_1]))
        
        to_break['running'] = False
        to_fill_1['seats_left'] = len(to_break['serials']) - 1
        self.failIf(pokertournament.breakGame(to_break, [to_fill_1]))
        
        to_fill_1['seats_left'] = len(to_break['serials'])
        self.failUnlessEqual(pokertournament.breakGame(to_break, [to_fill_1]), [(1, 2, [1, 2])])
        
        to_fill_1['seats_left'] = len(to_break['serials']) - 1
        to_fill_2['seats_left'] = 1
        self.failUnlessEqual(pokertournament.breakGame(to_break, [to_fill_1, to_fill_2]), [(1, 3, [1]), (1, 2, [2])])

    # -------------------------------------------------------
    def testBreakGames(self):
        """Test Poker Tournament : Break games"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 50,
            'players_min': 25,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        for player in range(12):
            self.failUnless(tournament.register(player))
            
        tournament.createGames()
        
        self.failUnlessEqual(len(tournament.games), 3) 
        
        self.failUnlessEqual(tournament.games[0].allCount(), 3)
        self.failUnlessEqual(tournament.games[1].allCount(), 4)
        self.failUnlessEqual(tournament.games[2].allCount(), 5)

        # This remove leaves us with 2, 4, 5, which means that nothing can be broken.
        tournament.removePlayer(tournament.games[0].id, tournament.games[0].serialsAll()[0], now=True)
        self.failUnlessEqual(pokertournament.breakGames(tournament.games), [])

        # This will leave us with 2, 4, 4, which means table 0 can be broken, and one player
        #  wil be sent to each table.
        tournament.removePlayer(tournament.games[2].id, tournament.games[2].serialsAll()[0], now=True)

        player1 = tournament.games[0].serialsAll()[0]
        player2 = tournament.games[0].serialsAll()[1]
        
        self.failUnlessEqual(pokertournament.breakGames(tournament.games), 
                             [(1, 3, [player1]), (1, 2, [player2])])
        
        # Impossible to break less than 2 game
        self.failUnlessEqual(pokertournament.breakGames([tournament.games[0]]), [])
        
    def testBalanceGamesRunning(self):
        """Test Poker Tournament : Balance games when state RUNNING"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'players_min': 15,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(12):
            self.failUnless(tournament.register(player))
        
        # Note: balanceGames() is called by createGames() so initially,
        # the tables will be balanced as 3 players at first table, 4 at
        # second, and 5 at third.  (This doesn't sound all that balanced,
        # but it's consistent with the algorithm in
        # pokertournament.equalizeGames()

        tournament.createGames()
        tournament.state = pokertournament.TOURNAMENT_STATE_RUNNING
        self.failUnlessEqual(len(tournament.games[0].serialsAll()), 3)
        self.failUnlessEqual(len(tournament.games[1].serialsAll()), 4)
        self.failUnlessEqual(len(tournament.games[2].serialsAll()), 5)

        # Remove one player from every game.
        tournament.removePlayer(tournament.games[0].id, tournament.games[0].serialsAll()[0], now=True)
        tournament.removePlayer(tournament.games[1].id, tournament.games[1].serialsAll()[0], now=True)
        tournament.removePlayer(tournament.games[2].id, tournament.games[2].serialsAll()[0], now=True)
        
        # Get the players of the first game
        player1 = tournament.games[0].serialsAll()[0]
        player2 = tournament.games[0].serialsAll()[1]
     
        # Ensure that the first game is the one selected for breaking
        self.failUnlessEqual(
            pokertournament.breakGames(tournament.games),
            [(1, 3, [player1]), (1, 2, [player2])]
        )
        
        # Test the balancing.  First, ensure that the players are still at
        # the first game
        self.failUnless(tournament.id2game[1].getPlayer(player1))
        self.failIf(tournament.id2game[2].getPlayer(player1))
        self.failIf(tournament.id2game[3].getPlayer(player1))
        
        self.failUnless(tournament.id2game[1].getPlayer(player2))
        self.failIf(tournament.id2game[2].getPlayer(player2))
        self.failIf(tournament.id2game[3].getPlayer(player2))
        
        self.failUnless(tournament.balanceGames())
        
        self.failUnlessEqual(len(tournament.id2game), 2)
        self.failUnless(tournament.id2game[3].getPlayer(player1))
        self.failUnless(tournament.id2game[2].getPlayer(player2))
        
        self.failIf(tournament.need_balance)

    # -------------------------------------------------------
    def testBalanceGamesRegistering(self):
        """Test Poker Tournament : Balance games when state REGISTERING"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'players_min': 15,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(12):
            self.failUnless(tournament.register(player))
        
        # Note: balanceGames() is called by createGames() so initially,
        # the tables will be balanced as 3 players at first table, 4 at
        # second, and 5 at third.  (This doesn't sound all that balanced,
        # but it's consistent with the algorithm in
        # pokertournament.equalizeGames()

        tournament.createGames()
        self.failUnlessEqual(len(tournament.games[0].serialsAll()), 3)
        self.failUnlessEqual(len(tournament.games[1].serialsAll()), 4)
        self.failUnlessEqual(len(tournament.games[2].serialsAll()), 5)

        # Remove one player from every game.
        tournament.removePlayer(tournament.games[0].id, tournament.games[0].serialsAll()[0], now=True)
        tournament.removePlayer(tournament.games[1].id, tournament.games[1].serialsAll()[0], now=True)
        tournament.removePlayer(tournament.games[2].id, tournament.games[2].serialsAll()[0], now=True)
        
        # Get the players of the first game
        player1 = tournament.games[0].serialsAll()[0]
        player2 = tournament.games[0].serialsAll()[1]
     
        # Ensure that the first game is the one selected for breaking
        self.failUnlessEqual(pokertournament.breakGames(tournament.games),
                             [(1, 3, [player1]), (1, 2, [player2])])
        
        # Test the balancing.  First, ensure that the players are still at
        # the first game
        self.failUnless(tournament.id2game[1].getPlayer(player1))
        self.failIf(tournament.id2game[2].getPlayer(player1))
        self.failIf(tournament.id2game[3].getPlayer(player1))
        
        self.failUnless(tournament.id2game[1].getPlayer(player2))
        self.failIf(tournament.id2game[2].getPlayer(player2))
        self.failIf(tournament.id2game[3].getPlayer(player2))
        
        self.failUnless(tournament.balanceGames())
        
        self.failUnlessEqual(len(tournament.id2game), 2)
        self.failUnless(tournament.id2game[3].getPlayer(player1))
        self.failUnless(tournament.id2game[2].getPlayer(player2))
        
        self.failIf(tournament.need_balance)
        
        
        # Create a new tournament where is no need to break a game
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'players_min': 15,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(12):
            self.failUnless(tournament.register(player))
        

        # As above, note: balanceGames() is called by createGames() so
        # initially, the tables will be balanced as 3 players at first
        # table, 4 at second, and 5 at third.  (This doesn't sound all
        # that balanced, but it's consistent with the algorithm in
        # pokertournament.equalizeGames()

        tournament.createGames()
        self.failUnlessEqual(len(tournament.games[0].serialsAll()), 3)
        self.failUnlessEqual(len(tournament.games[1].serialsAll()), 4)
        self.failUnlessEqual(len(tournament.games[2].serialsAll()), 5)
        
        # ...therefore, no table balancing should be needed ... so
        # equalizeGames() should return nothing, and balance games should
        # be False.

        self.failUnlessEqual(pokertournament.equalizeGames(tournament.games), [])
        self.failIf(tournament.balanceGames())
        
        
    # -------------------------------------------------------
    def testEndTurn(self):
        """Test Poker Tournament : End turn"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 10,
            'seats_per_game': 5,
            'sit_n_go': 'y',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(10):
            self.failUnless(tournament.register(player))
        
        # 2 games (5 players)
        self.failUnlessEqual(len(tournament.games), 2)
        
        # Ten players in the tournament
        self.failUnlessEqual(len(tournament.players), 10)
        
        # Get created games
        game1 = tournament.id2game[1]
        game2 = tournament.id2game[2]
        
        # Game 2, players 1, 2, 3 broke
        players = game2.playersAll()
        for num in range(3):
            players[num].money = 0
            self.failUnless(game2.isBroke(players[num].serial))
        self.failUnlessEqual(game2.brokeCount(), 3)
        
        # End turn of game 2
        tournament.removeBrokePlayers(2, now=True)
        self.failUnless(tournament.tourneyEnd(2))
        
        # Players broke removed
        # Game balanced
        self.failUnlessEqual(len(game1.playersAll()), 3)
        self.failUnlessEqual(len(game2.playersAll()), 4)
        
        # Game 2 players broke
        players = game2.playersAll()
        for num in range(len(players)):
            players[num].money = 0
            self.failUnless(game2.isBroke(players[num].serial))
            
        # End turn of game 2
        tournament.removeBrokePlayers(2, now=True)
        self.failUnless(tournament.tourneyEnd(2))
        
        # Game 2 break
        self.failUnlessEqual(len(tournament.games), 1)
        
        # All the players of game 1 are borke except one
        players = game1.playersAll()
        for num in range(len(players) - 1):
            players[num].money = 0
            self.failUnless(game1.isBroke(players[num].serial))
            
        # End turn of game 1
        tournament.removeBrokePlayers(1, now=True)
        self.failIf(tournament.tourneyEnd(1))
        
        # End of the tounament
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_COMPLETE)
        self.failUnlessEqual(len(tournament.games), 0)
        self.failUnlessEqual(len(tournament.id2game), 0)
        
    # -------------------------------------------------------
    def testEndTurnFirstBreakAndBalance(self):
        """Test Poker Tournament :
        1) a tournament enters BREAK_WAIT
        2) all tables but table T1 finished their hand
        3) the table T1 finishes its hand AND is destroyed as a side
           effect of a call to balanceGames, because the T1 players
           are dispatched to the other tables.
        This is a special case where updateBreak will be called from endTurn
        with a game_id for a table that is gone. updateBreak must gracefully
        ignore the fact it is gone and proceed to BREAK state.
        """
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 10,
            'seats_per_game': 5,
            'sit_n_go': 'y',
            'breaks_first': 0
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(10):
            self.failUnless(tournament.register(player))
        
        # 2 games (5 players)
        self.failUnlessEqual(len(tournament.games), 2)
        
        # Ten players in the tournament
        self.failUnlessEqual(len(tournament.players), 10)
        
        # Get created games
        game1 = tournament.id2game[1]
        game2 = tournament.id2game[2]
        
        # Game 1, players 1 broke
        players = game1.playersAll()
        for num in range(1):
            players[num].money = 0
            self.failUnless(game1.isBroke(players[num].serial))
        self.failUnlessEqual(game1.brokeCount(), 1)

        # End turn of game 1
        tournament.removeBrokePlayers(1, now=True)
        self.failUnless(tournament.tourneyEnd(1))
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_BREAK_WAIT, tournament.state)
        self.failUnlessEqual([1], tournament.breaks_games_id)
        
        # Game 2, players 1, 2, 3, 4 broke as if 5 got all their chips
        players = game2.playersAll()
        for num in range(4):
            players[num].money = 0
            self.failUnless(game2.isBroke(players[num].serial))
        self.failUnlessEqual(game2.brokeCount(), 4)
        
        # End turn of game 2
        tournament.removeBrokePlayers(2, now=True)
        self.failUnless(tournament.tourneyEnd(2))
        
        # Players broke removed
        # Game balanced, game2 discarded, game1 left
        self.failUnlessEqual(len(game1.playersAll()), 5)
        self.failUnlessEqual([game1], tournament.games)
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_BREAK, tournament.state)

        tournament.state = pokertournament.TOURNAMENT_STATE_RUNNING
        
        # Game 1 players broke
        players = game1.playersAll()
        for num in range(len(players) - 1):
            players[num].money = 0
            self.failUnless(game1.isBroke(players[num].serial))
            
        # End turn of game 1
        tournament.removeBrokePlayers(1, now=True)
        self.failIf(tournament.tourneyEnd(1))
        
        # End of the tounament
        self.failUnlessEqual(tournament.state, pokertournament.TOURNAMENT_STATE_COMPLETE)
        self.failUnlessEqual(len(tournament.games), 0)
        self.failUnlessEqual(len(tournament.id2game), 0)
        
    # -------------------------------------------------------
    def testEndTurnFirstBreakAndSinglePlayer(self):
        """Test Poker Tournament :
        On a two tables tournament with two players tables (but this applies to N tables)
        1) table T1 finishes its hand and only has one player left
           tournament is not on BREAK_WAIT
        2) tournament break time is reached
        3) table T2 finishes its hand, no player is busted.
           endTurn is called and tournament enters BREAK_WAIT
           T2 is added to the list of tables for which there
           is not need to wait before declaring the tournament
           on break. Because T1 has only one player left and
           all other tables are expecting the break (i.e. no
           hand will be played), it can be added to the list
           of tables ready for the break.
        """
        arguments = {
            'dirs': self.dirs,
            'players_quota': 4,
            'seats_per_game': 2,
            'sit_n_go': 'y',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        # Register the players
        for player in range(4):
            self.failUnless(tournament.register(player))
        
        # 2 games (4 players)
        self.failUnlessEqual(len(tournament.games), 2)
        
        # 4 players in the tournament
        self.failUnlessEqual(len(tournament.players), 4)
        
        # Get created games
        game1 = tournament.id2game[1]
        game2 = tournament.id2game[2]
        
        # Game 2, players 1 broke as if 2 got all his chips
        players = game2.playersAll()
        players[0].money = 0
        self.failUnless(game2.isBroke(players[0].serial))
        self.failUnlessEqual(game2.brokeCount(), 1)

        # End turn of game 2
        tournament.removeBrokePlayers(2, now=True)
        self.failUnless(tournament.tourneyEnd(2))
        self.failUnlessEqual(len(game2.playersAll()), 1)
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_RUNNING, tournament.state)

        # break time is now
        tournament.breaks_first = 0
        
        # End turn of game 1
        tournament.removeBrokePlayers(1, now=True)
        self.failUnless(tournament.tourneyEnd(1))
        self.failUnlessEqual([game1,game2], tournament.games)
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_BREAK, tournament.state)
        self.failUnlessEqual(len(game1.playersAll()), 2)
        self.failUnlessEqual(len(game2.playersAll()), 1)

    # -------------------------------------------------------
    def testGetRank(self):
        """Test Poker Tournament : Get rank"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'seats_per_game': 5,
            'start_time': time.time() + 20000,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        for player in range(10):
            self.failUnless(tournament.register(player))
            
        tournament.winners = [1, 5, 8]
        
        self.failUnlessEqual(tournament.getRank(1), 8)
        self.failUnlessEqual(tournament.getRank(5), 9)
        self.failUnlessEqual(tournament.getRank(8), 10)
        
        for player in range(10):
            if player not in tournament.winners:
                self.failUnlessEqual(tournament.getRank(player), -1)

    # -------------------------------------------------------
    def testCancel(self):
        """Test Poker Tournament : Cancel"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'players_min': 5,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        for player in range(3):
            self.failUnless(tournament.register(player))
        
        self.failUnlessEqual({0:None, 1:None, 2:None}, tournament.players)
        tournament.start_time = 0
        self.assertEqual(None, tournament.canRun())
        tournament.updateRunning()
        self.failUnlessEqual({}, tournament.players)
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_CANCELED, tournament.state)
        self.failIf(tournament.cancel())

    # -------------------------------------------------------
    def testRunRegular(self):
        """Test Poker Tournament : Cancel"""
        
        arguments = {
            'dirs': self.dirs,
            'players_quota': 20,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        self.failUnless(tournament.register(1))
        tournament.start_time = 0
        self.failUnless(tournament.register(2))
        
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_RUNNING, tournament.state)
        
    def testHistoryReduceWorksAfterPlayerRemove(self):

        arguments = {
            'dirs': self.dirs,
            'players_quota': 5,
            'start_time': time.time() + 20000,
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        
        self.failUnless(tournament.register(1))
        tournament.start_time = 0
        self.failUnless(tournament.register(2))
        
        self.failUnlessEqual(pokertournament.TOURNAMENT_STATE_RUNNING, tournament.state)
        game = tournament.games[0]
        
        game.beginTurn(1)
        self.assertTrue(game.isFirstRound())
        
        # finish the tourney
        game.callNraise(1,game.serial2player[1].money)
        game.call(2)
        
        # remove a player from the tourney and call historyReduce
        tournament.removePlayer(game.id,1, now=True)
        self.assertTrue(game.historyCanBeReduced())
        game.historyReduce()
        

class Breaks(unittest.TestCase):

    def setUp(self):
        self.now = time.time() + 20000
        pokertournament.tournament_seconds = self.seconds
        
    def seconds(self):
        return self.now
    
    def test_remainingBreakSeconds(self):
        arguments = { 
            'dirs': [path.join(TESTS_PATH, '../conf')],
            'players_quota':  20,
            'start_time': self.seconds(),
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        self.assertEqual(None, tournament.remainingBreakSeconds())
        tournament.breaks_since = self.now - 1
        tournament.breaks_duration = 2
        self.assertEqual(1, tournament.remainingBreakSeconds())

    def test_updateBreak(self):
        
        arguments = { 
            'dirs': [path.join(TESTS_PATH, '../conf')],
            'players_quota': 20,
            'start_time': self.seconds(),
            'seats_per_game': 5,
            'sit_n_go': 'n',
        }
                            
        tournament = pokertournament.PokerTournament(**arguments)
        tournament.state = pokertournament.TOURNAMENT_STATE_RUNNING
        #
        # No break, updateBreak does nothing
        #
        tournament.breaks_duration = 0
        self.assertEqual(False, tournament.updateBreak(0))
        #
        # RUNNING but not time to break yet
        #
        tournament.breaks_duration = 5
        tournament.breaks_running_since = tournament.start_time
        tournament.breaks_first = 10
        tournament.breaks_interval = 10
        tournament.breaks_duration = 1
        tournament.breaks_count = 1
        self.failUnless(tournament.updateBreak())
        tournament.breaks_count = 0
        self.failUnless(tournament.updateBreak())
        #
        # RUNNING -> BREAK_WAIT 
        #
        self.now = tournament.breaks_running_since + tournament.breaks_first
        class Game:
            def __init__(self, id):
                self.id = id
            def playersAll(self):
                return [1,2,3]
                
        tournament.games = [Game(1), Game(2)]
        self.failUnless(tournament.updateBreak(1))
        self.failUnless(hasattr(tournament, 'breaks_games_id'))
        self.assertEqual([1],tournament.breaks_games_id)
        self.assertEqual(pokertournament.TOURNAMENT_STATE_BREAK_WAIT, tournament.state)
        #
        # BREAK_WAIT -> BREAK
        #
        self.failUnless(tournament.updateBreak(2))
        self.failIf(hasattr(tournament, 'breaks_games_id'))
        self.assertEqual(pokertournament.TOURNAMENT_STATE_BREAK, tournament.state)
        self.assertEqual(self.now, tournament.breaks_since)
        #
        # BREAK -> RUNNING
        #
        self.now += tournament.breaks_duration
        self.failUnless(tournament.updateBreak())
        self.assertEqual(self.now, tournament.breaks_running_since)
        #
        # Call with invalid state
        #
        tournament.state = pokertournament.TOURNAMENT_STATE_CANCELED
        self.assertEqual(None, tournament.updateBreak())

class PokerTournamentStatsTestCase(unittest.TestCase):
    class MockObj(object):
        _messages = []
        def __init__(self,**kw):
            for k,v in kw.items():
                setattr(self, k, v)
            self.log = log.get_child('MockObj')
        def error(self,msg):
            self._messages.append(msg)
    class MockTourney(MockObj):
        pass
    class MockGame(MockObj):
        pass
    class MockPlayer(MockObj):
        pass
    
    def setUp(self):
        self.players = {
            21: PokerTournamentStatsTestCase.MockPlayer(serial=21,name='Player21',money=4000),
            12: PokerTournamentStatsTestCase.MockPlayer(serial=12,name='Player12',money=3000),
            11: PokerTournamentStatsTestCase.MockPlayer(serial=11,name='Player11',money=2000),
            22: PokerTournamentStatsTestCase.MockPlayer(serial=22,name='Player22',money=1000)
        }
        self.game1 = PokerTournamentStatsTestCase.MockGame(
            serial2player = {11:self.players[11],12:self.players[12]}
        )
        self.game2 = PokerTournamentStatsTestCase.MockGame(
            serial2player = {21:self.players[21],22:self.players[22]}
        )
        self.tourney = PokerTournamentStatsTestCase.MockTourney(
            serial = 1,
            winners = [],
            games = [self.game1,self.game2]
        )
        self.stats = pokertournament.PokerTournamentStats(self.tourney)
    
    def testStats(self):
        self.stats.update(None)
        
        # no inactive players (i.e. all are still playing)
        stats = self.stats(0)
        self.assertEqual(21, stats['player_chips_max_serial'])
        self.assertEqual('Player21', stats['player_chips_max_name'])
        self.assertEqual(self.players[21].money, stats['chips_max'])
        
        # stats was called with invalid serial -> rank is 0
        self.assertEqual(0, stats['rank'])
        
        # stats called with chipsleader should return 1
        stats = self.stats(21)
        self.assertEqual(1, stats['rank'])
        
        # 21 lost (i.e. was added to the winners list) -> should be on last place (i.e. 4th)
        self.tourney.winners = [21]
        self.stats.update(0)
        stats = self.stats(21)
        self.assertEqual(12, stats['player_chips_max_serial'])
        self.assertEqual(4, stats['rank'], '21 should be last (4th).')
        
        # update can not be called if there are no active players
        # (the reasoning behind this is that in this way, it is called as a last moment when there is only
        # one player left -> his chips are shown, he is inserted as a chipsleader, and everything else is
        # ok too).
        self.tourney.winners = self.players.keys()
        self.assertEqual(False, self.stats.update(0))
        #self.assertTrue("need players in games" in self.tourney._messages[0])
    

# ---------------------------------------------------------
def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PokerTournamentTestCase))
#    suite.addTest(unittest.makeSuite(PokerTournamentTestCase, prefix = "testEndTurnFirstBreakAndSinglePlayer"))
    suite.addTest(unittest.makeSuite(Breaks))
    suite.addTest(unittest.makeSuite(PokerTournamentStatsTestCase))
    # Comment out above and use line below this when you wish to run just
    # one test by itself (changing prefix as needed).
#    suite.addTest(unittest.makeSuite(Breaks, prefix = "testPrizes"))
    return suite
    
# ---------------------------------------------------------
def run():
    try:
        import xmlrunner
        runner = xmlrunner.XMLTestRunner(output='build/tests')
    except ImportError:
        runner = unittest.TextTestRunner()
    return runner.run(GetTestSuite())
    
# ---------------------------------------------------------
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/test-pokertournament.py ) ; ( cd ../tests ; make COVERAGE_FILES='../pokerengine/pokertournament.py' TESTS='coverage-reset test-pokertournament.py coverage-report' check )"
# End:
