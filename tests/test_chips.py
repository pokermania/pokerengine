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

from pokerengine.pokerchips import PokerChips
from pokerengine import pokerchips


class TestChips(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test1(self):
        pokerchips.MAX_CHIPS_PER_STACK = 100
        values = [100, 200, 500, 1000, 2500]
        chips = PokerChips(values, 0)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0])

        chips = PokerChips(values, 20000)
        self.assertEqual(chips.toint(), 20000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 4])
        chips.add([150, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [100, 35, 4, 6, 4])
        self.assertEqual(chips.toint(), 35000)
        
        chips = PokerChips(values, 20000)
        total = 20000 + sum(map(lambda x: x * 150, values))
        chips.add([150, 150, 150, 150, 150])
        self.assertEqual(chips.chips, [100, 100, 100, 100, 194])
        self.assertEqual(chips.toint(), total)
        
        chips = PokerChips(values, 20000)
        chips.subtract([0, 20, 0, 0, 0])
        self.assertEqual(chips.chips, [8, 6, 3, 5, 3])
        self.assertEqual(chips.toint(), 16000)

        chips = PokerChips(values, 600000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 236])

        chips = PokerChips(values)
        chips.add(600000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 236])

        chips = PokerChips(values)
        chips.set([200, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [100, 50, 0, 0, 0])

        chips = PokerChips(values, 200)
        chips.subtract(250)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0])
        
        chips = PokerChips(values, 20000)
        self.assertEqual(chips.__str__(), "PokerChips([8, 6, 4, 6, 4]) = 20000 (-0)")
        self.assertEqual(chips.__repr__(), "PokerChips([8, 6, 4, 6, 4])")

    def test2(self):
        pokerchips.MAX_CHIPS_PER_STACK = 30
        values = [100, 200, 500, 1000, 2500, 500000]
        chips = PokerChips(values, 0)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0, 0])

        chips = PokerChips(values, 20000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 4, 0])
        chips.add([150, 0, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [30, 30, 20, 6, 4, 0])
        self.assertEqual(chips.toint(), 35000)
        
        chips = PokerChips(values, 20000)
        total = 20000 + sum(map(lambda x: x * 150, values))
        chips.add([150, 150, 150, 150, 150, 150])
        self.assertEqual(chips.chips, [30, 30, 30, 31, 44, 151])
        self.assertEqual(chips.toint(), total)
        
        chips = PokerChips(values, 20000)
        chips.subtract([0, 20, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [8, 6, 3, 5, 3, 0])
        self.assertEqual(chips.toint(), 16000)

        chips = PokerChips(values, 600000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 36, 1])

        chips = PokerChips(values)
        chips.add(600000)
        self.assertEqual(chips.chips, [8, 6, 4, 6, 36, 1])

        chips = PokerChips(values)
        chips.set([200, 0, 0, 0, 0, 0])
        self.assertEqual(chips.chips, [30, 30, 22, 0, 0, 0])

        chips = PokerChips(values, 20000)
        chips.subtract(25000)
        self.assertEqual(chips.chips, [0, 0, 0, 0, 0, 0])
        
        chips = PokerChips(values, 20000)
        self.assertEqual(chips.__str__(), "PokerChips([8, 6, 4, 6, 4, 0]) = 20000 (-0)")
        self.assertEqual(chips.__repr__(), "PokerChips([8, 6, 4, 6, 4, 0])")

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestChips))
    return suite
    

def run():
    return unittest.TextTestRunner().run(GetTestSuite())
    
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
