#
# Copyright (C) 2004, 2005, 2006 Mekensleep
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
if test -z "$RSYNC" ; then
   AC_MSG_ERROR(rsync is needed to install poker-engine)
fi

AM_MAINTAINER_MODE

test x$prefix = xNONE && prefix="$ac_default_prefix"
test x$exec_prefix = xNONE && exec_prefix="$prefix"

if test -z "$PYTHON_VERSION_CONSTRAINT" ; then PYTHON_VERSION_CONSTRAINT='>=2.2' ; fi

m4_define([_AM_PYTHON_INTERPRETER_LIST], [python2.4 python2.3 python2.2 python])
AM_PATH_PYTHON([$PYTHON_VERSION_CONSTRAINT])
eval pythonpath=$pythondir
if eval test "$pythondir" != "$pyexecdir" ; then
   eval pythonpath=$pythonpath:$pyexecdir
fi
AC_SUBST(pythonpath, [$pythonpath])

PKG_CHECK_MODULES(PYPOKER_EVAL, pypoker-eval$PYTHON_VERSION >= 128.0, [
  MAYBE_PYTHON_VERSION=$PYTHON_VERSION
] , [
  PKG_CHECK_MODULES(PYPOKER_EVAL, pypoker-eval >= 128.0,, [AC_MSG_ERROR(pypoker-eval is a mandatory library)])
])
pythonpath=`pkg-config --variable=pythonpath pypoker-eval$MAYBE_PYTHON_VERSION`:$pythonpath

AC_SUBST(MAYBE_PYTHON_VERSION, [$MAYBE_PYTHON_VERSION])
VERSIONED_PACKAGE=$PACKAGE$MAYBE_PYTHON_VERSION
pkgdatadir=$datadir/$PACKAGE$MAYBE_PYTHON_VERSION
AC_SUBST(pkgdatadir, [$pkgdatadir])
pkgsysconfdir=$sysconfdir/$PACKAGE$MAYBE_PYTHON_VERSION
AC_SUBST(pkgsysconfdir, [$pkgsysconfdir])
AC_SUBST(pythondir, [`eval echo $pythondir`])

AC_SUBST(POKER_ENGINE_PKGDATADIR, [`eval echo $datadir/$VERSIONED_PACKAGE`])

PYTHON_DEPENDENCIES="$PYTHON_DEPENDENCIES libxml2"
PYTHON_DEPENDENCIES="$PYTHON_DEPENDENCIES libxslt"

AM_PYTHON_DEPENDS([$PYTHON_DEPENDENCIES])

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
                 tests/muck.py
                 tests/positions.py
                 tests/sit.py
                 tests/tournament.py
                 tests/upgrades.py
                 tests/test-all.py	
                 tests/test-pokercards.py
                 tests/test-pokerengineconfig.py
                 tests/test-pokertournament.py
                 tests/test-game.py
                 tests/test-pokerchips.py
                 tests/test-pokerplayer.py
                 tests/test-version.py
                 tests/Makefile], [chmod -w $ac_file])
AC_OUTPUT
