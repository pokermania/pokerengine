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

class TestBuyIn(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [path.join(TESTS_PATH, '../conf')])
        self.game.setVariant("holdem")
        self.game.setBettingStructure("1-2_20-200_limit")

    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_new_player(self, serial, seat):
        game = self.game
        self.failUnless(game.addPlayer(serial, seat))
        self.failUnless(game.payBuyIn(serial, game.bestBuyIn()))
        self.failUnless(game.sit(serial))
        game.botPlayer(serial)
        game.noAutoBlindAnte(serial)

    def pay_blinds(self):
        game = self.game
        for serial in game.serialsAll():
            game.autoBlindAnte(serial)
        for serial in game.serialsAll():
            game.noAutoBlindAnte(serial)

    def test1(self):
        game = self.game
        self.failUnless(game.addPlayer(1))
        self.failIf(game.payBuyIn(1, game.buyIn() - 1))
        self.failIf(game.getPlayer(1).buy_in_payed)
        self.failIf(game.payBuyIn(1, game.maxBuyIn() + 1))
        self.failIf(game.getPlayer(1).buy_in_payed)
        self.failUnless(game.payBuyIn(1, game.bestBuyIn()))
        self.failUnless(game.getPlayer(1).buy_in_payed)

        self.failUnless(game.addPlayer(2))
        self.failUnless(game.payBuyIn(2, game.maxBuyIn()))
        self.failUnless(game.getPlayer(2).buy_in_payed)

    def test2(self):
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        player1money = self.game.getPlayer(1).money
        self.failIf(self.game.rebuy(300000, self.game.bestBuyIn()))
        self.failUnless(self.game.rebuy(1, 1))
        self.assertEqual(self.game.getPlayer(1).money, player1money + 1)
        self.failIf(self.game.rebuy(1, self.game.maxBuyIn()))
        self.assertEqual(self.game.getPlayer(1).money, player1money + 1)
        self.failUnless(self.game.rebuy(1, 1))
        self.assertEqual(self.game.getPlayer(1).money, player1money + 2)
        self.pay_blinds()
        money = self.game.getPlayerMoney(1)
        self.failUnless(self.game.rebuy(1, 1))
        self.assertEqual(self.game.getPlayerMoney(1), money + 1)

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBuyIn))
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
# compile-command: "( cd .. ; ./config.status tests/buyin.py ) ; ( cd ../tests ; make TESTS='buyin.py' check )"
# End:
