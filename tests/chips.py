#
# Copyright (C) 2004 Mekensleep
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

import unittest
from pokerengine.pokerchips import PokerChips
from pokerengine import pokerchips

class TestChips(unittest.TestCase):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def log(self, string):
        print string

    def test1(self):
        """
        """
        pokerchips.MAX_TOKENS_PER_STACK = 100
        values = [1, 2, 5, 10, 25]
        chips = PokerChips(values, 0)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0])

        chips = PokerChips(values, 200)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 4])
        chips.add([150, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [100, 35, 4, 6, 4])
        self.assertEqual(chips.toint(), 350)
        
        chips = PokerChips(values, 200)
        total = 200 + sum(map(lambda x: x * 150, values))
        chips.add([150, 150, 150, 150, 150])
        self.assertEqual(chips.chips, [100, 100, 100, 100, 194])
        self.assertEqual(chips.toint(), total)
        
        chips = PokerChips(values, 200)
        chips.subtract([0, 20, 0, 0, 0])
        self.assertEqual(chips.chips, [6, 7, 3, 5, 3])
        self.assertEqual(chips.toint(), 160)

        chips = PokerChips(values, 6000)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 236])

        chips = PokerChips(values)
        chips.add(6000)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 236])

        chips = PokerChips(values)
        chips.set([200, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [100, 50, 0, 0, 0])

        chips = PokerChips(values, 200)
        chips.subtract(250)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0])
        
        chips = PokerChips(values, 200)
        self.assertEqual(chips.__str__(), "PokerChips([6, 7, 4, 6, 4]) = 200")
        self.assertEqual(chips.__repr__(), "PokerChips([6, 7, 4, 6, 4])")

    def test2(self):
        """
        """
        pokerchips.MAX_TOKENS_PER_STACK = 30
        values = [1, 2, 5, 10, 25, 5000]
        chips = PokerChips(values, 0)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0, 0])

        chips = PokerChips(values, 200)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 4, 0])
        chips.add([150, 0, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [30, 30, 20, 6, 4, 0])
        self.assertEqual(chips.toint(), 350)
        
        chips = PokerChips(values, 200)
        total = 200 + sum(map(lambda x: x * 150, values))
        chips.add([150, 150, 150, 150, 150, 150])
        self.assertEqual(chips.chips, [30, 30, 30, 31, 44, 151])
        self.assertEqual(chips.toint(), total)
        
        chips = PokerChips(values, 200)
        chips.subtract([0, 20, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [6, 7, 3, 5, 3, 0])
        self.assertEqual(chips.toint(), 160)

        chips = PokerChips(values, 6000)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 36, 1])

        chips = PokerChips(values)
        chips.add(6000)
        self.assertEqual(chips.chips, [6, 7, 4, 6, 36, 1])

        chips = PokerChips(values)
        chips.set([200, 0, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [30, 30, 22, 0, 0, 0])

        chips = PokerChips(values, 200)
        chips.subtract(250)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0, 0])
        
        chips = PokerChips(values, 200)
        self.assertEqual(chips.__str__(), "PokerChips([6, 7, 4, 6, 4, 0]) = 200")
        self.assertEqual(chips.__repr__(), "PokerChips([6, 7, 4, 6, 4, 0])")

def run():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestChips))
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()
