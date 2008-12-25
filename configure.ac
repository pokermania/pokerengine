#
# Copyright (C) 2006, 2007, 2008 Loic Dachary <loic@dachary.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep
#
# Mekensleep
# 24 rue vieille du temple
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

# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.54)
AC_INIT(poker-engine, [esyscmd(perl -n -e "print if(s/^version_number = \"(.*)\".*/\1/s)" pokerengine/__init__.py)])
AC_CONFIG_AUX_DIR(config)
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR([pokerengine/pokergame.py])

# Checks for programs.
AC_PROG_MAKE_SET

AC_PATH_PROG(RSYNC, [rsync])
if test -z "$RSYNC" ; then
   AC_MSG_ERROR(rsync is needed to install poker-engine)
fi

AM_MAINTAINER_MODE

AM_PATH_PYTHON([2.3])

pkgsysconfdir=$sysconfdir/$PACKAGE
AC_SUBST(pkgsysconfdir, [$pkgsysconfdir])

PKG_CHECK_MODULES(PYPOKER_EVAL, pypoker-eval >= 132.0,, [AC_MSG_ERROR(pypoker-eval is a mandatory library)])

python_script="
import imp
import sys

path = list()
modules = sys.argv.pop(1)
for module in modules.split('.'):
        (file,  pathname, info) = imp.find_module(module, sys.path + path)
        sys.stdout.write(pathname + ' ')
        path = list(( pathname, ))
"
for module in libxml2 libxslt pokereval ; do
    AC_MSG_CHECKING([wether python module $module is available])
    if $PYTHON -c "$python_script" $module ; then
       AC_MSG_RESULT([... yes])
    else
       AC_MSG_ERROR([failed])
    fi
done

# i18n
AM_PO_SUBDIRS

# Generate files
AC_CONFIG_FILES([tests/run pokerconfigupgrade], [chmod 555 $ac_file])
AC_CONFIG_FILES([po/Makefile], [AM_POSTPROCESS_PO_MAKEFILE])
AC_CONFIG_FILES([Makefile
                 poker-engine.pc
                 pokerconfigupgrade.8
                 pokerengine/Makefile
                 tests/allin.py
                 tests/blinds.py
                 tests/buyin.py
                 tests/bugs.py
                 tests/chips.py
                 tests/deal.py
                 tests/eval.py
                 tests/history.py
                 tests/muck.py
                 tests/positions.py
                 tests/sit.py
                 tests/tournament.py
                 tests/upgrades.py
                 tests/libxml2leak.py
                 tests/test-gamehistory.py
                 tests/test-pokercards.py
                 tests/test-pokerengineconfig.py
                 tests/test-pokertournament.py
                 tests/test-pokerprizes.py
                 tests/test-game.py
                 tests/test-pokerchips.py
                 tests/test-pokerrake.py
                 tests/test-pokerplayer.py
                 tests/test-version.py
                 tests/test-i18n.py
                 tests/Makefile], [chmod -w $ac_file])
AC_OUTPUT
