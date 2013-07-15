#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2006 Mekensleep
#
# Mekensleep
# 26 rue des rosiers
# 75004 Paris
# licensing@mekensleep.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Authors:
# Pierre-Andre (05/2006)
# Loic Dachary <loic@dachary.org>
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

import time

from pokerengine import pokercards
from pokerengine import pokergame

CallbackIds = None
CallbackArgs = None

# ------------------------------------------------------------ 
def InitCallback():
    global CallbackIds
    global CallbackArgs
    
    CallbackIds = None
    CallbackArgs = None

# ------------------------------------------------------------ 
def Callback(id, *args):
    global CallbackIds
    global CallbackArgs
    
    if not CallbackIds: CallbackIds = []
    if not CallbackArgs: CallbackArgs = []
        
    CallbackIds.append(id)
    CallbackArgs.append(args)

# ------------------------------------------------------------ 
class PokerGameHistoryTestCase(unittest.TestCase):
    
    TestConfDirectory = path.join(TESTS_PATH, 'test-data/conf')
    TestConfigUrl = 'unittest.%s.xml'
    TestConfigFile = 'config'
    
    # ------------------------------------------------------------
    def setUp(self):
        self.game = pokergame.PokerGameServer(PokerGameHistoryTestCase.TestConfigUrl, [PokerGameHistoryTestCase.TestConfDirectory])
        InitCallback()
        
    # ------------------------------------------------------------ 
    def tearDown(self):
        pass
        
    # ------------------------------------------------------------ 
    def testPokerGameMessage(self):
        """Test Poker game messages"""
        
        game_time = time.time()
        
        board = pokercards.PokerCards() 
        hand1 = pokercards.PokerCards(['4d', 'Ts'])
        hand2 = pokercards.PokerCards(['3h', 'Kc'])
        
        history = [
            ('game', 1, 2, 3, game_time, 'variant','betting_structure', [1, 2], 7, { 1 : 500, 2 : 1000}),
            ('wait_for', 1, 'first_round'),
            ('player_list', [1, 2]),
            ('round', 'round1', board, { 1 : hand1, 2 : hand2}),
            ('showdown', board, {1 : hand1, 2 : hand2}),
            ('position', 1, 1),
            ('blind_request', 1, 1000, 100, 'big_and_dead'),
            ('wait_blind', 1),
            ('blind', 1, 1000, 0),
            ('ante_request', 1, 100),
            ('ante', 1, 500),
            ('all-in', 1),
            ('call', 1, 500),
            ('check', 1),
            ('fold', 1),
            ('raise', 1, 500),
            ('canceled', 1, 10),
            ('end', [1], [{ 'serial2share': { 1: 500 } }]),
            ('sitOut', 1),
            ('leave', [(1, 2), (2, 7)]),
            ('finish', 1),
            ('muck', (1,2)),
            ('rebuy', 1, 500),
            ('unknown',)
        ]
                        
        # Register the callback function
        self.game.registerCallback(Callback)
                        
        # Generate all the type of messages managed
        for message in history:
            self.game.historyAdd(*message)

        # All the messages are stored 
        self.failUnlessEqual(self.game.historyGet(), history)
        
        # Check the callback calls
        self.failUnlessEqual(CallbackArgs, history)
        
    # ------------------------------------------------------------ 
    def testHistory2messagesGameEvent(self):
        """Test Poker Game History to message Game event"""
        
        game_time = time.time()
        
        hand_serial = 2 
        variant = 'variant'
        betting_structure = 'betting_structure'
        
        history = [
            ('game', 1, hand_serial, 3, game_time, 'variant','betting_structure', [1, 2], 7, { 1 : 500, 2 : 1000})
        ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, 'hand #%d, %s, %s' % (hand_serial, variant, betting_structure))
        self.failUnlessEqual(message, [])
        
    # ------------------------------------------------------------ 
    def testHistory2messagesWaitForEvent(self):
        """Test Poker Game History to message wait for event"""
        
        history = [
            ('wait_for', 1, 'first_round'),
            ('wait_for', 2, 'late')
        ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        
        message1 = '1 waiting for big blind'
        message2 = '2 waiting for late blind'
        self.failUnlessEqual(message, [message1, message2])
        
    # ------------------------------------------------------------ 
    def testHistory2messagesCheck(self):
        """Test Poker Game History to message check"""
        
        history = [('check', 1)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 checks']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesFold(self):
        """Test Poker Game History to message fold"""
        
        history = [('fold', 1)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 folds']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesRaise(self):
        """Test Poker Game History to message Raise"""
        
        history = [('raise', 1, 5)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 raises 5']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesAllIn(self):
        """Test Poker Game History to message All In"""
        
        history = [('all-in', 1)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 is all in']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesSitOut(self):
        """Test Poker Game History to message Sit out"""
        
        history = [('sitOut', 1)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 sits out']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesAnte(self):
        """Test Poker Game History to message Ante"""
        
        history = [('ante', 1, 5)]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 pays 5 ante']) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesBlind(self):
        """Test Poker Game History to message blind"""
        
        history = [
            ('blind', 1, 10, 5),
            ('blind', 1, 10, 0)
        ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [
            '1 pays 10 blind and 5 dead',
            '1 pays 10 blind'
        ]) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesCancelled(self):
        """Test Poker Game History to message blind"""
        
        history = [
            ('canceled', 1, 1),
            ('canceled', 0, 1),
            ('canceled', 0, 0)
        ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [
            'turn canceled (1 returned to 1)',
            'turn canceled',
            'turn canceled'
        ]) 
        
    # ------------------------------------------------------------ 
    def testHistory2messagesShowdown(self):
        """Test Poker Game History to message showdown"""
        
        board = pokercards.PokerCards(['Ad', 'As'])
        hand1 = pokercards.PokerCards(['4d', 'Ts'])
        hand2 = pokercards.PokerCards(['3h', 'Kc'])
        nocards = pokercards.PokerCards([pokercards.PokerCards.NOCARD, pokercards.PokerCards.NOCARD])
        
        history = [
            ('showdown', board, { 1 : hand1, 2 : hand2}),
            ('showdown', pokercards.PokerCards(), {1 : hand1, 2 : nocards}),
        ]
                        
        subject, message = self.GetMessagesFromHistory(history, str, True)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [
            'Board: Ad As',
            'Cards player 1: 4d Ts',
            'Cards player 2: 3h Kc',
            'Cards player 1: 4d Ts'
        ])
        
    # ------------------------------------------------------------ 
    def testHistory2messagesRound(self):
        """Test Poker Game History to message showdown"""
        
        board = pokercards.PokerCards(['Ad', 'As'])
        hand1 = pokercards.PokerCards(['4d', 'Ts'])
        hand2 = pokercards.PokerCards(['3h', 'Kc'])
        nocards = pokercards.PokerCards([pokercards.PokerCards.NOCARD, pokercards.PokerCards.NOCARD])
        
        history = [
        ('round', 'round1', board, { 1 : hand1, 2 : hand2}),
        ('round', 'round2', pokercards.PokerCards(), {1 : hand1, 2 : nocards}),
        ('round', 'round3', pokercards.PokerCards(), {}),
        ]
                        
        subject, message = self.GetMessagesFromHistory(history, str, True)
        self.failUnlessEqual(subject, '')
        
        self.failUnlessEqual(message, [
        'round1, 2 players',
        'Board: Ad As',
        'Cards player 1: 4d Ts',
        'Cards player 2: 3h Kc',
        'round2, 2 players',
        'Cards player 1: 4d Ts',
        'round3'
        ])
        
    # ------------------------------------------------------------ 
    def testHistory2messagesEnd(self):
        """Test Poker Game History to end message"""
        
        self.game.variant = 'holdem'
        
        # The player 1 wins because all the other players are fold
        game_state = {'serial2share': {1: 5}, 'foldwin': True}
        
        history = [ ('end', [1], [game_state]) ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        message1 = '1 receives 5 (everyone else folded)'
        self.failUnlessEqual(message, [message1])
        
        # Invalid frame
        invalid_frame = { 'type': 'invalid'}
            
        hand1 = pokercards.PokerCards(['Ad', 'As'])
        board = pokercards.PokerCards(['9d', '6s', 'Td', '4d', '4h'])
        
        game_state = {
            'serial2best': {
                1: { 
                    'hi': self.game.eval.best('hi', hand1.tolist(True) + board.tolist(True), []), 
                    'low': self.game.eval.best('low', hand1.tolist(True) + board.tolist(True), []) 
                }
            },
            'foldwin': False
        }
                            
        history = [ ('end', [1], [game_state, invalid_frame]) ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [])
        
        # Left over frame
        frame = { 
        'type': 'left_over',
        'serial' : 1,
        'chips_left' : 10
        }
                    
        history = [ ('end', [1], [game_state, frame]) ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['1 receives 10 odd chips'])
        
        # uncalled frame
        frame = { 
        'type': 'uncalled',
        'serial' : 1,
        'uncalled' : 1
        }
                
        history = [ ('end', [1], [game_state, frame]) ]
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, ['returning uncalled bet 1 to 1'])
        
        # Resolve frame 1
        frame = { 
        'type': 'resolve',
        'serials' : [1, 2, 3],
        'serial2share': {1: 3, 2: 2},
        'hi' : [1, 2],
        'low' : [1],
        'pot' : 5,
        'chips_left' : 3
        }
                    
        hand1 = pokercards.PokerCards(['8h', '2s'])
        hand2 = pokercards.PokerCards(['Ac', '2c'])
        board = pokercards.PokerCards(['9d', '5s', '3h', '4d', '5s'])
        
        game_state ={
            'serial2best': { 
                1: { 
                    'hi' : self.game.eval.best('hi', hand1.tolist(True) + board.tolist(True), []), 
                    'low' : self.game.eval.best('low', hand1.tolist(True) + board.tolist(True), [])
                },
                2: { 
                    'hi' : self.game.eval.best('hi', hand2.tolist(True) + board.tolist(True), []), 
                    'low' : self.game.eval.best('low', hand2.tolist(True) + board.tolist(True), []) 
                }
            },
            'foldwin': False
        }
                
        history = [ ('end', [1], [game_state, frame]) ]
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        
        self.failUnlessEqual(message, [
            '1 shows High card Nine ',
            '1 shows 8, 5, 4, 3, 2 (low)',
            '2 shows Straight Five to Ace ',
            '1 2 tie ',
            '1 wins (low)',
            'winners share a pot of 5 (minus 3 odd chips)',
            '1 receives 3',
            '2 receives 2'
        ])
                                                
        # Resolve frame 2
        frame = { 
             'type': 'resolve',
             'serials' : [1, 2],
             'serial2share': {1: 3, 2: 2},
             'hi' : [1, 2],
             'pot' : 5,
             'chips_left' : 3
        }
                    
        hand1 = pokercards.PokerCards(['Ad', 'As'])
        hand2 = pokercards.PokerCards(['Kd', '3c'])
        board = pokercards.PokerCards(['9d', '6s', 'Td', '4d', '4h'])
        
        game_state = {
            'serial2best': { 
                1: {
                    'hi' : self.game.eval.best('hi', hand1.tolist(True) + board.tolist(True), []), 
                    'low' : self.game.eval.best('low', hand1.tolist(True) + board.tolist(True), []) 
                },
                2: { 
                    'hi' : self.game.eval.best('hi', hand2.tolist(True) + board.tolist(True), [])
                }
            },
            'foldwin': False
        }
                
        history = [ ('end', [1], [game_state, frame]) ]
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [
            '1 shows Two pairs Aces and Fours, Ten kicker ',
            '2 mucks loosing hand',
            '1 2 tie ',
            'winners share a pot of 5 (minus 3 odd chips)',
            '1 receives 3',
            '2 receives 2'
        ])
            
    # ------------------------------------------------------------ 
    def testHistory2messagesEmpty(self):
        """Test Poker Game History to message empty"""
        
        history = [
            ('player_list', [1, 2]),
            ('position', 1, 1),
            ('blind_request', 1, 10, 1, 'big_and_dead'),
            ('wait_blind', 1),
            ('rebuy', 1, 5),
            ('ante_request', 1, 1),
            ('leave', [(1, 2), (2, 7)]),
            ('finish', 1),
            ('muck', (1,2)),
            ('Unknown',)
        ]
        
        subject, message = self.GetMessagesFromHistory(history)
        self.failUnlessEqual(subject, '')
        self.failUnlessEqual(message, [])
        
    # ------------------------------------------------------------ 
    def GetMessagesFromHistory(self, history, serial2name = str, pocket_messages = False):
        self.game.turn_history = []
        self.game.turn_history_reduced = []
        self.game.turn_history_unreduced_position = 0
        for message in history:
            self.game.historyAdd(*message)
        return pokergame.history2messages(self.game, self.game.historyGet(), serial2name, pocket_messages)
    
# ------------------------------------------------------------
def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PokerGameHistoryTestCase))
    # Comment out above and use line below this when you wish to run just
    # one test by itself (changing prefix as needed).
#    suite.addTest(unittest.makeSuite(PokerGameHistoryTestCase, prefix = "test2"))
    return suite
    
# ------------------------------------------------------------
def GetTestedModule():
    return pokergame
  
# ------------------------------------------------------------
def run():
    return unittest.TextTestRunner().run(GetTestSuite())
    
# ------------------------------------------------------------
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/test-gamehistory.py ) ; ( cd ../tests ; make COVERAGE_FILES='../pokerengine/pokergame.py' TESTS='coverage-reset test-gamehistory.py coverage-report' check )"
# End:
