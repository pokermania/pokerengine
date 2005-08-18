#
# Copyright (C) 2004, 2005 Mekensleep
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
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#  Loic Dachary <loic@gnu.org>

# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.54)
AC_INIT(poker-engine, [esyscmd(perl -n -e "print if(s/^version_number = \"(.*)\".*/\1/s)" pokerengine/__init__.py)])
AC_CANONICAL_TARGET
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR([pokerengine/pokergame.py])

# Checks for programs.
AC_PROG_MAKE_SET

AC_PATH_PROG(RSYNC, [rsync])

AM_PATH_PYTHON([2.3])

AM_MAINTAINER_MODE

test x$prefix = xNONE && prefix="$ac_default_prefix"

AC_SUBST(POKER_ENGINE_PKGDATADIR, [`eval echo $datadir/$PACKAGE`])

# Generate files
AC_CONFIG_FILES([tests/run pokerconfigupgrade], [chmod 555 $ac_file])
AC_CONFIG_FILES([Makefile
                 poker-engine.pc
                 pokerconfigupgrade.8
                 pokerengine/Makefile
                 tests/allin.py
                 tests/blinds.py
                 tests/buyin.py
                 tests/chips.py
                 tests/deal.py
                 tests/eval.py
                 tests/history.py
                 tests/positions.py
                 tests/sit.py
                 tests/tournament.py
                 tests/upgrades.py
                 tests/Makefile], [chmod -w $ac_file])
AC_OUTPUT
