# -*- mode: python -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2008 Bradley M. Kuhn <bkuhn@ebb.org>
# Copyright (C) 2006             Mekensleep <licensing@mekensleep.com>
#                                26 rue des rosiers, 75004 Paris
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
#  Bradley M. Kuhn <bkuhn@ebb.org>
#  Pierre-Andre (05/2006)
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

from tests.testmessages import get_messages, clear_all_messages
import logging
from tests.testmessages import TestLoggingHandler
logger = logging.getLogger()
handler = TestLoggingHandler()
logger.addHandler(handler)
logger.setLevel(10)

from pokerengine import pokerprizes

class PokerPrizesTestCase(unittest.TestCase):
    TestConfDirectory = path.join(TESTS_PATH, 'conf')
        
    # ---------------------------------------------------------
    def setUp(self):
        self.dirs = [PokerPrizesTestCase.TestConfDirectory]
    
    # -------------------------------------------------------
    def tearDown(self):
        pass

    # -------------------------------------------------------
    def test01_algorithmPrizeInterface(self):
        """test01_algorithmPrizeInterface
        Test the payout structure of the Algorithm prize interface"""
        pa = pokerprizes.__dict__["PokerPrizesAlgorithm"](buy_in_amount = 100, player_count = 4)
        self.assertEquals(pa.buy_in, 100)
        self.assertEquals(pa.player_count, 4)

        self.failUnlessEqual(pa.getPrizes(), [400])
        
        for cnt in range(5, 9):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)
            if cnt == 5:
                pa.removePlayer()
                self.assertEquals(pa.player_count, 4)
                self.failUnlessEqual(pa.getPrizes(), [400])
                pa.addPlayer()
                self.assertEquals(pa.player_count, cnt) 
                self.failUnlessEqual(pa.getPrizes(), [375, 125])

        self.failUnlessEqual(pa.getPrizes(), [600, 200])

        for cnt in range(9, 19):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)
        self.failUnlessEqual(pa.getPrizes(), [1125, 450, 225])
        
        for cnt in range(19, 29):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)

        self.failUnlessEqual(pa.getPrizes(), [1575, 700, 350, 175])
        
        for cnt in range(29, 39):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)

        self.failUnlessEqual(pa.getPrizes(), [1902, 950, 237, 237, 237, 237])
        
        for cnt in range(39, 49):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)

        self.failUnlessEqual(len(pa.getPrizes()), int(48 * 0.20))
        
        for cnt in range(49, 199):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)

        self.failUnlessEqual(len(pa.getPrizes()), int(198 * 0.15))
        
        for cnt in range(199, 299):
            pa.addPlayer()
            self.failUnlessEqual(pa.player_count, cnt)

        self.failUnlessEqual(len(pa.getPrizes()), int(298 * 0.10))
    # -------------------------------------------------------
    def test02_tablePrizeInterface(self):
        """test02_tablePrizeInterface
        Test the payout structure of the table prize interface"""
        pt = pokerprizes.__dict__["PokerPrizesTable"](buy_in_amount = 100, player_count = 2, config_dirs = self.dirs)
        self.assertEquals(pt.buy_in, 100)
        self.assertEquals(pt.player_count, 2)

        self.failUnlessEqual(pt.getPrizes(), [200])
        
        for player in range(4, 7):
            pt.addPlayer()
            if player == 4:
                pt.removePlayer()
                self.assertEquals(pt.player_count, 2)
                self.failUnlessEqual(pt.getPrizes(), [200])
                pt.addPlayer()
                self.assertEquals(pt.player_count, 3)
                self.failUnlessEqual(pt.getPrizes(), [300])

        self.failUnlessEqual(pt.getPrizes(), [350, 150])
        
        for player in range(7, 28):
            pt.addPlayer()
        self.failUnlessEqual(pt.getPrizes(), [1300, 780, 520])
        
        for player in range(28, 48):
            pt.addPlayer()
        self.failUnlessEqual(pt.getPrizes(), [1702, 1012, 690, 506, 368, 322])
        
        for player in range(48, 198):
            pt.addPlayer()
        self.failUnlessEqual(pt.getPrizes(), [5394, 3253, 1989, 1548, 1332, 1136, 921, 725, 509, 392, 294, 294, 294, 245, 245, 245, 196, 196, 196, 196])
        
        for player in range(198, 298):
            pt.addPlayer()
        self.failUnlessEqual(len(pt.getPrizes()), 40)
    # -------------------------------------------------------
    def test03_virtualBaseClass(self):
        """test03_virtualBaseClass
        Test minor things not elsewhere covered for the base class"""
        v = pokerprizes.PokerPrizes(5, player_count = 3, guarantee_amount = 100)
        self.assertEquals(v.buy_in, 5)
        self.assertEquals(v.player_count, 3)
        self.assertEquals(v.guarantee_amount, 100)

        clear_all_messages()

        exceptCaught = False
        try:
            v.getPrizes()
            self.failIf(True) # should not reach here
        except NotImplementedError, nie:
            exceptCaught = True
            self.assertEquals(nie.__str__(), 'getPrizes NOT IMPLEMENTED IN ABSTRACT BASE CLASS')
        self.failUnless(exceptCaught)
        self.assertEquals(get_messages(), ['getPrizes NOT IMPLEMENTED IN ABSTRACT BASE CLASS'])
# ---------------------------------------------------------
def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PokerPrizesTestCase))
    # Comment out above and use line below this when you wish to run just
    # one test by itself (changing prefix as needed).
#    suite.addTest(unittest.makeSuite(Breaks, prefix = "test2"))
    return suite
    
# ---------------------------------------------------------
def run():
    return unittest.TextTestRunner().run(GetTestSuite())
    
# ---------------------------------------------------------
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/test-pokerprizes.py ) ; ( cd ../tests ; make COVERAGE_FILES='../pokerengine/pokerprizes.py' TESTS='coverage-reset test-pokerprizes.py coverage-report' check )"
# End:
