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
#  Henry Precheur <henry@precheur.org>
#  Loic Dachary <loic@gnu.org>
#

from types import *

MAX_TOKENS_PER_STACK = 23
INT2CHIPS_FACTOR = 0.3

class PokerChips:

    def __init__(self, values, what = False):
        self.values = values
        self.size = len(self.values)
        if what == False:
            self.reset()
            return
        
        if type(what) is IntType or type(what) is LongType:
            self.chips = PokerChips.int2chips(values, INT2CHIPS_FACTOR, what)
            self.limitTokens()
        elif type(what) is ListType:
            self.chips = what[:]
            self.limitTokens()
        else:
            self.chips = what.chips[:]

    def __eq__(self, other):
        if type(other) is PokerChips:
            return self.chips == other.chips
        else:
            return False

    def __ne__(self, other):
        if type(other) is PokerChips:
            return self.chips != other.chips
        else:
            return True

    def __str__(self):
        return "PokerChips(%s) = %d" % (self.chips, self.toint())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.chips)

    def copy(self):
        return PokerChips(self.values, self)
    
    def reset(self):
        self.chips = [ 0 ] * self.size

    def set(self, chips):
        #
        # Must copy because if chips is a PokerChips object it
        # will be a reference to a chips data member used in another
        # object.
        #
        self.chips = PokerChips.convert(self.values, chips).chips[:]
        self.limitTokens()

    def convert(values, what):
        if type(what) is IntType or type(what) is LongType:
            what = PokerChips.int2chips(values, INT2CHIPS_FACTOR, what)
        if type(what) is ListType:
            return PokerChips(values, what)
        else:
            return what
        
    convert = staticmethod(convert)

    def add(self, other):
        other = PokerChips.convert(self.values, other)
        self.chips = [ self.chips[i] + other.chips[i] for i in xrange(self.size) ]
        self.limitTokens()

    def subtract(self, other):
        other = PokerChips.convert(self.values, other)
        chips = [ self.chips[i] - other.chips[i] for i in xrange(self.size) ]
        if len(filter(lambda x: x < 0, chips)) != 0:
            res = self.toint() - other.toint()
            if res < 0:
                self.reset()
            else:
                self.set(res)
        else:
            self.chips = chips

    def toint(self):
        return int(sum([ self.chips[i] * self.values[i] for i in xrange(self.size) ]))

    def int2chips(values, factor, money):
        
        chips = [0] * len(values)

        for i in range(len(values) - 1, -1, -1):
            if i == 0:
                to_distribute = money
            else:
                to_distribute = money - int(values[i] / factor)
            if to_distribute > 0:
                chips[i] = to_distribute / values[i]
                money -= to_distribute - to_distribute % values[i]

        if money:
            print "*CRITICAL* %d money was lost" % money
            
        return chips

    int2chips = staticmethod(int2chips)

    def limitTokens(self):
        def lcm(a, b):
            def gcm(x, y):
                if y == 0:
                    return x
                else:
                    return gcm(y, x % y)
            return (a * b) / gcm(a, b)
        for i in xrange(len(self.chips) - 1):
            if self.chips[i] > MAX_TOKENS_PER_STACK:
                _lcm = lcm(self.values[i], self.values[i + 1])
                too_many = ( self.chips[i] - MAX_TOKENS_PER_STACK ) * self.values[i]
                moving = too_many - too_many % _lcm
                if moving > 0:
                    self.chips[i] -= moving / self.values[i]
                    self.chips[i + 1] += moving / self.values[i + 1]
