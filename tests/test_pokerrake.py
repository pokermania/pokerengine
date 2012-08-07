# -*- coding: utf-8 -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2006 Mekensleep
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
#  Pierre-Andre (05/2006)
#  Loic Dachary <loic@dachary.org>
#

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

from pokerengine import pokerrake, pokergame

class PokerRakeTestCase(unittest.TestCase):
        
    # -----------------------------------------------------------------------------------------------------
    def setUp(self):
        pass
    
    # -----------------------------------------------------------------------------------------------------    
    def tearDown(self):
        pokerrake._get_rake_instance = None
        
    # -----------------------------------------------------------------------------------------------------    
    def test01_Init(self):
        """Test Poker rake : get_rake_instance"""
        game = pokergame.PokerGameClient("unittest.%s.xml", ['nodir'])
        rake = pokerrake.get_rake_instance(game)
        
    # -----------------------------------------------------------------------------------------------------    
    def test02_AlternatePokerRake(self):
        """Test Poker rake : get_rake_instance alternate PokerRake"""
        game = pokergame.PokerGameClient("unittest.%s.xml", ['nodir', path.join(TESTS_PATH, 'test-data')])
        rake = pokerrake.get_rake_instance(game)
        self.failUnless(hasattr(rake, 'gotcha'))
        
# -----------------------------------------------------------------------------------------------------
def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PokerRakeTestCase))
    # Comment out above and use line below this when you wish to run just
    # one test by itself (changing prefix as needed).
#    suite.addTest(unittest.makeSuite(PokerRakeTestCase, prefix = "test2"))
    return suite
    
# -----------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------
def run():
    try:
        import xmlrunner
        runner = xmlrunner.XMLTestRunner(output='build/tests')
    except ImportError:
        runner = unittest.TextTestRunner()
    return runner.run(GetTestSuite())
    
# -----------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/test-pokerrake.py ) ; ( cd ../tests ; make COVERAGE_FILES='../pokerengine/pokerrake.py' TESTS='coverage-reset test-pokerrake.py coverage-report' check )"
# End:
