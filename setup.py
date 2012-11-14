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
        os.system("conf/build.sh")
        DistutilsBuild.run(self)

from pprint import pprint as pp

setup(
    name='poker-engine',
    version='1.5.4',
    packages=['pokerengine'],
    data_files=[
        ('bin', ['pokerconfigupgrade']),
        ('share/poker-engine/conf', glob('conf/*.xml')),
        ('share/man/man8', ['pokerconfigupgrade.8']),
        ('share/doc/python-poker-engine', ['AUTHORS', 'README'])
    ] + [(
        'share/locale/%s/LC_MESSAGES' % locale,
        ['locale/%s/LC_MESSAGES/poker-engine.mo' % locale]
    ) for locale in list(basename(po).rsplit('.', 1)[0] for po in glob('po/*.po'))],
    cmdclass={'build': ExtendedBuild }
)

