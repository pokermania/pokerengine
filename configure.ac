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
AC_INIT(poker-engine, 1.0.1)
AC_CANONICAL_TARGET
AM_INIT_AUTOMAKE()
AC_CONFIG_SRCDIR([pokerengine/pokergame.py])

# Checks for programs.
AC_PROG_MAKE_SET

AM_PATH_PYTHON([2.3])

AM_MAINTAINER_MODE

# Generate files
AC_CONFIG_FILES([tests/run], [chmod +x tests/run])
AC_CONFIG_FILES([Makefile
                 pokerengine/Makefile
                 tests/Makefile])
AC_OUTPUT
