#!/bin/bash

#
# cd to build.sh dir
cd $(dirname $0)

#
# /100
bc100() {
    echo $1\*0.01 | bc -q | sed -e's/^.00$/0/' -e 's/\.00$//'
}

#
# no limit level
no_limit_levels () {
    local name="$1" ; shift
    local levels_file="$1" ; shift
    local buyin_min=$1 ; shift
    local buyin_max=$(((buyin_min*2)-1));
    local blind_frequency=$1 ; shift
    local blind_frequency_unit="$1" ; shift
    local unit=$1 ; shift

    sed \
        -e "s;_NAME_;$name;g" \
        -e "s;_MAX_BUY_IN_;$buyin_max;g" \
        -e "s;_BUY_IN_;$buyin_min;g" \
        -e "s/_BLIND_LEVEL_FILE_/$levels_file/g" \
        -e "s/_BLIND_FREQUENCY_/$blind_frequency/g" \
        -e "s/_BLIND_UNIT_/$blind_frequency_unit/g" \
        -e "s/_UNIT_/$unit/g" \
        no-limit-levels-blind.template > poker.level-${name}.xml
    echo poker.level-${name}.xml
}   
#   
no_limit_levels 10-20-no-limit-lsng9 poker.levels-blinds-lsng9.xml 100000 6 minutes 500
no_limit_levels 15-30-no-limit-wfrmtt poker.levels-blinds-colin.xml 150000 10 minutes 500
no_limit_levels 15-30-no-limit-wsop poker.levels-blinds-colin.xml 150000 6 minutes 500

#
# pokermania
pokermania () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local buyin_min=$1 ; shift
    local buyin_max=$1 ; shift

    local buyin_best=$buyin_max
    local unit=100
    local cap=-1

    local name="$(bc100 $blind_small)-$(bc100 $blind_big)_$(bc100 $buyin_min)-$(bc100 $buyin_max)"
    local desc="$name"

    sed \
        -e "s/_NAME_/$name/" \
        -e "s/_DESC_/$desc/" \
        -e "s/_UNIT_/$unit/" \
        -e "s/_BEST_BUY_IN_/$buyin_best/" \
        -e "s/_MAX_BUY_IN_/$buyin_max/" \
        -e "s/_BUY_IN_/$buyin_min/" \
        -e "s/_SMALL_/$blind_small/" \
        -e "s/_BIG_/$blind_big/" \
        -e "s/_CAP_/$cap/" \
        pokermania.template > poker.${name}_pokermania.xml
    echo poker.${name}_pokermania.xml
}
#            small     big     buyin buyin_max
pokermania     100     200      1000     10000
pokermania     200     400      1000     10000
pokermania     200     400     10000     20000
pokermania     500    1000     20000     50000
pokermania     500    1000     50000    100000
pokermania    2000    4000    100000    200000
pokermania    2000    4000    200000    400000
pokermania    6000   12000    400000    600000
pokermania    6000   12000    600000    800000
pokermania   10000   20000    800000   1000000
pokermania   10000   20000   1000000   1500000
pokermania   20000   40000   1500000   2000000
pokermania   20000   40000   2000000   2500000
pokermania   30000   60000   2500000   3000000
pokermania   30000   60000   3000000   4000000
pokermania   50000  100000   4000000   5000000
pokermania   50000  100000   5000000  10000000
pokermania  150000  300000  10000000  15000000
pokermania  150000  300000  15000000  20000000
pokermania  250000  500000  20000000  25000000
pokermania  250000  500000  25000000  30000000
pokermania  400000  800000  30000000  40000000
pokermania  400000  800000  40000000  60000000
pokermania  800000 1600000  60000000  80000000
pokermania  800000 1600000  80000000 100000000
pokermania 1500000 3000000 100000000 150000000
pokermania 1500000 3000000 150000000 200000000

#
# no-limit
no_limit () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*10]
    local buyin_best=$[$blind_big*50]
    local buyin_max=$[$blind_big*100]

    local name="$(bc100 $blind_small)-$(bc100 $blind_big)_$(bc100 $buyin_min)-$(bc100 $buyin_max)"
    local desc="$name"
    sed \
        -e "s/_NAME_/$name/" \
        -e "s/_DESC_/$desc/" \
        -e "s/_UNIT_/$unit/" \
        -e "s/_BEST_BUY_IN_/$buyin_best/" \
        -e "s/_MAX_BUY_IN_/$buyin_max/" \
        -e "s/_BUY_IN_/$buyin_min/" \
        -e "s/_SMALL_/$blind_small/" \
        -e "s/_BIG_/$blind_big/" \
        no-limit.template > poker.${name}_no-limit.xml
    echo poker.${name}_no-limit.xml
}
#        small   big  unit
no_limit     1     2     1
no_limit     2     4     2
no_limit     5    10     5
no_limit    12    25     1
no_limit    25    50     5
no_limit    50   100    50
no_limit   100   200   100
no_limit   200   400   100
no_limit   300   600   100
no_limit   500  1000   500
no_limit  1000  2000  1000
no_limit  3000  6000  1000
no_limit  5000 10000  5000
no_limit 10000 20000 10000


#
# pot-limit
pot_limit () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*10]
    local buyin_best=$[$blind_big*50]
    local buyin_max=$[$blind_big*100]

    local name="$(bc100 $blind_small)-$(bc100 $blind_big)_$(bc100 $buyin_min)-$(bc100 $buyin_max)"
    local desc="$name"
    sed \
        -e "s/_NAME_/$name/" \
        -e "s/_DESC_/$desc/" \
        -e "s/_UNIT_/$unit/" \
        -e "s/_BEST_BUY_IN_/$buyin_best/" \
        -e "s/_MAX_BUY_IN_/$buyin_max/" \
        -e "s/_BUY_IN_/$buyin_min/" \
        -e "s/_SMALL_/$blind_small/" \
        -e "s/_BIG_/$blind_big/" \
        pot-limit.template > poker.${name}_pot-limit.xml
    echo poker.${name}_pot-limit.xml
}
#         small   big  unit
pot_limit     1     2     1
pot_limit     2     4     2
pot_limit     5    10     5
pot_limit    12    25     1
pot_limit    25    50     5
pot_limit    50   100    50
pot_limit   100   200   100
pot_limit   200   400   100
pot_limit   300   600   100
pot_limit   500  1000   500
pot_limit  1000  2000  1000
pot_limit  3000  6000  1000
pot_limit  5000 10000  5000
pot_limit 10000 20000 10000

#
# limit
limit () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*10]
    local buyin_best=$[$blind_big*50]
    local buyin_max=$[$blind_big*100]
    local big_bet=$[$blind_big*2]

    local name="$(bc100 $blind_small)-$(bc100 $blind_big)_$(bc100 $buyin_min)-$(bc100 $buyin_max)"
    local desc="$name"
    sed \
        -e "s/_NAME_/$name/" \
        -e "s/_DESC_/$desc/" \
        -e "s/_UNIT_/$unit/" \
        -e "s/_BEST_BUY_IN_/$buyin_best/" \
        -e "s/_MAX_BUY_IN_/$buyin_max/" \
        -e "s/_BUY_IN_/$buyin_min/" \
        -e "s/_SMALL_/$blind_small/" \
        -e "s/_BIG_/$blind_big/" \
        -e "s/_BIGBET_/$big_bet/" \
        limit.template > poker.${name}_limit.xml
    echo poker.${name}_limit.xml
}
#     small   big unit
limit     1     2    1
limit     2     5    1
limit     5    10    5
limit    12    25    1
limit    25    50    5
limit    50   100   50
limit   100   200  100
limit   150   300   50
limit   250   500   50
limit   500  1000  500
limit  1500  3000  500
limit  2500  5000  500
limit  5000 10000 5000

#
# no blinds no ante limit
sed \
    -e "s/_NAME_/0-0_50-5000/" \
    -e "s/_DESC_/No blind, no antes/" \
    -e "s/_UNIT_/100/" \
    -e "s/_BEST_BUY_IN_/5000/" \
    -e "s/_MAX_BUY_IN_/500000/" \
    -e "s/_BUY_IN_/500000/" \
    -e "s/_SMALL_/0/" \
    -e "s/_BIG_/0/" \
    limit.template > poker.0-0_50-5000_limit.xml
echo poker.0-0_50-5000_limit.xml


#
# ante-limit
ante_limit () {
    local ante=$1 ; shift
    local bringin=$1 ; shift
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*5]
    local buyin_best=$[$blind_big*30]
    local buyin_max=$[$blind_big*100000]

    local name="$(bc100 $blind_small)-$(bc100 $blind_big)_$(bc100 $buyin_min)-$(bc100 $buyin_max)"
    local desc="$name"
    sed \
        -e "s/_NAME_/$name/" \
        -e "s/_DESC_/$desc/" \
        -e "s/_UNIT_/$unit/" \
        -e "s/_BEST_BUY_IN_/$buyin_best/" \
        -e "s/_MAX_BUY_IN_/$buyin_max/" \
        -e "s/_BUY_IN_/$buyin_min/" \
        -e "s/_SMALL_/$blind_small/" \
        -e "s/_BIG_/$blind_big/" \
        -e "s/_ANTE_/$ante/" \
        -e "s/_BRINGIN_/$bringin/" \
        ante-limit.template > poker.${name}_ante-limit.xml
    echo poker.${name}_ante-limit.xml
}
#          ante bringin small  big unit
ante_limit    1       2     4    8    1
ante_limit    2       5    10   20    2
ante_limit    5      10    25   50    5
ante_limit    5      25    50  100    5
ante_limit   10      50   100  200   10
ante_limit   25     100   200  400   25
ante_limit   25     150   300  600   25
ante_limit   50     200   500 1000   50
ante_limit  100     500  1000 2000  100
ante_limit  500    1500  3000 6000  500

