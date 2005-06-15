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

from pprint import pprint
import unittest
from pokerengine.pokergame import PokerGameServer

class TestBlinds(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [ "../conf" ])
        self.game.verbose = 3
        self.game.setVariant("holdem")
        self.game.setBettingStructure("2-4-limit")

    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_new_player(self, serial, seat):
        game = self.game
        self.failUnless(game.addPlayer(serial, seat))
        self.failUnless(game.payBuyIn(serial, game.buyIn()))
        self.failUnless(game.sit(serial))
        game.botPlayer(serial)
        game.noAutoBlindAnte(serial)

    def pay_blinds(self):
        game = self.game
        for serial in game.serialsAll():
            game.autoBlindAnte(serial)
        for serial in game.serialsAll():
            game.noAutoBlindAnte(serial)

    def check_blinds(self, descriptions):
        players = self.game.playersAll()
        players.sort(lambda a,b: int(a.seat - b.seat))
        for player in players:
            (blind, missed, wait) = descriptions.pop(0)
            self.failUnless(blind == player.blind)
            self.failUnless(missed == player.missed_blind)
            self.failUnless(wait == player.wait_for)
            
    def test1(self):
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.beginTurn(2)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           (None, None, False), # 2
                           ('small', None, False), # 3
                           ('big', None, False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.beginTurn(3)
        # (blind, missed, wait)
        self.check_blinds([('big', None, False), # 1
                           (None, None, False), # 2
                           (None, None, False), # 3
                           ('small', None, False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.beginTurn(4)
        # (blind, missed, wait)
        self.check_blinds([('small', None, False), # 1
                           ('big', None, False), # 2
                           (None, None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()
        
    def test2(self):
        """
        Two new players enter the game and both pay the big blind
        """
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 8)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

        for (serial, seat) in ((10, 4), (11, 5)):
            self.make_new_player(serial, seat)

        self.game.beginTurn(2)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           (None, None, False), # 2
                           ('small', None, False), # 3
                           ('big', 'n/a', False), # 10
                           ('late', 'n/a', False), # 11
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

    def test3(self):
        """
        Two new players enter the game between the small
        and big blind. They are allowed to play during the
        second turn because they cannot be awarded the button
        as they arrive.
        """
        for (serial, seat) in ((1, 0), (2, 1), (3, 7), (4, 8)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

        for (serial, seat) in ((10, 4), (11, 5)):
            self.make_new_player(serial, seat)

        self.game.beginTurn(2)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           (None, None, False), # 2
                           (None, 'n/a', 'late'), # 10
                           (None, 'n/a', 'late'), # 11
                           ('small', None, False), # 3
                           ('big', None, False), # 4
                           ]
                          )
        self.pay_blinds()
        # players who did not pay the big blind are removed from
        # the history by historyReduce
        game_index = 0
        player_list_index = 7
        serial2chips_index = 9
        history = self.game.turn_history
        self.assertEqual(history[game_index][player_list_index], [1, 2, 10, 11, 3, 4])
        self.assertEqual(history[game_index][serial2chips_index].keys(), [1, 2, 3, 4, 10, 11, 'values'])
        self.game.historyReduce()
        self.assertEqual(history[game_index][player_list_index], [1, 2, 3, 4])
        self.assertEqual(history[game_index][serial2chips_index].keys(), [1, 2, 3, 4, 'values'])

        self.game.beginTurn(3)
        # (blind, missed, wait)
        self.check_blinds([('big', None, False), # 1
                           (None, None, False), # 2
                           ('late', 'n/a', False), # 10
                           ('late', 'n/a', False), # 11
                           (None, None, False), # 3
                           ('small', None, False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.beginTurn(4)
        # (blind, missed, wait)
        self.check_blinds([('small', None, False), # 1
                           ('big', None, False), # 2
                           (None, None, False), # 10
                           (None, None, False), # 11
                           (None, None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

    def test4(self):
        """
        Less than 6 players, player 4 missed the big and small blinds
        and must pay the big blind when back in the game.
        """
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           (None, None, False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.sitOut(4)

        self.game.beginTurn(2)
        # (blind, missed, wait)
        self.check_blinds([('big', None, False), # 1
                           (None, None, False), # 2
                           ('small', None, False), # 3
                           (None, 'big', False), # 4
                           ]
                          )
        self.pay_blinds()
        
        self.game.beginTurn(3)
        # (blind, missed, wait)
        self.check_blinds([('small', None, False), # 1
                           ('big', None, False), # 2
                           (None, None, False), # 3
                           (None, 'big', False), # 4
                           ]
                          )
        self.pay_blinds()

        self.game.sit(4)
        
        self.game.beginTurn(4)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           ('big', 'big', False), # 4
                           ]
                          )
        self.pay_blinds()


    def test5(self):
        """
        More than 5 players, player 4 missed the big and small blinds
        and must pay the big and the small blind when back in the game.
        """
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           ('small', None, False), # 2
                           ('big', None, False), # 3
                           (None, None, False), # 4
                           (None, None, False), # 5
                           (None, None, False), # 6
                           ]
                          )
        self.pay_blinds()

        self.game.sitOut(4)

        self.game.beginTurn(2)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           (None, None, False), # 2
                           ('small', None, False), # 3
                           (None, 'big', False), # 4
                           ('big', None, False), # 5
                           (None, None, False), # 6
                           ]
                          )
        self.pay_blinds()
        
        self.game.beginTurn(3)
        # (blind, missed, wait)
        self.check_blinds([(None, None, False), # 1
                           (None, None, False), # 2
                           (None, None, False), # 3
                           (None, 'big', False), # 4
                           ('small', None, False), # 5
                           ('big', None, False), # 6
                           ]
                          )
        self.pay_blinds()

        self.game.sit(4)
        
        self.game.beginTurn(4)
        # (blind, missed, wait)
        self.check_blinds([('big', None, False), # 1
                           (None, None, False), # 2
                           (None, None, False), # 3
                           ('big_and_dead', 'big', False), # 4
                           (None, None, False), # 5
                           ('small', None, False), # 6
                           ]
                          )
        self.pay_blinds()


def run():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBlinds))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()
