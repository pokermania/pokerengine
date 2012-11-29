#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep
#
# Mekensleep
# 26 rue des rosiers
# 75004 Paris
#       licensing@mekensleep.com
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
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))
sys.path.insert(1, path.join(TESTS_PATH, "../../common"))

from log_history import log_history

import time

import reflogging
log = reflogging.root_logger.get_child('test-tournament')

from pokerengine.pokergame import PokerGameServer
from pokerengine.pokertournament import equalizeGames, breakGames, PokerTournament

NGAMES = 5

class PokerPredefinedDecks:
    def __init__(self, decks):
        self.decks = decks
        self.index = 0
        
    def shuffle(self, deck):
        deck[:] = self.decks[self.index][:]
        self.index += 1
        if self.index >= len(self.decks):
            self.index = 0
        
class TestTournament(unittest.TestCase):

    def setUp(self):
        predefined_decks = [
            "8d 2h 2c 8c 4c Kc Ad 9d Ts Jd 5h Tc 4d 9h 8h 7h 9c 2s 3c Kd 5s Td 5d Th 3s Kh Js Qh 7d 2d 3d 9s Qd Ac Jh Jc Qc 6c 7s Ks 5c 4h 7c 4s Qs 6s 6h Ah 6d As 3h 8s", # distributed from the end
            ]
        self.games = []
        for i in xrange(NGAMES):
            game = PokerGameServer("poker.%s.xml", [path.join(TESTS_PATH, '../conf')])
            game.setVariant("7stud")
            game.setBettingStructure("0-0_50-5000_limit")
            game.id = i
            game.shuffler = PokerPredefinedDecks(map(lambda deck: game.eval.string2card(deck.split(' ')), predefined_decks))
            self.games.append(game)

    def tearDown(self):
        del self.games

    def log(self, string):
        print string

class TestEqualize(TestTournament):
    
    def test1(self):
        """
        """
        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 8 players
        # table 1 : 8 players
        # table 2 : 7 players
        # table 3 : 7 players
        # table 4 : 2 players
        #
        counts = [8, 8, 7, 7, 2]
        for game in self.games:
            game.serial2player = {}
            for serial in xrange(counts.pop(0)):
                game.serial2player[game.id * 100 + serial] = None

        #
        # 2 players move
        #
        # table 0 : 8 players -> 1 leave to table 4
        # table 1 : 8 players -> 1 leave to table 4
        # table 2 : 7 players
        # table 3 : 7 players
        # table 4 : 2 players <- 2 arrive from table 0 and 1
        #
        self.assertEqual(equalizeGames(self.games[:]), [(0, 4, 0), (1, 4, 100)])
        
        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 10 players
        # table 1 : 8 players
        # table 2 : 3 players
        # table 3 : 9 players
        # table 4 : 5 players
        #
        counts = [10, 8, 3, 9, 5]
        for game in self.games:
            game.serial2player = {}
            for serial in xrange(counts.pop(0)):
                game.serial2player[game.id * 100 + serial] = None

        #
        # 6 players move
        #
        # table 0 : 10 players -> 3 leave (2 to table 2, 1 to table 4)
        # table 1 : 8 players  -> 1 leave (to table 2)
        # table 2 : 3 players  <- 4 arrive (2 from table 0, 1 from table 2, 1 from table 3)
        # table 3 : 9 players  -> 2 leave (1 to table 2, 1 to table 4)
        # table 4 : 5 players  <- 2 arrive (1 from table 0, 1 from table 3)
        #
        self.assertEqual(equalizeGames(self.games[:]), [
            (0, 4, 0),
            (0, 2, 1),
            (0, 4, 2),
            (1, 2, 100),
            (3, 4, 300),
            (3, 2, 301)])
            
        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 10 players
        # table 1 : 10 players
        # table 2 : 10 players
        # table 3 : 10 players
        # table 4 : 10 players
        #
        counts = [10, 10, 10, 10, 10]
        for game in self.games:
            game.serial2player = {}
            for serial in xrange(counts.pop(0)):
                game.serial2player[game.id * 100 + serial] = None
        #
        # Nothing to be done
        #
        self.assertEqual(equalizeGames(self.games[:]), [])

    def test2(self):
        #
        # Two 5 seats tables (0, 1) 
        # table 0 : 2 players
        # table 1 : 5 players
        #
        games = self.games[:2]
        games[0].serial2player = {}
        games[0].max_players = 5
        for serial in (1, 2):
            games[0].serial2player[serial] = None

        games[1].serial2player = {}
        games[1].max_players = 5
        for serial in (100, 101, 102, 103, 104):
            games[1].serial2player[serial] = None

        self.assertEqual(equalizeGames(games), [(1, 0, 100), (1, 0, 101)])

    def test3(self):
        #
        # Three 5 seats tables (0, 1, 2) 
        # table 0 : 2 players 
        # table 1 : 5 players (running)
        # table 2 : 5 players (running)
        #
        games = self.games[:3]
        games[0].serial2player = {}
        games[0].max_players = 5
        for serial in (1, 2):
            games[0].serial2player[serial] = None

        games[1].serial2player = {}
        games[1].max_players = 5
        games[1].state = "turn"
        for serial in (100, 101, 102, 103, 104):
            games[1].serial2player[serial] = None

        games[2].serial2player = {}
        games[2].max_players = 5
        games[2].state = "turn"
        for serial in (200, 201, 202, 203, 204):
            games[2].serial2player[serial] = None

        #
        # Games that could provide players are running and can't
        # provide players. Nothing can be done.
        #
        self.assertEqual(equalizeGames(games), [])

        #
        # Three 5 seats tables (0, 1, 2) 
        # table 0 : 2 players (running)
        # table 1 : 5 players (running)
        # table 2 : 5 players 
        #
        games[0].state = "turn"
        games[2].state = "end"
        #
        # Game 2 provide 2 players to game 0 
        #
        self.assertEqual(equalizeGames(games), [(2, 0, 200), (2, 0, 201)])

class TestBreak(TestTournament):
    
    def test1(self):
        """
        """
        #
        # Five 10 seats tables (0 to 4), each with 5 players
        #
        counts = [5] * NGAMES
        for game in self.games:
            for serial in xrange(counts.pop()):
                game.serial2player[game.id * 100 + serial] = None

        #
        # Players from table 0 go to table 4
        # Players from table 1 to to table 3
        #
        self.assertEqual(breakGames(self.games), [
            (0, 4, [0, 1, 2, 3, 4]),
            (1, 3, [104, 100, 101, 102, 103])
            ])

        #
        # Five 10 seats tables (0 to 4), table 0 with 10 players,
        # tables 1 to 4 with 5 players
        #
        for serial in xrange(5,10):
            self.games[0].serial2player[serial] = None

        #
        # Players from table 1 go to table 4
        # Players from table 2 go to table 3
        #
        self.assertEqual(breakGames(self.games), [
            (1, 4, [104, 100, 101, 102, 103]),
            (2, 3, [200, 201, 202, 203, 204])
            ])

        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 10 players
        # table 1 : 7 players
        # table 2 : 7 players
        # table 3 : 7 players
        # table 4 : 7 players
        #
        for game in self.games:
            for serial in xrange(5,7):
                game.serial2player[game.id * 100 + serial] = None

        #
        # Players from table 1 are spread on tables
        # 4, 3, 2
        #
        self.assertEqual(breakGames(self.games), [
            (1, 4, [100, 101, 102]),
            (1, 3, [103, 104, 105]),
            (1, 2, [106])
            ])

        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 10 players
        # table 1 : 7 players
        # table 2 : 7 players
        # table 3 : 9 players
        # table 4 : 7 players
        #
        for serial in xrange(7,9):
            self.games[3].serial2player[300 + serial] = None

        #
        # Players from table 1 are spread on tables
        # 3, 4, 2. Table 3 is chosen first because it is the
        # table with the largest number of players.
        #
        self.assertEqual(breakGames(self.games), [
            (1, 3, [100]),
            (1, 4, [101, 102, 103]),
            (1, 2, [104, 105, 106])
            ])

        #
        # Five 10 seats tables (0 to 4)
        # table 0 : 10 players
        # table 1 : 8 players
        # table 2 : 7 players
        # table 3 : 9 players
        # table 4 : 7 players
        #
        for serial in xrange(7,8):
            self.games[1].serial2player[100 + serial] = None

        #
        # Can't break any table : 6 free seats and smallest table
        # has seven players.
        #
        self.assertEqual(breakGames(self.games), [])

    def test2(self):
        #
        # Two 5 seats tables (0, 1) 
        # table 0 : 2 players
        # table 1 : 3 players
        #
        games = self.games[:2]
        games[0].serial2player = {}
        games[0].max_players = 5
        for serial in (1, 2):
            games[0].serial2player[serial] = None

        games[1].serial2player = {}
        games[1].max_players = 5
        for serial in (100, 101, 102):
            games[1].serial2player[serial] = None

        self.assertEqual(breakGames(games), [(0, 1, [1, 2])])

    def test3(self):
        """
        """
        #
        # Five 10 seats tables (0 to 4), each with 5 players
        #
        counts = [5] * NGAMES
        for game in self.games:
            for serial in xrange(counts.pop()):
                game.serial2player[game.id * 100 + serial] = None
                game.state = "turn"

        #
        # Tables 0, 1, 2, 3 are running and will not be broken.
        # Only table 4 is not running and can be broken.
        #
        self.games[4].state = "end"
        #
        # Players from table 4 go to table 3
        #
        self.assertEqual(breakGames(self.games), [(4, 3, [400, 401, 402, 403, 404])])
        
class TestRebuy(unittest.TestCase):

    def setUp(self):
        self.tourney = PokerTournament(name = 'Test create',
            players_quota = 4,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = 4,
            rebuy_delay = 600,
            buy_in=5,
            prizes_specs="algorithm")
        for serial in xrange(1,5):
            self.assertTrue(self.tourney.register(serial))

        self.game = self.tourney.games[0]
        self.players = self.game.playersAll()

    def tearDown(self):
        del self.tourney

    def test1_insertedWinnersAreCorrect(self):
        winners = [1,2,3,4]

        self.tourney.winners = winners
        self.assertEqual(self.tourney.winners, winners)

        self.tourney.winners = []
        self.assertEqual(self.tourney.winners, [])
    
    def test2(self):
        tourney = self.tourney
        game = self.game
        players = self.players
        player3 = [p for p in players if p.serial == 3][0]
        original_startmoney = player3.money

        def myremove_player(tournament, game_id, serial, now=False):
            if now:
                tournament.removePlayer(game_id, serial, now)

        tourney.callback_remove_player = myremove_player
        def my_rebuy(tournament, serial, table_id, player_chips, tourney_chips):
            self.assertEqual(table_id, game.id)
            self.assertEqual(tourney.buy_in, player_chips)
            if serial == 1:
                return 0
            return tourney_chips

        tourney.callback_rebuy = my_rebuy


        def looseMoney(serial):
            for player in players:
                if player.serial != serial:
                    continue
                player.money = 0
                self.assertTrue(game.isBroke(serial))

        # Player got broke
        looseMoney(1)
        self.assertEqual(tourney.winners, [])

        # Even removeBrokePlayers and endTurn doesn't remove him, 
        # because he has a chance for rebuy
        tourney.removeBrokePlayers(1)
        self.assertEqual(tourney.winners, [])

        # Player 2 gets broke, and chooses not to rebuy
        looseMoney(2)
        tourney.removeBrokePlayers(1)
        tourney.tourneyEnd(1)
        tourney.removePlayer(1, 2)
        self.assertEqual(tourney.winners, [2])
        self.assertEqual(tourney.getRank(2), 4)

        # Player 1 tries to rebuy but has not enough money
        err, reason = tourney.rebuy(1)
        self.assertFalse(err)
        # the error reason from our callback should be the same we get here
        self.assertEquals(reason, "money")

        # After Player 1 Timed out, he will be also removed
        # Note: this changes the rank for player 2
        tourney.removePlayer(1, 1)

        self.assertEqual(tourney.winners, [2, 1])
        self.assertEqual(tourney.getRank(2), 3)
        self.assertEqual(tourney.getRank(1), 4)

        # Player 3 get broke but rebuys a few times
        for _i in range(4):
            looseMoney(3)
            self.assertEqual(player3.money, 0)

            tourney.removeBrokePlayers(1)
            tourney.tourneyEnd(1)
            self.assertEqual(tourney.winners, [2, 1])

            err, reason = tourney.rebuy(3)
            self.assertTrue(err, reason)

            tourney.removeBrokePlayers(1)
            tourney.tourneyEnd(1)
            self.assertEqual(tourney.winners, [2, 1])

        # after the rebuy player 3 has the same money as he started 
        self.assertEqual(original_startmoney, player3.money)
        looseMoney(4)

        tourney.removeBrokePlayers(1)
        tourney.tourneyEnd(1)
        self.assertEqual(tourney.winners, [2, 1])

        err, reason = tourney.rebuy(4)
        self.assertTrue(err, reason)

        tourney.removeBrokePlayers(1)
        tourney.tourneyEnd(1)
        self.assertEqual(tourney.winners, [2, 1])

        looseMoney(4)
        tourney.removeBrokePlayers(1)
        tourney.tourneyEnd(1)
        tourney.removePlayer(1, 4)

        self.assertFalse(tourney.tourneyEnd(1))

        self.assertEqual(tourney.winners, [3,4,2,1])
        # We have just one winner and he wins the complete pot (4 * buy_in) + ( 5 * succesfull_rebuys)
        self.assertEqual(tourney.prizes(), [45])

    def testGetNextPositionWillReturnCorrectValue(self):
        def sortTmpWinner():
            return [k for k,_v in sorted(self.tourney._winners_dict_tmp.iteritems() ,key=lambda (a,b):(b,a),reverse=True)]
            return self.tourney._winners_dict_tmp.keys()

        def removePlayer(serials):
            nid = self.tourney._incrementToNextWinnerPosition()
            for serial in serials:
                self.tourney._winners_dict_tmp[serial] = nid

        def reenterPlayer(serials):
            for serial in serials:
                del self.tourney._winners_dict_tmp[serial]

        self.assertEqual(sortTmpWinner(), [])
        removePlayer([3,4])
        self.assertEqual(sortTmpWinner(), [4,3])
        removePlayer([2])
        self.assertEqual(sortTmpWinner(), [2,4,3])
        reenterPlayer([3,4])
        self.assertEqual(sortTmpWinner(), [2])
        removePlayer([1])
        self.assertEqual(sortTmpWinner(), [1,2])
    
    def testUnequalTables(self):
            
        tourney = PokerTournament(
            name = 'Test create',
            players_quota = 4,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = 2
        )
        
        def tourneySoftRemovePlayer(self, game_id, serial, now):
            game = self.id2game[game_id]
            game.removePlayer(serial)
            self.finallyRemovePlayer(serial, now)
        
        def gameCallbackTourneyEndTurn(game_id, game_type, *args):
            if game_type == 'end':
                tourney.endTurn(game_id)
                tourney.tourneyEnd(game_id)
                
        for serial in xrange(1,5): self.assertTrue(tourney.register(serial))
        
        for g in tourney.games: g.registerCallback(gameCallbackTourneyEndTurn)
        
        players = {}
        for g in tourney.games:
            for (serial,player) in g.serial2player.iteritems(): players[serial] = player
        
        for g in tourney.games:
            g.beginTurn(1)
        
        broke_info = {}
        # in all games, one of the two players is getting broke.
        for g in tourney.games:
            serial = g.getSerialInPosition()
            broke_player = players[serial]
            broke_info[serial] = g.id
            broke_player.money = 0
            g.fold(serial)
        
        self.assertEquals(len(tourney.games),1,'there should be only one game left (games: %s)' % tourney.id2game.keys())
        
        

class TestCreate(unittest.TestCase):

    def setUp(self):
        pass
        
    def test1(self):
        tourney = PokerTournament(
            name = 'Test create',
            players_quota = 4,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = 4,
            betting_structure = "level-10-20-no-limit"
        )

        for serial in xrange(1,5):
            self.failUnless(tourney.register(serial))

        self.assertEqual(len(tourney.games), 1)
        for game in tourney.games:
            for serial in game.serialsAll():
                game.botPlayer(serial)
        turn = 1
        running = True
        while running:
            turn += 1
            if turn >= 200: raise Exception('Suspecting infity loop (more than 200 turns were played).')
            for game in tourney.games:
                game.beginTurn(turn)
                tourney.removeBrokePlayers(game.id, now=True)
                if game.id in tourney.id2game and not tourney.tourneyEnd(game.id):
                    running = False 
                    break

    def test2(self):
        #
        # One table sit-n-go
        #
        tourney = PokerTournament(
            name = 'Test create',
            players_quota = 4,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = 4
        )

        for serial in xrange(1,4):
            self.failUnless(tourney.register(serial))
            self.failUnless(tourney.unregister(serial))
            self.failUnless(tourney.register(serial))
        self.failUnless(tourney.register(4))
        self.failIf(tourney.unregister(4))

        self.assertEqual(len(tourney.games), 1)
        game = tourney.games[0]
        game.beginTurn(1)

    def test3(self):
        #
        # Multi tables sit-n-go
        #
        seats_per_game = 10
        games_count = 2
        players_count = seats_per_game * games_count
        tourney = PokerTournament(
            name = 'Test create',
            players_quota = players_count,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = seats_per_game
        )

        for serial in xrange(1,players_count + 1):
            self.failUnless(tourney.register(serial))

        self.assertEqual(len(tourney.games), games_count)
        for game in tourney.games:
            for serial in game.serialsAll():
                game.botPlayer(serial)
        turn = 1
        running = True
        while running:
            turn += 1
            if turn >= 200: raise Exception('Suspecting infity loop (more than 200 turns were played).')
            for game in tourney.games:
                if game.sitCount() > 1:
                    game.beginTurn(turn)
                    tourney.removeBrokePlayers(game.id, now=True)
                    if game.id in tourney.id2game and not tourney.tourneyEnd(game.id):
                        running = False 
                        break

    def tourneyTableStartBalancedHelper(self, num_players, seats, num_tables, min_per_table):
        """tourneyTableStartBalancedHelper
        Helper function to test various scenarios of initial seating"""

        tourney = PokerTournament(
            name = 'Only%d' % num_players,
            players_quota = num_players,
            players_min = num_players,
            dirs = [path.join(TESTS_PATH, '../conf')],
            seats_per_game = seats,
            betting_structure = "level-10-20-no-limit"
        )

        for serial in xrange(1,num_players+1):
            self.failUnless(tourney.register(serial))

        self.assertEquals(len(tourney.games), num_tables)
        for game in tourney.games:
            self.failUnless(len(game.serial2player.values()) >= min_per_table)

    def test4_tourneyTableStartBalanced(self):
        """test4_tourneyTableStartBalanced

        Start with a table max of 5 players per table, and add 6 players
        to it.  This should create two tables of 3.  Tests other scenarios
        like this as well."""

        self.tourneyTableStartBalancedHelper(6, 5, 2, 2)
        self.tourneyTableStartBalancedHelper(13, 6, 3, 4)
        
        
class TestPrizes(unittest.TestCase):

    def assertTourneyPrizes(self, prizes_specs, quota, register_i, assert_prizes):
        tourney = PokerTournament(
            dirs = [path.join(TESTS_PATH, '../conf')],
            prizes_specs=prizes_specs,
            start_time = time.time() + 2000,
            sit_n_go = 'n',
            buy_in = 5,
            players_quota = quota
        )

        for ii in xrange(1, register_i+1):
            tourney.register(ii)

        self.assertEqual(tourney.prizes(), assert_prizes)


    def test_Algorithm10(self): self.assertTourneyPrizes('algorithm', 100, 10, [32, 12, 6])
    def test_Algorithm20(self): self.assertTourneyPrizes('algorithm', 100, 20, [57, 25, 12, 6])
    def test_Algorithm50(self): self.assertTourneyPrizes('algorithm', 1000, 50, [129, 62, 31, 7, 7, 7, 7])
    def test_Algorithm200(self): self.assertTourneyPrizes('algorithm', 1000, 200, [506, 250, 125, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7])
    def test_Table3(self): self.assertTourneyPrizes('table', 1000, 3, [15])
    def test_Table6(self): self.assertTourneyPrizes('table', 1000, 6, [21, 9])
    def test_Table30(self): self.assertTourneyPrizes('table', 1000, 30, [75, 45, 30])
    def test_Table50(self): self.assertTourneyPrizes('table', 1000, 50, [94, 55, 37, 27, 20, 17])
    def test_Table200(self): self.assertTourneyPrizes('table', 1000, 200, [278, 166, 101, 79, 68, 57, 47, 37, 26, 20, 15, 15, 15, 12, 12, 12, 10, 10, 10, 10])
    def test_Table300(self): self.assertTourneyPrizes('table', 1000, 300, [404, 231, 131, 105, 90, 75, 60, 45, 30, 22, 18, 18, 18, 15, 15, 15, 12, 12, 12, 12, 9, 9, 9, 9,
        9, 9, 9, 9, 9, 9, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7
    ])
    def test_Table500(self): self.assertTourneyPrizes('table', 1000, 500, [644, 350, 206, 158, 132, 106, 81, 56, 42, 32, 27, 27, 27, 22, 22, 22, 19, 19, 19, 19, 15, 15,
        15, 15, 15, 15, 15, 15, 15, 15, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10
    ])
    def test_Table700(self): self.assertTourneyPrizes('table', 1000, 700, [860, 455, 262, 210, 175, 140, 105, 70, 52, 38, 29, 29, 29, 26, 26, 26, 22, 22, 22, 22, 19, 19,
        19, 19, 19, 19, 19, 19, 19, 19, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 8, 8, 8, 8,
        8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7
    ])
    def test_Table1000(self): self.assertTourneyPrizes('table', 5000, 1000, [1210, 650, 375, 300, 250, 200, 150, 100, 75, 55, 42, 42, 42, 37, 37, 37, 32, 32, 32, 32, 27,
        27, 27, 27, 27, 27, 27, 27, 27, 27, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 12, 12,
        12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10
    ])
    def test_Table5000(self): self.assertTourneyPrizes('table', 5000, 5000, [5056, 2750, 1725, 1362, 1150, 862, 662, 437, 337, 237, 200, 200, 200, 174, 174, 174, 150, 150,
        150, 150, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65, 65,
        65, 65, 65, 65, 65, 65, 65, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40,
        40, 40, 40, 40, 40, 40, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37,
        37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32
    ])


def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEqualize))
    suite.addTest(unittest.makeSuite(TestBreak))
    suite.addTest(unittest.makeSuite(TestRebuy))
    suite.addTest(unittest.makeSuite(TestCreate))
    suite.addTest(unittest.makeSuite(TestPrizes))
    return suite

def run():
    return unittest.TextTestRunner().run(GetTestSuite())
    
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
