#
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
#  Loic Dachary <loic@dachary.org>
#
from os import path
import imp

class PokerRake:
    def __init__(self, game):
        pass

    def getRake(self, pot, uncalled, is_tournament = False):
        """ implementation constraint of compute is as follows :
        for any game1.pot greater than game2.pot
        compute(game1.pot) MUST be greater or equal to compute(game2.pot) """
        return 0 \
            if is_tournament \
            else int((pot - uncalled) * .05)

_get_rake_instance = None

def get_rake_instance(game):
    global _get_rake_instance
    if _get_rake_instance == None:
        for dir in game.dirs:
            file = dir + "/pokerrake.py"
            if path.exists(file):
                game.log.debug("get_rake_instance: trying to load '%s'", file)
                module = imp.load_source("user_defined_pokerrake", file)
                get_instance = getattr(module, "get_rake_instance")
                _get_rake_instance = get_instance
                break
            else:
                game.log.inform("get_rake_instance: '%s' does not exist", file)
        if _get_rake_instance == None:
            game.log.inform("get_rake_instance: no pokerrake.py found in directories %s", str(game.dirs))
            _get_rake_instance = lambda game: PokerRake(game)
        else:
            game.log.inform("get_rake_instance: using custom implementation of get_rake_instance")
    return apply(_get_rake_instance, [game])
