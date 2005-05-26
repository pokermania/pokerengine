#
# Copyright (C) 2005 Mekensleep
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
#

import sys, os
sys.path.insert(0, "..")

from pprint import pprint
from string import split
import unittest
from pokerengine.pokergame import PokerGameServer, history2messages
from pokerengine.pokercards import PokerCards
from pokerengine.pokerchips import PokerChips

class PokerPredefinedDecks:
    def __init__(self, decks):
        self.decks = decks
        self.index = 0
        
    def shuffle(self, deck):
        deck[:] = self.decks[self.index][:]
        self.index += 1
        if self.index >= len(self.decks):
            self.index = 0
        
class TestHistory(unittest.TestCase):

    def setUp(self):
        self.game = PokerGameServer("poker.%s.xml", [ "../conf" ])
        self.game.verbose = 3
        self.game.setVariant("holdem")
        self.game.setBettingStructure("2-4-limit")
        predefined_decks = [
            "8d 2h 2c 8c 4c Kc Ad 9d Ts Jd 5h Tc 4d 9h 8h 7h 9c 2s 3c Kd 5s Td 5d Th 3s Kh Js Qh 7d 2d 3d 9s Qd Ac Jh Jc Qc 6c 7s Ks 5c 4h 7c 4s Qs 6s 6h Ah 6d As 3h 8s", # distributed from the end
            ]
        self.game.shuffler = PokerPredefinedDecks(map(lambda deck: self.game.eval.string2card(split(deck)), predefined_decks))

    def tearDown(self):
        del self.game

    def make_new_player(self, serial, seat):
        game = self.game
        self.failUnless(game.addPlayer(serial, seat))
        self.failUnless(game.payBuyIn(serial, game.buyIn()))
        self.failUnless(game.sit(serial))
        game.botPlayer(serial)
        game.autoBlindAnte(serial)

    def test1(self):
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        self.assertEqual(str(history2messages(self.game, self.game.turn_history, pocket_messages = True)), "('hand #1, holdem, 2-4-limit', ['2 pays 1 blind', '3 pays 2 blind', 'pre-flop, 4 players', 'Cards player 1: 8s Ah', 'Cards player 2: 3h 6h', 'Cards player 3: As 6s', 'Cards player 4: 6d Qs', '4 calls 2', '1 calls 2', '2 calls 1', '3 checks', 'flop, 4 players', 'Board: 4s 7c 4h', 'Cards player 1: 8s Ah', 'Cards player 2: 3h 6h', 'Cards player 3: As 6s', 'Cards player 4: 6d Qs', '2 checks', '3 checks', '4 checks', '1 checks', 'turn, 4 players', 'Board: 4s 7c 4h 5c', 'Cards player 1: 8s Ah', 'Cards player 2: 3h 6h', 'Cards player 3: As 6s', 'Cards player 4: 6d Qs', '2 raise 4', '3 folds', '4 folds', '1 calls 4', 'river, 2 players', 'Board: 4s 7c 4h 5c Ks', 'Cards player 1: 8s Ah', 'Cards player 2: 3h 6h', '2 raise 4', '1 calls 4', '2 shows Straight Seven to Three for hi ', '1 mucks loosing hand', '2 wins hi ', '2 receives 24'])")

    def test2(self):
        for (serial, seat) in ((1, 0), (2, 1), (3, 2), (4, 3)):
            self.make_new_player(serial, seat)
        self.game.beginTurn(1)
        for event in self.game.historyGet():
            if event[0] == "round":
                (type, name, board, pockets) = event
                for (player_serial, pocket) in pockets.iteritems():
                    pocket.loseNotVisible()
                    self.assertEqual(pocket, PokerCards([PokerCards.NOCARD] * pocket.len()))
        
def run():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestHistory))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()
