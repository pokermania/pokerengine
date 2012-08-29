# -*- coding: utf-8 -*-
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2008 Bradley M. Kuhn <bkuhn@ebb.org>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#   Jerome Jeannin <griim.work@gmail.com>
#   Bradley M. Kuhn <bkuhn@ebb.org>

import unittest, sys
from os import path

TESTS_PATH = path.dirname(path.realpath(__file__))
sys.path.insert(0, path.join(TESTS_PATH, ".."))

from pokerengine import pokergame

#---------------------------
class FakePlatform:

  def __init__(self, system):
    self._system = system

  def system(self):
    return self._system

class FakeLocale:

  def __init__(self, lang):
    self._lang = lang

  def getdefaultlocale(self):
    return (self._lang, None)

# ---------------------------------------------------------    
class PokerI18NTest(unittest.TestCase):
         
    # ---------------------------------------------------------    
    def testTranslationFails(self):
        """Test I18N : domains/lang fails"""

        # When we do the init, we've already set it to an _() that returns
        # text.
        self.assertEquals(pokergame.init_i18n(None)("ANYTHING"), "ANYTHING")
        self.failUnlessEqual(pokergame._("Ace"), "Ace")
        
    # ---------------------------------------------------------    
    def testWindowsFails(self):
        """Test I18N : windows fails"""

        old_platform, pokergame.platform = pokergame.platform, FakePlatform("Windows")
        old_locale, pokergame.locale = pokergame.locale, FakeLocale("de")
        pokergame.init_i18n(None)
        self.failUnlessEqual(pokergame._("King"), "King")
        pokergame.platform = old_platform
        pokergame.locale = old_locale
        pokergame.init_i18n(None)

    # ---------------------------------------------------------    
    def testWindowsSuccess(self):
        """Test I18N : windows success"""

        old_platform, pokergame.platform = pokergame.platform, FakePlatform("Windows")
        old_locale, pokergame.locale = pokergame.locale, FakeLocale("de")
        pokergame.init_i18n(path.join(TESTS_PATH, "../locale"))
        self.failUnlessEqual(pokergame._("King"), u"König".encode('utf8'))
        pokergame.platform = old_platform
        pokergame.locale = old_locale
        pokergame.init_i18n(None)

    # ---------------------------------------------------------    
    def testUserWrittenTranslationFunction(self):
        """Test I18N : user written translation function"""
        self.assertEquals(
            pokergame.init_i18n(None, lambda text : "All your string are translated to us.")("DUMMY TEXT RETURN"),
            "DUMMY TEXT RETURN"
        )
        self.failUnlessEqual(pokergame._("Ace"), "All your string are translated to us.")
# ---------------------------------------------------------

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PokerI18NTest))
    return suite

def run():
    try:
        import xmlrunner
        runner = xmlrunner.XMLTestRunner(output='build/tests')
    except ImportError:
        runner = unittest.TextTestRunner()
    return runner.run(GetTestSuite())
    
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
