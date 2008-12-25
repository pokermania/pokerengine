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
MAINTAINERCLEANFILES = Makefile.in

export PYTHON

EXTRA_DIST = \
	coverage.py \
	__init__.py \
	testmessages.py \
	test-data/pokerrake.py \
	bugs.py \
	$(wildcard conf/*.xml) \
	$(wildcard test-data/conf/*.xml) \
	$(wildcard test-data/upgrade/*.xsl)

TESTS_ENVIRONMENT = ./run
TESTS = coverage-reset test-*.py history.py deal.py positions.py tournament.py allin.py chips.py blinds.py sit.py upgrades.py muck.py libxml2leak.py coverage-report

clean-local:
	rm -fr .coverage annotated */*.py[oc]

export top_srcdir

.PHONY: coverage-reset coverage-report
