#!/usr/bin/env python
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

from pokerengine import version

class VersionTestCase(unittest.TestCase):
    
    # -----------------------------------------------------------------------------------------------------
    def setUp(self):
        pass
    
    # -----------------------------------------------------------------------------------------------------    
    def tearDown(self):
        pass
        
    # -----------------------------------------------------------------------------------------------------
    def testStringRepresentation(self):
        """Test Version : String representation of the version object"""
        
        ver = version.Version('1.2.3')
        self.failUnlessEqual(repr(ver),ver.__class__.__name__ + ' (\'' + str(ver) + '\')')
        
    # -----------------------------------------------------------------------------------------------------
    def testParseError(self):
        """Test Version : Parsing error with invalid version string"""
        
        ver = version.Version()
        self.failUnlessRaises(ValueError,ver.parse,'')
        self.failUnlessRaises(ValueError,ver.parse,'1')
        self.failUnlessRaises(ValueError,ver.parse,'1.2')
        self.failUnlessRaises(ValueError,ver.parse,'1-2-3')
        self.failUnlessRaises(ValueError,ver.parse,'A.B.C')
        self.failUnlessRaises(ValueError,ver.parse,'1.2.3.')
        self.failUnlessRaises(ValueError,ver.parse,'1.2.3.4')
        
    # -----------------------------------------------------------------------------------------------------
    def testParseSuccess(self):
        """Test Version : Parsing success with valid version string"""
        
        ver = version.Version()
        try:
            ver.parse('1.2.3')
            major, medium, minor = ver.version
        except:
            self.fail('Exception generated version parsing')
            
        self.failUnlessEqual(major,1)
        self.failUnlessEqual(medium,2)
        self.failUnlessEqual(minor,3)
        
    # -----------------------------------------------------------------------------------------------------
    def testMajor(self):
        """Test Version : Major version number accessor"""
        
        ver = version.Version('1.2.3')
        self.failUnlessEqual(ver.major(),1)
        
    # -----------------------------------------------------------------------------------------------------
    def testMedium(self):
        """Test Version : Medium version number accessor"""
        
        ver = version.Version('1.2.3')
        self.failUnlessEqual(ver.medium(),2)
        
    # -----------------------------------------------------------------------------------------------------
    def testMinor(self):
        """Test Version : Minor version number accessor"""
        
        ver = version.Version('1.2.3')
        self.failUnlessEqual(ver.minor(),3)
        
    # -----------------------------------------------------------------------------------------------------
    def testStr(self):
        """Test Version : String representation"""
        
        sver = '1.2.3'
        ver = version.Version('1.2.3')
        self.failUnlessEqual(sver,str(ver))
        
    # -----------------------------------------------------------------------------------------------------
    def testAdd(self):
        """Test Version : Addition"""
        
        ver1 = version.Version('1.2.3')
        ver2 = ver1 + 1
        self.failUnlessEqual(version.Version('1.2.3'),ver1)        
        self.failUnlessEqual(version.Version('1.2.4'),ver2)
        
    # -----------------------------------------------------------------------------------------------------
    def testIAdd(self):
        """Test Version : Self addition"""
        
        ver1 = version.Version('1.2.3')
        ver1 += 1
        self.failUnlessEqual(version.Version('1.2.4'),ver1)
        
    # -----------------------------------------------------------------------------------------------------
    def testSub(self):
        """Test Version : Substraction"""
        
        ver1 = version.Version('3.2.1')
        ver2 = ver1 - 1
        self.failUnlessEqual(version.Version('3.2.1'),ver1)
        self.failUnlessEqual(version.Version('3.2.0'),ver2)
        
        ver2 = ver1 - 2
        self.failUnlessEqual(version.Version('3.2.1'),ver1)
        self.failUnlessEqual(version.Version('3.0.1'),ver2)
        
        ver2 = ver1 - 3
        self.failUnlessEqual(version.Version('3.2.1'),ver1)
        self.failUnlessEqual(version.Version('0.2.1'),ver2)
        
        self.failUnlessRaises(UserWarning,ver1.__sub__,4)
        
    # -----------------------------------------------------------------------------------------------------
    def testISub(self):
        """Test Version : Self substraction"""
        
        ver1 = version.Version('3.2.1')
        ver1 -= 1
        self.failUnlessEqual(version.Version('3.2.0'),ver1)
        
        ver1 = version.Version('3.2.1')
        ver1 -= 2
        self.failUnlessEqual(version.Version('3.0.1'),ver1)
        
        ver1 = version.Version('3.2.1')
        ver1 -= 3
        self.failUnlessEqual(version.Version('0.2.1'),ver1)
        
        ver1 = version.Version('3.2.1')
        self.failUnlessRaises(UserWarning,ver1.__sub__,4)
        
    # -----------------------------------------------------------------------------------------------------
    def testUpgradeChainInvalid(self):      
        """Test Version : Upgrade chain with invalid input formats"""
        
        ver_invalid = ['','1.2','1-2-3','A.B.C','1.2.3.','1.2.3.4']
        
        chain_invalid = []
        for ver1 in ver_invalid:
            for ver2 in ver_invalid:
                chain_invalid.append('upgrade-' + ver1 + '-' + ver2)
        chain_invalid.append('upgrade-1.2.3-1.2.')
        chain_invalid.append('upgrade-1.2.-1.2.3')
        chain_invalid.append('upgrade-1.2.3,1.2.4')
                
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('4.3.2',chain_invalid),[])
        
    # -----------------------------------------------------------------------------------------------------
    def testUpgradeChainFailed(self):      
        """Test Version : Upgrade chain with invalid inputs"""
        
        ver_invalid = ['upgrade-3.2.1-3.2.1','upgrade-3.2.1-3.2.0']
        
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('3.2.2',ver_invalid),[])
        
    # -----------------------------------------------------------------------------------------------------
    def testUpgradeChainIgnored(self):      
        """Test Version : Upgrade chain with ignored inputs"""
        
        ver_ignored = ['upgrade-0.9.0-1.0.0','upgrade-3.0.0-3.1.0']
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('3.2.3',ver_ignored),[])
        
    # -----------------------------------------------------------------------------------------------------
    def testUpgradeChainValid(self):      
        """Test Version : Upgrade chain with valid inputs"""
        
        ver_valid = ['upgrade-3.2.1-3.2.2','grade-3.2.2-3.2.3']
        
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('3.2.3',ver_valid),ver_valid)
        
        ver_valid = ['upgrade-3.2.2-3.2.3', 'upgrade-3.2.2-3.2.3']
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('3.2.3',ver_valid), ['upgrade-3.2.2-3.2.3'])
        
        ver_valid = ['upgrade-3.2.1-3.2.6', 'upgrade-3.2.1-3.2.3']
        ver = version.Version('3.2.1')
        self.failUnlessEqual(ver.upgradeChain('3.2.7',ver_valid), ['upgrade-3.2.1-3.2.6'])
        
# -----------------------------------------------------------------------------------------------------
def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VersionTestCase))
    # Comment out above and use line below this when you wish to run just
    # one test by itself (changing prefix as needed).
#    suite.addTest(unittest.makeSuite(VersionTestCase, prefix = "test2"))
    return suite
    
# -----------------------------------------------------------------------------------------------------
def GetTestedModule():
    return version
  
# -----------------------------------------------------------------------------------------------------
def run():
    return unittest.TextTestRunner().run(GetTestSuite())
    
# -----------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    if run().wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

# Interpreted by emacs
# Local Variables:
# compile-command: "( cd .. ; ./config.status tests/test-version.py ) ; ( cd ../tests ; make COVERAGE_FILES='../pokerengine/version.py' TESTS='coverage-reset test-version.py coverage-report' check )"
# End:
