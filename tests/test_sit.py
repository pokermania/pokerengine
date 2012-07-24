# -*- mode: python -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2005, 2006 Mekensleep
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

class TestSit(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [path.join(TESTS_PATH, 'conf')])
        self.game.setVariant("holdem")
        self.game.setBettingStructure("2-4-limit")

    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_new_player(self, serial, seat):
        game = self.game
        self.failUnless(game.addPlayer(serial, seat))
        self.failUnless(game.payBuyIn(serial, game.bestBuyIn()))
        self.failUnless(game.sit(serial))

    def pay_blinds(self):
        game = self.game
        for serial in game.serialsAll():
            game.autoBlindAnte(serial)
        for serial in game.serialsAll():
            game.noAutoBlindAnte(serial)

    def bot_players(self):
        game = self.game
        for serial in game.serialsAll():
            game.botPlayer(serial)
        
    def check_blinds(self, descriptions):
        players = self.game.playersAll()
        players.sort(key=lambda i: i.seat)
        for player in players:
            (blind, missed, wait) = descriptions.pop(0)
            if(blind != player.blind or missed != player.missed_blind or wait != player.wait_for):
                print "check_blinds FAILED actual %s != from expected %s" % ( (player.blind, player.missed_blind, player.wait_for), (blind, missed, wait) )
                self.fail()
            
            
    def test1_player_arrive_during_blinds(self):
        for (serial, seat) in ((1, 0), (2, 1)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        #
        # New player comes in while others are paying the blinds.
        # He does not participate in the game.
        #
        for (serial, seat) in ((3, 2),):
            self.make_new_player(serial, seat)
        self.pay_blinds()
        self.assertEqual(self.game.player_list, [1,2])
        self.bot_players()

        #
        # Next round the new player is waiting for the late blind
        #
        self.game.beginTurn(2)
        self.assertEqual(self.game.player_list, [1,2])
        self.pay_blinds()

        #
        # This round the new player is in
        #
        self.game.beginTurn(3)
        self.assertEqual(self.game.player_list, [1,2,3])
        self.pay_blinds()

    def test2_player_sitout_during_blinds(self):
        for (serial, seat) in ((1, 0), (2, 1), (3, 2)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        #
        # player 1 deals
        # player 2 small blind
        # player 3 big blind
        #
        # player 3 sits out while player 2 is in position : she is
        # marked as sit_out_next_turn because she is not in position
        #
        self.assertEqual(2, self.game.getSerialInPosition())
        self.game.sitOutNextTurn(3)
        player3 = self.game.getPlayer(3)
        self.assertEqual("big", player3.blind)
        self.failUnless(player3.isSit())
        self.assertEqual(True, player3.sit_out_next_turn)
        #
        # player 3 sits back and because she is sit_out_next_turn,
        # which can only happen in the blind/ante round if she 
        # sat out after being included in the player list for the
        # turn, she is sit. By contrast, if she had been sit
        # during the blind/ante turn, she would have been marked
        # wait_for = "first_round"
        #
        self.game.sit(3)
        self.assertEqual(False, player3.sit_out_next_turn)
        self.assertEqual(False, player3.wait_for)


def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSit))
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
# compile-command: "( cd .. ; ./config.status tests/sit.py ) ; ( cd ../tests ; make TESTS='sit.py' check )"
# End:
