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
#  Loic Dachary <loic@dachary.org>
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

from pokerengine.pokergame import PokerGameServer
from pokereval import PokerEval

poker_eval = PokerEval()
_initial_money = 1000

class TestDeal(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [path.join(TESTS_PATH, 'conf')])
        self.game.setVariant("7stud")
        self.game.setBettingStructure("ante-10-20-limit")

    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_new_player(self, i, initial_money):
        self.assert_(self.game.addPlayer(i))
        player = self.game.serial2player[i]
        player.money = initial_money
        player.buy_in_payed = True
        self.assert_(self.game.sit(i))
        player.auto_blind_ante = True

    def test1(self):
        """
        8 players, non fold, last card is a community card
        """
        game = self.game
        for serial in xrange(1,9):
            self.make_new_player(serial, 2000)
        game.beginTurn(1)
        while True:
            if game.isLastRound():
                self.assertEqual(len(game.board.tolist(True)), 1)

            for x in xrange(1,9):
                serial = game.getSerialInPosition()
                self.assertEqual(game.check(serial), True)
                    
            if not game.isRunning():
                break;

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDeal))
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
# compile-command: "( cd .. ; ./config.status tests/deal.py ) ; ( cd ../tests ; make TESTS='deal.py' check )"
# End:
