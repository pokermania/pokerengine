#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import basename
from glob import glob
from distutils.core import setup

from distutils.command.build import build as DistutilsBuild

class ExtendedBuild(DistutilsBuild):
    
    def run(self):
        os.system("make -C po")
        os.system("bash conf/build.sh")
        DistutilsBuild.run(self)

from pprint import pprint as pp

setup(
    name='poker-engine',
    version='1.5.4',
    packages=['pokerengine'],
    data_files=[
        ('bin', ['pokerconfigupgrade']),
        ('share/poker-engine/conf', [
            'conf/poker.0-0_50-5000_limit.xml',
            'conf/poker.0-0-limit.xml',
            'conf/poker..01-.02_.20-2_limit.xml',
            'conf/poker..01-.02_.20-2_no-limit.xml',
            'conf/poker..01-.02_.20-2_pot-limit.xml',
            'conf/poker..02-.04_.40-4_no-limit.xml',
            'conf/poker..02-.04_.40-4_pot-limit.xml',
            'conf/poker..02-.05_.50-5_limit.xml',
            'conf/poker..04-.08_.40-8000_ante-limit.xml',
            'conf/poker..05-.10_1-10_limit.xml',
            'conf/poker..05-.10_1-10_no-limit.xml',
            'conf/poker..05-.10_1-10_pot-limit.xml',
            'conf/poker.100-200_10000-15000_pokermania.xml',
            'conf/poker.100-200_2000-20000_no-limit.xml',
            'conf/poker.100-200_2000-20000_pot-limit.xml',
            'conf/poker.100-200_8000-10000_pokermania.xml',
            'conf/poker.10-20_100-2000000_ante-limit.xml',
            'conf/poker..10-.20_1-20000_ante-limit.xml',
            'conf/poker.10-20_200-2000_no-limit.xml',
            'conf/poker.10-20_200-2000_pot-limit.xml',
            'conf/poker.1-2_10-100_pokermania.xml',
            'conf/poker.1-2_10-200000_ante-limit.xml',
            'conf/poker.1-2_20-200_limit.xml',
            'conf/poker.1-2_20-200_no-limit.xml',
            'conf/poker.1-2_20-200_pot-limit.xml',
            'conf/poker..12-.25_2.50-25_limit.xml',
            'conf/poker..12-.25_2.50-25_no-limit.xml',
            'conf/poker..12-.25_2.50-25_pot-limit.xml',
            'conf/poker.15000-30000_1000000-1500000_pokermania.xml',
            'conf/poker.15000-30000_1500000-2000000_pokermania.xml',
            'conf/poker.1500-3000_100000-150000_pokermania.xml',
            'conf/poker.1500-3000_150000-200000_pokermania.xml',
            'conf/poker.1.50-3_30-300_limit.xml',
            'conf/poker.15-30_300-3000_limit.xml',
            'conf/poker.200-400_15000-20000_pokermania.xml',
            'conf/poker.200-400_20000-25000_pokermania.xml',
            'conf/poker.20-40_1000-2000_pokermania.xml',
            'conf/poker.20-40_2000-4000_pokermania.xml',
            'conf/poker.2-4_100-200_pokermania.xml',
            'conf/poker.2-4_10-100_pokermania.xml',
            'conf/poker.2-4_20-400000_ante-limit.xml',
            'conf/poker.2-4_40-400_no-limit.xml',
            'conf/poker.2-4_40-400_pot-limit.xml',
            'conf/poker.2500-5000_200000-250000_pokermania.xml',
            'conf/poker.2500-5000_250000-300000_pokermania.xml',
            'conf/poker.2.50-5_50-500_limit.xml',
            'conf/poker..25-.50_2.50-50000_ante-limit.xml',
            'conf/poker.25-50_500-5000_limit.xml',
            'conf/poker..25-.50_5-50_limit.xml',
            'conf/poker..25-.50_5-50_no-limit.xml',
            'conf/poker..25-.50_5-50_pot-limit.xml',
            'conf/poker.300-600_25000-30000_pokermania.xml',
            'conf/poker.300-600_30000-40000_pokermania.xml',
            'conf/poker.30-60_300-6000000_ante-limit.xml',
            'conf/poker.30-60_600-6000_no-limit.xml',
            'conf/poker.30-60_600-6000_pot-limit.xml',
            'conf/poker.3-6_30-600000_ante-limit.xml',
            'conf/poker.3-6_60-600_no-limit.xml',
            'conf/poker.3-6_60-600_pot-limit.xml',
            'conf/poker.4000-8000_300000-400000_pokermania.xml',
            'conf/poker.4000-8000_400000-600000_pokermania.xml',
            'conf/poker.500-1000_40000-50000_pokermania.xml',
            'conf/poker.500-1000_50000-100000_pokermania.xml',
            'conf/poker.50-100_1000-10000_limit.xml',
            'conf/poker.50-100_1000-10000_no-limit.xml',
            'conf/poker.50-100_1000-10000_pot-limit.xml',
            'conf/poker..50-1_10-100_limit.xml',
            'conf/poker..50-1_10-100_no-limit.xml',
            'conf/poker..50-1_10-100_pot-limit.xml',
            'conf/poker..50-1_5-100000_ante-limit.xml',
            'conf/poker.5-10_100-1000_limit.xml',
            'conf/poker.5-10_100-1000_no-limit.xml',
            'conf/poker.5-10_100-1000_pot-limit.xml',
            'conf/poker.5-10_200-500_pokermania.xml',
            'conf/poker.5-10_500-1000_pokermania.xml',
            'conf/poker.5-10_50-1000000_ante-limit.xml',
            'conf/poker.60-120_4000-6000_pokermania.xml',
            'conf/poker.60-120_6000-8000_pokermania.xml',
            'conf/poker.7stud.xml',
            'conf/poker.8000-16000_600000-800000_pokermania.xml',
            'conf/poker.8000-16000_800000-1000000_pokermania.xml',
            'conf/poker.holdem.xml',
            'conf/poker.level-001.xml',
            'conf/poker.level-10-15-pot-limit.xml',
            'conf/poker.level-10-20-no-limit-lsng9.xml',
            'conf/poker.level-10-20-no-limit.xml',
            'conf/poker.level-15-30-no-limit-wfrmtt.xml',
            'conf/poker.level-15-30-no-limit-wsop.xml',
            'conf/poker.level-15-30-no-limit.xml',
            'conf/poker.level-2-4-limit.xml',
            'conf/poker.levels-ante-colin.xml',
            'conf/poker.levels-blinds-colin.xml',
            'conf/poker.levels-blinds-lsng9.xml',
            'conf/poker.levels-blinds.xml',
            'conf/poker.omaha8.xml',
            'conf/poker.omaha.xml',
            'conf/poker.payouts.xml',
            'conf/poker.razz.xml',
        ]),
        ('share/man/man8', ['pokerconfigupgrade.8']),
        ('share/doc/python-poker-engine', ['AUTHORS', 'README'])
    ] + [(
        'share/locale/%s/LC_MESSAGES' % locale,
        ['locale/%s/LC_MESSAGES/poker-engine.mo' % locale]
    ) for locale in list(basename(po).rsplit('.', 1)[0] for po in glob('po/*.po'))],
    cmdclass={'build': ExtendedBuild }
)

