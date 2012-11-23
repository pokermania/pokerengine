#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
#  Loic Dachary <loic@gnu.org>
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

from pokerengine.pokergame import PokerGameServer
from pokerengine.pokercards import PokerCards
from pokereval import PokerEval

poker_eval = PokerEval()
_initial_money = 1000

class TestPosition(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [path.join(TESTS_PATH, '../conf')])
        self.game.setVariant("holdem")
        self.game.setBettingStructure("1-2_20-200_limit")

    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_cards(self, *args):
        return PokerCards(poker_eval.string2card(args))
    
    def make_new_player(self, i, initial_money = _initial_money):
        self.assert_(self.game.addPlayer(i))
        player = self.game.serial2player[i]
        player.money = initial_money
        player.buy_in_payed = True
        self.assert_(self.game.sit(i))
        player.auto_blind_ante = True

    def test1(self):
        """
        """
        game = self.game
        player = {}
        for serial in xrange(1,6):
            self.make_new_player(serial)
            player[serial] = game.serial2player[serial]

        game.beginTurn(1)
        for serial in (2, 3, 4, 5):
            player[serial].hand = self.make_cards('__', '__')

        player[1].hand = self.make_cards('Ad', 'As')
        self.assertTrue(540 <= game.handEV(1, 100000) <= 570)
        player[1].hand = self.make_cards('2c', '7s')
        self.assertTrue(100 <= game.handEV(1, 100000) <= 120)
        game.board = self.make_cards('2c', '3c', '4s')
        player[1].hand = self.make_cards('2s', '7s')
        self.assertTrue(160 <= game.handEV(1, 100000) <= 180)

        game.board = self.make_cards('2c', '3c', '4s', '4c')
        player[1].hand = self.make_cards('2s', '7s')
        self.assertTrue(70 <= game.handEV(1, 100000) <= 80)

        game.board = self.make_cards('2c', '3c', '4s', '4c', 'Kc')
        player[1].hand = self.make_cards('2s', '7s')
        self.assertTrue(3 <= game.handEV(1, 100000) <= 9)

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPosition))
    return suite

def run():
    return unittest.TextTestRunner().run(GetTestSuite())

if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/eval.py ) ; ( cd ../tests ; make TESTS='eval.py' check )"
# End:
