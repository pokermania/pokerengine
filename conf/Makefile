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
#  Loic Dachary <loic@gnu.org>
#
# 

buildconf:
	( \
		echo '10-20-no-limit-lsng9 100000 poker.levels-blinds-lsng9.xml 6 minutes 500'; \
		echo '15-30-no-limit-wfrmtt 150000 poker.levels-blinds-colin.xml 10 minutes 500'; \
		echo '15-30-no-limit-wsop 150000 poker.levels-blinds-colin.xml 6 minutes 500'; \
	) | while read name buy_in blind_level_file blind_frequency blind_unit unit ; do \
		sed -e "s;_NAME_;$$name;g" -e "s;_BUY_IN_;$$buy_in;g" -e "s/_BLIND_LEVEL_FILE_/$$blind_level_file/g" -e "s/_BLIND_FREQUENCY_/$$blind_frequency/g" -e "s/_BLIND_UNIT_/$$blind_unit/g" -e "s/_UNIT_/$$unit/g" < no-limit-levels-blind.template > poker.level-$${name}.xml ; \
	done
	( \
		echo '1-2_10-100_1000 1-2_10-100_1000 100 200 1000 10000 -1 100'; \
		echo '2-4_10-100_1000 2-4_10-100_1000 200 400 1000 10000 -1 100'; \
		echo '2-4_100-200_2000 2-4_100-200_2000 200 400 10000 20000 -1 100'; \
		echo '5-10_200-500_5000 5-10_200-500_5000 500 1000 20000 50000 -1 100'; \
		echo '5-10_500-1000_10000 5-10_500-1000_10000 500 1000 50000 100000 -1 100'; \
		echo '20-40_1000-2000_20000 20-40_1000-2000_20000 2000 4000 100000 200000 -1 100'; \
		echo '20-40_2000-4000_40000 20-40_2000-4000_40000 2000 4000 200000 400000 -1 100'; \
		echo '60-120_4000-6000_60000 60-120_4000-6000_60000 6000 12000 400000 600000 -1 100'; \
		echo '60-120_6000-8000_80000 60-120_6000-8000_80000 6000 12000 600000 800000 -1 100'; \
		echo '100-200_8000-10000_100000 100-200_8000-10000_100000 10000 20000 800000 1000000 -1 100'; \
		echo '100-200_10000-15000_150000 100-200_10000-15000_150000 10000 20000 1000000 1500000 -1 100'; \
		echo '200-400_15000-20000_200000 200-400_15000-20000_200000 20000 40000 1500000 2000000 -1 100'; \
		echo '200-400_20000-25000_250000 200-400_20000-25000_250000 20000 40000 2000000 2500000 -1 100'; \
		echo '300-600_25000-30000_300000 300-600_25000-30000_300000 30000 60000 2500000 3000000 -1 100'; \
		echo '300-600_30000-40000_400000 300-600_30000-40000_400000 30000 60000 3000000 4000000 -1 100'; \
		echo '500-1000_40000-50000_500000 500-1000_40000-50000_500000 50000 100000 4000000 5000000 -1 100'; \
		echo '500-1000_50000-100000_1000000 500-1000_50000-100000_1000000 50000 100000 5000000 10000000 -1 100'; \
		echo '1500-3000_100000-150000_1500000 1500-3000_100000-150000_1500000 150000 300000 10000000 15000000 -1 100'; \
		echo '1500-3000_150000-200000_2000000 1500-3000_150000-200000_2000000 150000 300000 15000000 20000000 -1 100'; \
		echo '2500-5000_200000-250000_2500000 2500-5000_200000-250000_2500000 250000 500000 20000000 25000000 -1 100'; \
		echo '2500-5000_250000-300000_3000000 2500-5000_250000-300000_3000000 250000 500000 25000000 30000000 -1 100'; \
		echo '4000-8000_300000-400000_4000000 4000-8000_300000-400000_4000000 400000 800000 30000000 40000000 -1 100'; \
		echo '4000-8000_400000-600000_6000000 4000-8000_400000-600000_6000000 400000 800000 40000000 60000000 -1 100'; \
		echo '8000-16000_600000-800000_8000000 8000-16000_600000-800000_8000000 800000 1600000 60000000 80000000 -1 100'; \
		echo '8000-16000_800000-1000000_10000000 8000-16000_800000-1000000_10000000 800000 1600000 80000000 100000000 -1 100'; \
		echo '15000-30000_1000000-1500000_15000000 15000-30000_1000000-1500000_15000000 1500000 3000000 100000000 150000000 -1 100'; \
		echo '15000-30000_1500000-2000000_20000000 15000-30000_1500000-2000000_20000000 1500000 3000000 150000000 200000000 -1 100'; \
	) | while read name desc small big buy_in max_buy_in cap unit ; do \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$max_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" -e "s/_CAP_/$$cap/g" < pokermania.template > poker.$${name}-pokermania.xml ; \
	done
	( \
		echo '.01-.02 .01/.02 1 2 1' ; \
		echo '.02-.04 .02/.04 2 4 2' ; \
		echo '.05-.10 .05/.10 5 10 5' ; \
		echo '.10-.25 .10/.25 12 25 1' ; \
		echo '.25-.50 .25/.50 25 50 5' ; \
		echo '.50-1 .50/1 50 100 50' ; \
		echo '1-2 1/2 100 200 100' ; \
		echo '2-4 2/4 200 400 100' ; \
		echo '3-6 3/6 300 600 100' ; \
		echo '5-10 5/10 500 1000 500' ; \
		echo '10-20 10/20 1000 2000 1000' ; \
		echo '30-60 30/60 3000 6000 1000' ; \
		echo '50-100 50/100 5000 10000 5000' ; \
		echo '100-200 100/200 10000 20000 10000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 10` ; \
		best_buy_in=`expr $$big \* 50` ; \
		max_buy_in=`expr $$big \* 100` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" < no-limit.template > poker.$${name}-no-limit.xml ; \
	done
	( \
		echo '.01-.02 .01/.02 1 2 1' ; \
		echo '.02-.04 .02/.04 2 4 2' ; \
		echo '.05-.10 .05/.10 5 10 5' ; \
		echo '.10-.25 .10/.25 12 25 1' ; \
		echo '.25-.50 .25/.50 25 50 5' ; \
		echo '.50-1 .50/1 50 100 50' ; \
		echo '1-2 1/2 100 200 100' ; \
		echo '2-4 2/4 200 400 100' ; \
		echo '3-6 3/6 300 600 100' ; \
		echo '5-10 5/10 500 1000 500' ; \
		echo '10-20 10/20 1000 2000 1000' ; \
		echo '30-60 30/60 3000 6000 1000' ; \
		echo '50-100 50/100 5000 10000 5000' ; \
		echo '100-200 100/200 10000 20000 10000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 10` ; \
		best_buy_in=`expr $$big \* 50` ; \
		max_buy_in=`expr $$big \* 100` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" < pot-limit.template > poker.$${name}-pot-limit.xml ; \
	done
	( \
		echo '.02-.04 .02/.04 1 2 1' ; \
		echo '.05-.10 .05/.10 2 5 1' ; \
		echo '.10-.25 .10/.25 5 10 5' ; \
		echo '.25-.50 .25/.50 12 25 1' ; \
		echo '.50-1 .50/1 25 50 5' ; \
		echo '1-2 1/2 50 100 50' ; \
		echo '2-4 2/4 100 200 100' ; \
		echo '3-6 3/6 150 300 50' ; \
		echo '5-10 5/10 250 500 50' ; \
		echo '10-20 10/20 500 1000 500' ; \
		echo '30-60 30/60 1500 3000 500' ; \
		echo '50-100 50/100 2500 5000 500' ; \
		echo '100-200 100/200 5000 10000 5000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 5` ; \
		best_buy_in=`expr $$big \* 30` ; \
		max_buy_in=`expr $$big \* 100000` ; \
		big_bet=`expr $$big \* 2` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" -e "s/_BIGBET_/$$big_bet/g" < limit.template > poker.$${name}-limit.xml ; \
	done
	( \
		echo '.04-.08 .04/.08 4 8 1 2 1' ; \
		echo '.10-.20 .10/.20 10 20 2 5 2' ; \
		echo '.25-.50 .25/.50 25 50 5 10 5' ; \
		echo '.50-1 .50/1 50 100 5 25 5' ; \
		echo '1-2 1/2 100 200 10 50 10' ; \
		echo '2-4 2/4 200 400 25 100 25' ; \
		echo '3-6 3/6 300 600 25 150 25' ; \
		echo '5-10 5/10 500 1000 50 200 50' ; \
		echo '10-20 10/20 1000 2000 100 500 100' ; \
		echo '30-60 30/60 3000 6000 500 1500 500' ; \
	) | while read name desc small big ante bringin unit ; do \
		buy_in=`expr $$big \* 5` ; \
		best_buy_in=`expr $$big \* 30` ; \
		max_buy_in=`expr $$big \* 100000` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" -e "s/_ANTE_/$$ante/g" -e "s/_BRINGIN_/$$bringin/g" < ante-limit.template > poker.ante-$${name}-limit.xml ; \
	done

