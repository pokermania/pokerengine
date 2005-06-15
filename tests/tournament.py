#
# Copyright (C) 2004, 2005 Mekensleep
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#  Loic Dachary <loic@gnu.org>
#

import sys, os
sys.path.insert(0, "..")

import unittest
from pokerengine.pokergame import PokerGameServer
from pokerengine.pokertournament import equalizeGames, breakGames, PokerTournament

NGAMES = 5

class TestTournament(unittest.TestCase):

    def setUp(self):
        self.games = []
        for i in xrange(NGAMES):
            game = PokerGameServer("poker.%s.xml", [ "../conf" ])
            game.verbose = 3
            game.setVariant("7stud")
            game.setBettingStructure("0-0-limit")
            game.id = i
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

        self.assertEqual(equalizeGames(games), [(1, 0, 104), (1, 0, 100)])

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
        self.assertEqual(breakGames(self.games[:]), [
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
        self.assertEqual(breakGames(self.games[:]), [
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
        self.assertEqual(breakGames(self.games[:]), [
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
        self.assertEqual(breakGames(self.games[:]), [
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
        self.assertEqual(breakGames(self.games[:]), [])

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
        self.assertEqual(breakGames(self.games[:]), [(4, 3, [400, 401, 402, 403, 404])])
        
class TestCreate(unittest.TestCase):

    def test1(self):
        #
        # One table sit-n-go
        #
        tourney = PokerTournament(name = 'Test create',
                                       verbose = 3,
                                       players_quota = 4,
                                       dirs = [ '../conf' ],
                                       seats_per_game = 4)

        for serial in xrange(1,4):
            self.failUnless(tourney.register(serial))
            self.failUnless(tourney.unregister(serial))
            self.failUnless(tourney.register(serial))
        self.failUnless(tourney.register(4))
        self.failIf(tourney.unregister(4))

        self.assertEqual(len(tourney.games), 1)
        game = tourney.games[0]
        game.beginTurn(1)

    def test2(self):
        #
        # Multi tables sit-n-go
        #
        seats_per_game = 10
        games_count = 2
        players_count = seats_per_game * games_count
        tourney = PokerTournament(name = 'Test create',
                                  verbose = 3,
                                  players_quota = players_count,
                                  dirs = [ '../conf' ],
                                  seats_per_game = seats_per_game)

        for serial in xrange(1,players_count + 1):
            self.failUnless(tourney.register(serial))

        self.assertEqual(len(tourney.games), games_count)
        for game in tourney.games:
            for serial in game.serialsAll():
                game.botPlayer(serial)
        turn = 1
        running = True
        while running:
            for game in tourney.games:
                if game.sitCount() > 1:
                    game.beginTurn(turn)
                    running = tourney.endTurn(game.id)
                    if not running: break
        for serial in tourney.winners:
            print "%d\thas rank %d" % ( serial, tourney.getRank(serial) )


class TestPrizes(unittest.TestCase):

    def test1(self):
        tourney = PokerTournament()
        tourney.can_register = False

        tourney.players = [1] * 10
        self.assertEqual(tourney.prizes(5), [32, 12, 6])

        tourney.players = [1] * 20
        self.assertEqual(tourney.prizes(5), [57, 25, 12, 6])

        tourney.players = [1] * 50
        self.assertEqual(tourney.prizes(5), [129, 62, 31, 7, 7, 7, 7])
                        
        tourney.players = [1] * 200
        self.assertEqual(tourney.prizes(5), [506, 250, 125, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7])
                        
def run():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEqualize))
    suite.addTest(unittest.makeSuite(TestBreak))
    suite.addTest(unittest.makeSuite(TestCreate))
    suite.addTest(unittest.makeSuite(TestPrizes))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()
