#!/bin/bash

#
# cd to build.sh dir
cd $(dirname $0)

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
no_limit_levels 10-20-no-limit-lsng9 poker.levels-blinds-lsng9.xml 1000 6 minutes 5
no_limit_levels 15-30-no-limit-wfrmtt poker.levels-blinds-colin.xml 1500 10 minutes 5
no_limit_levels 15-30-no-limit-wsop poker.levels-blinds-colin.xml 1500 6 minutes 5
no_limit_levels 50-100-no-limit-deep-stack poker.levels-blinds-deep-stack.xml 10000 6 minutes 5

#
# no limit level ante
no_limit_levels_ante () {
    local name="$1" ; shift
    local levels_file="$1" ; shift
    local ante_levels_file="$1" ; shift
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
        -e "s/_ANTE_LEVEL_FILE_/$ante_levels_file/g" \
        -e "s/_BLIND_FREQUENCY_/$blind_frequency/g" \
        -e "s/_BLIND_UNIT_/$blind_frequency_unit/g" \
        -e "s/_ANTE_FREQUENCY_/$blind_frequency/g" \
        -e "s/_ANTE_UNIT_/$blind_frequency_unit/g" \
        -e "s/_UNIT_/$unit/g" \
        no-limit-levels-blind-ante.template > poker.level-${name}.xml
    echo poker.level-${name}.xml
}

no_limit_levels_ante 15-30-no-limit-ante poker.levels-blinds-colin.xml poker.levels-ante-colin.xml 1500 6 minutes 5
no_limit_levels_ante 15-30-no-limit-late-ante poker.levels-blinds-colin.xml poker.levels-late-ante.xml 1500 6 minutes 5


#
# pokermania
pokermania () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local buyin_min=$1 ; shift
    local buyin_max=$1 ; shift

    local buyin_best=$buyin_max
    local unit=1
    local cap=-1

    local name="${blind_small}-${blind_big}_${buyin_min}-${buyin_max}"
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
#           small    big   buyin buyin_max
pokermania      1      2      10       100
pokermania      2      4      10       100
pokermania      2      4     100       200
pokermania      5     10     200       500
pokermania      5     10     500      1000
pokermania     20     40    1000      2000
pokermania     20     40    2000      4000
pokermania     60    120    4000      6000
pokermania     60    120    6000      8000
pokermania    100    200    8000     10000
pokermania    100    200   10000     15000
pokermania    200    400   15000     20000
pokermania    200    400   20000     25000
pokermania    300    600   25000     30000
pokermania    300    600   30000     40000
pokermania    500   1000   40000     50000
pokermania    500   1000   50000    100000
pokermania   1500   3000  100000    150000
pokermania   1500   3000  150000    200000
pokermania   2500   5000  200000    250000
pokermania   2500   5000  250000    300000
pokermania   4000   8000  300000    400000
pokermania   4000   8000  400000    600000
pokermania   8000  16000  600000    800000
pokermania   8000  16000  800000   1000000
pokermania  15000  30000 1000000   1500000
pokermania  15000  30000 1500000   2000000
pokermania 100000 200000 6000000   8000000

#
# no-limit
no_limit () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*10]
    local buyin_best=$[$blind_big*50]
    local buyin_max=$[$blind_big*100]

    local name="${blind_small}-${blind_big}_${buyin_min}-${buyin_max}"
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
#        small big unit
no_limit     1   2    1
no_limit     2   4    1
no_limit     3   6    1
no_limit     5  10    5
no_limit    10  20   10
no_limit    30  60   10
no_limit    50 100   50
no_limit   100 200  100


#
# pot-limit
pot_limit () {
    local blind_small=$1 ; shift
    local blind_big=$1 ; shift
    local unit=$1 ; shift

    local buyin_min=$[$blind_big*10]
    local buyin_best=$[$blind_big*50]
    local buyin_max=$[$blind_big*100]

    local name="${blind_small}-${blind_big}_${buyin_min}-${buyin_max}"
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
#         small big unit
pot_limit     1   2    1
pot_limit     2   4    1
pot_limit     3   6    1
pot_limit     5  10    5
pot_limit    10  20   10
pot_limit    30  60   10
pot_limit    50 100   50
pot_limit   100 200  100

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

    local name="${blind_small}-${blind_big}_${buyin_min}-${buyin_max}"
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
#     small big unit
limit     1   2    1
limit     5  10    5
limit    15  30    5
limit    25  50    5
limit    50 100   50

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

    local name="${blind_small}-${blind_big}_${buyin_min}-${buyin_max}"
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
#          ante bringin small big unit
ante_limit    1       5    10  20    1
ante_limit    5      15    30  60    5

