# -*- coding: utf-8 -*-
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

import shutil, os
from pokerengine.pokerengineconfig import Config
from pokerengine.version import version

class TestUpgrades(unittest.TestCase):

    def test1(self):
        shutil.rmtree("conftest", ignore_errors = True)
        os.mkdir("conftest")
        os.system("%(cmd)s --upgrades=%(upgrades)s --reference=%(configs)s conftest" % {
            'cmd': path.join(TESTS_PATH, '../pokerconfigupgrade'),
            'upgrades': path.join(TESTS_PATH, '../upgrades'),
            'configs': path.join(TESTS_PATH, '../conf')
        })
        os.chmod("conftest", 0755)
        os.system("%(cmd)s --upgrades=%(upgrades)s conftest" % {
            'cmd': path.join(TESTS_PATH, '../pokerconfigupgrade'),
            'upgrades': path.join(TESTS_PATH, '../upgrades')
        })
        config = Config(['conftest'])
        for file in os.listdir("conftest"):
            if ".xml" in file:
                config.load(file)
                self.assertEqual(config.headerGet("/child::*/@poker_engine_version"), version)
        shutil.rmtree("conftest")

def GetTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUpgrades))
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
