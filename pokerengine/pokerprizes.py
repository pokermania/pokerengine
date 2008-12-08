#
# Copyright (C)             2008 Bradley M. Kuhn <bkuhn@ebb.org>
# Copyright (C) 2006, 2007, 2008 Loic Dachary <loic@dachary.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep <licensing@mekensleep.com>
#                                24 rue vieille du temple, 75004 Paris
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
#  Bradley M. Kuhn <bkuhn@ebb.org>
#  Loic Dachary <loic@gnu.org>
#
from pokerengine.pokerengineconfig import Config
############################################################################
class PokerPrizesFactory:
    """PokerPrizes is designed to handle payout strcutres for poker
    tournaments.  The Factory is used to generate different types of
    payout structure builds.

    The public interface usage looks something like this:
    
        prizes = pokerprizes.PokerPrizeFactory("Type")(buyInAmount = 100, playerCount = 5)
        prizes.addPlayer()
        prizeArray = prizes.getPrizes() 
        # returns an list where index+1 st place gets the price, prizeArray[index]"""

    def __init__(self, moduleStr = 'pokerprizes', classPrefix = "PokerPrizes", defaultClass = "PokerPrizesAlgorithm"):
        self.moduleStr = moduleStr
        self.classPrefix = classPrefix
        self.defaultClass = defaultClass
    # ----------------------------------------------------------------------
    def error(self, string):
        self.message("ERROR " + string)
    # ----------------------------------------------------------------------
    def message(self, string):
        print string
    # ----------------------------------------------------------------------
    def getClass(self, classname):
        classname = self.classPrefix + classname
        try:
            return getattr(__import__(self.moduleStr, globals(), locals(), [classname]), classname)
        except AttributeError, ae:
            self.error(ae.__str__())
        classname = self.defaultClass
        return getattr(__import__(self.moduleStr, globals(), locals(), [classname]), classname)
############################################################################
class PokerPrizes:
    """PokerPrizesVirtual base class for PokerPrizes"""
    def __init__(self, buyInAmount, playerCount = 0, guaranteeAmount = 0, configDirs = None):
        self.buy_in = buyInAmount
        self.player_count = playerCount
        self.guarantee_amount = guaranteeAmount
    # ----------------------------------------------------------------------
    def error(self, string):
        self.message("ERROR " + string)
    # ----------------------------------------------------------------------
    def message(self, string):
        print "[PokerPrizes] " + string
    # ----------------------------------------------------------------------
    def addPlayer(self):
        self.player_count += 1
    # ----------------------------------------------------------------------
    def removePlayer(self):
        self.player_count -= 1
    # ----------------------------------------------------------------------
    def getPrizes(self):
        errStr = "getPrizes NOT IMPLEMENTED IN ABSTRACT BASE CLASS"
        self.error(errStr)
        raise NotImplementedError(errStr)
############################################################################
class PokerPrizesAlgorithm(PokerPrizes):
    def getPrizes(self):
        buy_in = self.buy_in
        candidates_count = self.player_count 
        if candidates_count < 5:
            winners = 1
        elif candidates_count < 10:
            winners = 2
        elif candidates_count < 20:
            winners = 3
        elif candidates_count < 30:
            winners = 4
        elif candidates_count < 40:
            winners = 6
        elif candidates_count < 50:
            winners = int(candidates_count * 0.2)
        elif candidates_count < 200:
            winners = int(candidates_count * 0.15)
        else:
            winners = int(candidates_count * 0.1)

        prizes = []
        prize_pool = max(self.guarantee_amount, buy_in * candidates_count)
        money_left = prize_pool
        while winners > 0:
            if money_left / winners < max(1, prize_pool / 100, int(buy_in * 2.5)):
                prizes.extend([ money_left / winners ] * winners)
                winners = 0
            else:
                money_left /= 2
                winners -= 1
                prizes.append(money_left)
        rest = prize_pool - sum(prizes)
        prizes[0] += rest
        return prizes
############################################################################
class PokerPrizesTable(PokerPrizes):
    def __init__(self, buyInAmount, playerCount = 0, guaranteeAmount = 0, configDirs = ['.'],
                 configFileName = "poker.payouts.xml"):
        self._loadPayouts(configDirs)

        PokerPrizes.__init__(self, buyInAmount = buyInAmount, playerCount = playerCount,
                             guaranteeAmount = guaranteeAmount)
    # ----------------------------------------------------------------------
    def _loadPayouts(self, dirs):
        config = Config(dirs)
        config.load("poker.payouts.xml")
        self.payouts = []
        for node in config.header.xpathEval("/payouts/payout"):
            properties = config.headerNodeProperties(node)
            self.payouts.append(( int(properties['max']), map(lambda percent: float(percent) / 100, node.content.split())))
    # ----------------------------------------------------------------------
    def getPrizes(self):
        buy_in = self.buy_in
        for ( maximum, payouts ) in self.payouts:
            if self.player_count <= maximum:
                break

        total = max(self.guarantee_amount, self.player_count * buy_in)
        prizes = map(lambda percent: int(total * percent), payouts)
        #
        # What's left because of rounding errors goes to the tournament winner
        #
        prizes[0] += total - sum(prizes)
        return prizes
