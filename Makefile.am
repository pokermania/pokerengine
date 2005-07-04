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
#
# 
ACLOCAL_AMFLAGS = -I config

SUBDIRS = pokerengine tests 

MAINTAINERCLEANFILES = \
	py-compile \
	aclocal.m4 \
	config.guess \
	config.sub \
	configure \
	install-sh \
	missing \
	Makefile.in \
	INSTALL \
	.in

pkgsysconfdir = ${sysconfdir}/${PACKAGE}
dist_pkgsysconf_DATA = \
	conf/poker.0-0-limit.xml \
	conf/poker.10-15-limit.xml \
	conf/poker.10-15-pot-limit.xml \
	conf/poker.15-30-no-limit.xml \
	conf/poker.2-4-limit.xml \
	conf/poker.2-4-no-limit.xml \
	conf/poker.7stud.xml \
	conf/poker.ante-10-15-pot-limit.xml \
	conf/poker.ante-5-10-limit.xml \
	conf/poker.holdem.xml \
	conf/poker.level-10-15-pot-limit.xml \
	conf/poker.level-15-30-no-limit.xml \
	conf/poker.level-2-4-limit.xml \
	conf/poker.omaha8.xml \
	conf/poker.omaha.xml

EXTRA_DIST = \
	bootstrap \
	config/python.m4 \
	examples/simple.py

pkgconfigdir = ${libdir}/pkgconfig
pkgconfig_DATA = poker-engine.pc

clean-local:
	rm -f */*.py[co]
