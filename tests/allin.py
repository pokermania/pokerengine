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
#  Henry Precheur <henry@precheur.org>
#  Loic Dachary <loic@gnu.org>
#

import sys, os
sys.path.insert(0, "..")

import unittest
from pokerengine.pokergame import PokerGameServer, PokerGame
from pokerengine.pokerchips import PokerChips
from pokerengine.pokercards import PokerCards
from pokereval import PokerEval

poker_eval = PokerEval()
_initial_money = 10

class TestAllIn(unittest.TestCase):

    def setUp(self, variant, betting):
        output = os.getenv("test_output")
        if output != None:
            self.output_file = open(output, 'a')
        else:
            self.output_file = sys.stderr
        self.game = PokerGameServer("poker.%s.xml", [ "../conf" ])
        self.game.verbose = 3
        self.game.setVariant(variant)
        self.game.setBettingStructure(betting)
        self.game.verbose = 3

    def bestWithStrings(self, side, serial):
        (value, cards) = self.game.bestHand(side, serial)
        return (cards[0], self.game.eval.card2string(cards[1:]))
        
    def tearDown(self):
        del self.game

    def log(self, string):
        print string

    def make_cards(self, visible, *args):
        cards = PokerCards(poker_eval.string2card(args))
        if visible:
            cards.allVisible()
        else:
            cards.allHidden()
        return cards
    
    def make_new_player(self, i, initial_money = _initial_money):
        self.assert_(self.game.addPlayer(i))
        player = self.game.serial2player[i]
        player.money = PokerChips(self.game.chips_values, initial_money)
        player.buy_in_payed = True
        self.assert_(self.game.sit(i))
        player.auto_blind_ante = True

    def prepareGame(self, nplayers):
        pot = 91
        self.money = 1
        self.player = {}
        money = self.money
        game = self.game
        player = self.player
        for serial in xrange(1,nplayers+1):
            self.make_new_player(serial, money)
            player[serial] = game.serial2player[serial]
        game.beginTurn(1)
        game.pot = PokerChips(game.chips_values, pot)


class TestCommonAllIn(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "holdem", "2-4-no-limit")

    def test1_AllIn(self):
        #
        # 5 players (counting 1-5 included).
        # In pre-flop, player 3 goes all-in immediately.
        # All other players also go all in, therefore all cards
        # are dealt and the game ends.
        #
        # player[1] money = 50
        # player[2] money = 10
        # player[3] money = 10
        # player[4] money = 200
        # player[5] money = 10
        #
        # player[1] side_pot = 130 (p[1]=50 + p[2]=10 + p[3]=10 + p[4]=50 + p[5]=10) 
        # player[2] side_pot = 50  (p[1]=10 + p[2]=10 + p[3]=10 + p[4]=10 + p[5]=10) 
        # player[3] side_pot = 50  (p[1]=10 + p[2]=10 + p[3]=10 + p[4]=10 + p[5]=10) 
        # player[4] side_pot = 280 (p[1]=50 + p[2]=10 + p[3]=10 + p[4]=200 + p[5]=10) 
        # player[5] side_pot = 50  (p[1]=10 + p[2]=10 + p[3]=10 + p[4]=10 + p[5]=10) 
        #
        #
        game = self.game
        player = {}
        for serial in xrange(1,6):
            player[serial] = serial - 1
            self.make_new_player(serial, 10)
        game.serial2player[1].money.set(50);
        game.serial2player[4].money.set(200);
        game.beginTurn(1)
        self.assertEqual(game.state, "pre-flop")

        for serial in (4, 5, 1):
            self.assertEqual(game.position, player[serial])
            game.call(serial)
        #
        # player 2 goes all in, 1000 is more than he has
        #
        game.callNraise(2, 1000) 
        self.assertEqual(game.inGameCount(), 4)
        self.assertEqual(game.notFoldCount(), 5)
        player2 = game.serial2player[2];
        self.assertEqual(player2.bet.toint(), 10)
        self.assertEqual(player2.money.toint(), 0)
        self.assertEqual(game.highestBetNotFold(), 10)
        self.assertEqual(game.highestBetInGame(), 2)
        self.assertEqual(game.position, player[3])
        self.assertEqual(game.serialsInGame(), [1, 3, 4, 5])
        self.assertEqual(game.serialsNotFold(), [1, 2, 3, 4, 5])
        #
        # player 3 tries to check but is not allowed to, should
        # return False and have no side effect 
        #
        self.assertEqual(game.check(3), False)

        #
        # Inhibit the distributeMoney and showdown so that we
        # can check the values of the side pots.
        #
        game.is_directing = False
        #
        # All other players call, i.e. they all go all in since they
        # all started with the same amount of chips
        #
        for serial in (3, 4, 5, 1):
            self.assertEqual(game.position, player[serial])
            game.callNraise(serial, 1000)
        self.assertEqual(game.side_pots,
                         {'building': 0, 'pots': [
            [50, 50],
            [80, 130],
            [150, 280]
            ],
                          'contributions': {
            0: {0:
                {1: 10,
                 2: 10,
                 3: 10,
                 4: 10,
                 5: 10},
                1:
                {1: 40,
                 4: 40},
                2:
                {4: 150}
                }
            }
                          })
        self.assertEqual(game.serial2player[1].side_pot_index, 1)
        self.assertEqual(game.serial2player[2].side_pot_index, 0)
        self.assertEqual(game.serial2player[3].side_pot_index, 0)
        self.assertEqual(game.serial2player[4].side_pot_index, 2)
        self.assertEqual(game.serial2player[5].side_pot_index, 0)

        self.assertEqual(game.inGameCount(), 0)
        self.assertEqual(game.notFoldCount(), 5)
        self.assertEqual(game.state, "end")
        
class TestAllInCase2(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "holdem", "2-4-no-limit")

    def test1_AllIn(self):
        #
        # 5 players (counting 1-5 included).
        # flop: player 2 4 fold
        # turn: player 3 bets, player raises 5 all-in, player 1 calls
        #       player 3 raises all in, player 5 calls all in
        #
        #
        game = self.game
        player = {}
        for serial in xrange(1,6):
            player[serial] = serial - 1
            self.make_new_player(serial, 52)
        game.serial2player[3].money.set(202);
        game.serial2player[5].money.set(72);
        game.serial2player[1].money.set(102);
        game.beginTurn(2)

        self.assertEqual(game.state, "pre-flop")
        game.fold(4)
        game.call(5)
        game.call(1)
        game.fold(2)
        game.check(3)
        self.assertEqual(game.inGameCount(), 3)

        #
        # Inhibit the distributeMoney and showdown so that we
        # can check the values of the side pots.
        #
        game.is_directing = False

        self.assertEqual(game.state, "flop")
        game.callNraise(3, 50)   # bet 50 (200 - 50 = 150 remaining)
        game.callNraise(5, 70)   # raises 70 (50 to call, raise 20) => all in
        game.call(1)             # calls 70 (70 to call, 100 - 70 = 30 remaining)
        game.callNraise(3, 150)  # raises 150 (20 to call, raise 130)  => all in
        game.call(1)             # calls 30 => all in

        self.assertEqual(game.side_pots,
                         {'building': 0, 'pots':
                          [[217, 217],
                           [60, 277],
                           [100, 377]],
                          'contributions':
                          {0: {0: {1: 2, 2: 1, 3: 2, 5: 2}},
                           1: {0: {1: 70, 3: 70, 5: 70},
                               1: {1: 30, 3: 30},
                               2: {3: 100}}}
                          })
        self.assertEqual(game.serial2player[1].side_pot_index, 1) # 277
        self.assertEqual(game.serial2player[3].side_pot_index, 2) # 377
        self.assertEqual(game.serial2player[5].side_pot_index, 0) # 217

        self.assertEqual(game.inGameCount(), 0)
        self.assertEqual(game.notFoldCount(), 3)
        self.assertEqual(game.state, "end")
        
class TestRaise(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "holdem", "15-30-no-limit")

    def test1_Raise(self):
        #
        # 2 players (counting 1-2 included).
        #
        # player[1] money = 2000
        # player[2] money = 2000
        #
        game = self.game
        player = {}
        for serial in xrange(1,3):
            player[serial] = serial - 1
            self.make_new_player(serial, 2000)
        game.beginTurn(1)
        self.assertEqual(game.state, "pre-flop")

        self.assertEqual(game.position, player[2])
        game.call(2)

        game.callNraise(1, 500) 
        self.assertEqual(game.betLimits(2), (1000, 1985, 500))
        
class TestHoldemAllIn(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "holdem", "0-0-limit")
        
    def test1_ChipLeft(self):
        """
        Two players are even, 3 to split, 1 odd chip
        """
        game = self.game
        self.prepareGame(2)
        game.pot = PokerChips(game.chips_values, 3)
        game.side_pots = {'pots': { 0: (3, 3) } }
        game.serial2player[1].hand = self.make_cards(False, '7h', '3h')
        game.serial2player[2].hand = self.make_cards(False, '7d', '3s')
        game.board = self.make_cards(True, '6h', '4d', '7s', 'Kc', '7c')
        game.distributeMoney()
        self.assertEqual(len(game.winners), 2)
        self.assertEqual(game.pot.toint(), 0)
        winner = game.serial2player[1]
        self.assertEqual(winner.money.toint(), 2)
        #
        # Dealer is player[1], player next to dealer is player[2],
        # the odd chips go to the player next to the dealer
        #
        winner = game.serial2player[2]
        self.assertEqual(winner.money.toint(), 3)
        game.endTurn()

class TestOmaha8AllIn(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "omaha8", "0-0-limit")
        
    def dealCardsOne(self):
        """
        
        1) A player is all in and wins nothing. However, he
           was all-in for an amount greater than the highest bet
           and gets back the difference.
        2) A player is all in and wins one side of the pot.
        3) Two players tie for one side of the pot.
        4) Odd chips are distributed.
        5) A player is all in for an amount larger than all other
           bets and get it back.
        
        player[1] is all-in with a side pot of 91 and loses but
                  get the extra chips back (200 - 91) = 109
        player[2] is all-in with a side pot of 51
                  player[2] wins hi (Straight) => 51/2 = 25
                  player[5] win lo (NoPair)     => 51/2 = 25 
        player[3,4,5] are still playing for a pot of (91 - 51) = 40
                  player[3,4] tie for hi (Pair)=> (40 / 2) / 2 = 10 each
                  player[5] win lo (Nopair)     => (40 / 2) = 20

        player[2] inherit 1 odd chip
        """

        game = self.game
        game.side_pots = {'pots': {
             0: (51, 51),
             1: (40, 91),
             2: (109, 200)
            }}
        player = self.player
        game.board = self.make_cards(True, 'As', '4d', '5h', '7d', '9c')

        player[1].hand = self.make_cards(False, 'Th', 'Js', 'Qs', '2c')
        player[1].side_pot_index = 2
        player[1].all_in = True
        self.assertEqual(self.bestWithStrings("hi", 1),
                          ('NoPair', ['As', 'Qs', 'Js', '9c', '7d']))
        
        player[2].hand = self.make_cards(False, '6c', '8c', 'Qd', 'Kd')
        player[2].side_pot_index= 0
        player[2].all_in = True
        self.assertEqual(self.bestWithStrings("hi", 2),
                         ('Straight', ['9c', '8c', '7d', '6c', '5h']))
        self.assertEqual(self.bestWithStrings("low", 2),
                         ('NoPair', ['8c', '6c', '5h', '4d', 'As']))

        player[3].hand = self.make_cards(False, 'Ac', '8s', 'Qh', 'Kh')
        player[3].side_pot_index= 1
        self.assertEqual(self.bestWithStrings("hi", 3),
                         ('OnePair', ['As', 'Ac', 'Kh', '9c', '7d']))
        self.assertEqual(self.bestWithStrings("low", 3),
                         ('NoPair', ['8s', '7d', '5h', '4d', 'Ac']))
        
        player[4].hand = self.make_cards(False, 'Ad', '8d', 'Qc', 'Kc')
        player[4].side_pot_index= 1
        self.assertEqual(self.bestWithStrings("hi", 4),
                         ('OnePair', ['As', 'Ad', 'Kc', '9c', '7d']))

        player[5].hand = self.make_cards(False, '2s', '6s', 'Jd', 'Ks')
        player[5].side_pot_index= 1
        self.assertEqual(self.bestWithStrings("low", 5),
                          ('NoPair', ['6s', '5h', '4d', '2s', 'As']))

    def dealCardsTwo(self):
        """
        Simple situation, no all-in, player[3] with straight
        """
        game = self.game
        game.side_pots = {'pots': {
             0: (91, 91)
            }}
        player = self.player
        game.board = self.make_cards(True, 'As', '4d', '5h', '7d', '9c')

        player[1].hand = self.make_cards(False, 'Th', 'Js', 'Qs', '2c')
        self.assertEqual(self.bestWithStrings("hi", 1),
                         ('NoPair', ['As', 'Qs', 'Js', '9c', '7d']))
        self.assertEqual(self.bestWithStrings("low", 1),
                         ('Nothing', []))
        
        player[2].hand = self.make_cards(False, 'Ac', '8s', 'Qh', 'Kh')
        self.assertEqual(self.bestWithStrings("hi", 2),
                         ('OnePair', ['As', 'Ac', 'Kh', '9c', '7d']))
        self.assertEqual(self.bestWithStrings("low", 2),
                         ('NoPair', ['8s', '7d', '5h', '4d', 'Ac']))
        
        player[3].hand = self.make_cards(False, '6c', '8c', 'Qd', 'Kd')
        self.assertEqual(self.bestWithStrings("hi", 3),
                         ('Straight', ['9c', '8c', '7d', '6c', '5h']))
        self.assertEqual(self.bestWithStrings("low", 3),
                         ('NoPair', ['8c', '6c', '5h', '4d', 'As']))

        player[4].hand = self.make_cards(False, '2s', 'Ts', 'Jd', '3s')
        self.assertEqual(self.bestWithStrings("hi", 4),
                         ('Straight', ['5h', '4d', '3s', '2s', 'As']))
        self.assertEqual(self.bestWithStrings("low", 4),
                         ('NoPair', ['5h', '4d', '3s', '2s', 'As']))

        player[5].hand = self.make_cards(False, 'Ad', '8d', 'Qc', 'Kc')
        self.assertEqual(self.bestWithStrings("hi", 5),
                         ('OnePair', ['As', 'Ad', 'Kc', '9c', '7d']))
        self.assertEqual(self.bestWithStrings("low", 5),
                         ('NoPair', ['8d', '7d', '5h', '4d', 'Ad']))

    def test1_distributeMoney(self):
        self.prepareGame(5)
        self.dealCardsOne()
        game = self.game
        money = self.money
        player = self.player
        game.distributeMoney()
        self.assertEqual(len(game.winners), 4)
        self.assertEqual(game.pot.toint(), 0)
        self.assertEqual(player[1].money.toint(), money + 109)
        self.assertEqual(player[2].money.toint(), money + 25 + 1)
        self.assertEqual(player[3].money.toint(), money + 10)
        self.assertEqual(player[4].money.toint(), money + 10)
        self.assertEqual(player[5].money.toint(), money + 25 + 20)

    def test2_showdown(self):
        self.prepareGame(5)
        self.dealCardsOne()
        game = self.game
        money = self.money
        player = self.player
        game.distributeMoney()
        game.showdown()
        self.assertEqual(game.side2winners["hi"], [2, 3, 4])
        self.assertEqual(game.side2winners["low"], [5])
        self.assertEqual(player[1].hand.areVisible(), False)
        self.assertEqual(player[2].hand.areVisible(), True)
        self.assertEqual(player[3].hand.areVisible(), True)
        self.assertEqual(player[4].hand.areVisible(), True)
        self.assertEqual(player[5].hand.areVisible(), True)

    def test3_showdown(self):
        self.prepareGame(5)
        self.dealCardsTwo()
        game = self.game
        money = self.money
        player = self.player
        game.distributeMoney()
        game.showdown()
        self.assertEqual(game.side2winners["hi"], [3])
        self.assertEqual(game.side2winners["low"], [4])
        self.assertEqual(player[1].hand.areVisible(), False)
        self.assertEqual(player[2].hand.areVisible(), True)
        self.assertEqual(player[3].hand.areVisible(), True)
        self.assertEqual(player[4].hand.areVisible(), True)
        self.assertEqual(player[5].hand.areVisible(), False)
        
class TestHoldemPlayBoard(TestAllIn):

    def setUp(self):
        TestAllIn.setUp(self, "holdem", "0-0-limit")
        
    def dealCardsOne(self):
        """
        Two players play the board
        """
        game = self.game
        game.side_pots = {'pots': {
             0: (91, 91)
            }}
        player = self.player
        game.board = self.make_cards(True, 'As', 'Ac', 'Ad', '7d', '7c')

        player[1].hand = self.make_cards(False, 'Th', 'Js')
        self.assertEqual(self.bestWithStrings("hi", 1),
                         ('FlHouse', ['As', 'Ac', 'Ad', '7c', '7d']))
        
        player[2].hand = self.make_cards(False, '9c', '8s')
        self.assertEqual(self.bestWithStrings("hi", 2),
                         ('FlHouse', ['As', 'Ac', 'Ad', '7c', '7d']))
        
    def test1_showdown(self):
        self.prepareGame(2)
        self.dealCardsOne()
        game = self.game
        money = self.money
        player = self.player
        game.distributeMoney()
        self.assertEqual(game.side2winners["hi"], [1, 2])

def run():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRaise))
    suite.addTest(unittest.makeSuite(TestHoldemAllIn))
    suite.addTest(unittest.makeSuite(TestCommonAllIn))
    suite.addTest(unittest.makeSuite(TestAllInCase2))
    suite.addTest(unittest.makeSuite(TestOmaha8AllIn))
    suite.addTest(unittest.makeSuite(TestHoldemPlayBoard))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()
