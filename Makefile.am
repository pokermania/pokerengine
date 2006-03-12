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
#
# 
ACLOCAL_AMFLAGS = -I config

pkgdatadir=@pkgdatadir@
pkgsysconfdir=@pkgsysconfdir@
pythondir=@pythondir@

SUBDIRS = pokerengine tests 

MAINTAINERCLEANFILES = \
	py-compile \
	aclocal.m4 \
	config.guess \
	config.sub \
	configure \
	install-sh \
	mkinstalldirs \
	missing \
	Makefile.in \
	INSTALL \
	.in

confpokerdir = ${pkgdatadir}/conf
dist_confpoker_DATA = \
	$(wildcard ${top_srcdir}/conf/*.xml)

upgradepokerdir = ${pkgdatadir}/upgrades
dist_upgradepoker_DATA = \
	$(wildcard ${top_srcdir}/upgrades/*.xsl)

EXTRA_DIST = \
	bootstrap \
	config/python.m4 \
	config/python-depends.m4 \
	examples/simple.py \
	$(wildcard conf/*.template)

pkgconfigdir = ${libdir}/pkgconfig
pkgconfig_DATA = poker-engine.pc

man_MANS = \
	pokerconfigupgrade.8

sbin_SCRIPTS = \
	pokerconfigupgrade

clean-local:
	rm -f */*.py[co]

all-local:
	if [ -w ${srcdir}/conf ] ; then \
		${PYTHON} ${top_builddir}/pokerconfigupgrade --verbose=1 --upgrades=${srcdir}/upgrades ${srcdir}/conf ; \
	fi

install-data-local:
	mkdir -p "${DESTDIR}${pkgsysconfdir}"
	${PYTHON} ${top_builddir}/pokerconfigupgrade --verbose=1 --upgrades=${srcdir}/upgrades --reference=${srcdir}/conf "${DESTDIR}${pkgsysconfdir}"
	chmod u+w "${DESTDIR}${pkgsysconfdir}"

install-data-hook:
	if [ "${MAYBE_PYTHON_VERSION}" ] ; then \
		cp ${DESTDIR}${pkgconfigdir}/poker-engine.pc ${DESTDIR}${pkgconfigdir}/poker-engine${PYTHON_VERSION}.pc ; \
		cp -a ${DESTDIR}${sbindir}/pokerconfigupgrade ${DESTDIR}${sbindir}/pokerconfigupgrade${PYTHON_VERSION} ; \
	fi

uninstall-local:
	rm -fr "${DESTDIR}${pkgsysconfdir}"
	rm -f ${DESTDIR}${sbindir}/pokerconfigupgrade${MAYBE_PYTHON_VERSION}
	rm -f ${DESTDIR}${pkgconfigdir}/poker-engine${MAYBE_PYTHON_VERSION}.pc

buildconf:
	( \
		echo '.01-.02 .01/.02 1 2 1' ; \
		echo '.02-.04 .02/.04 2 4 2' ; \
		echo '.05-.10 .05/.10 5 10 5' ; \
		echo '.10-.25 .10/.25 12 25 1' ; \
		echo '.25-.50 .25/.50 25 50 5' ; \
		echo '.50-1 .50/1 50 100 50' ; \
		echo '1-2 1/2 100 200 100' ; \
		echo '2-4 2/4 200 400 100' ; \
		echo '3-6 3/6 300 600 100' ; \
		echo '5-10 5/10 500 1000 500' ; \
		echo '10-20 10/20 1000 2000 1000' ; \
		echo '30-60 30/60 3000 6000 1000' ; \
		echo '50-100 50/100 5000 10000 5000' ; \
		echo '100-200 100/200 10000 20000 10000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 10` ; \
		best_buy_in=`expr $$big \* 50` ; \
		max_buy_in=`expr $$big \* 100` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" < conf/no-limit.template > conf/poker.$${name}-no-limit.xml ; \
	done

	( \
		echo '.01-.02 .01/.02 1 2 1' ; \
		echo '.02-.04 .02/.04 2 4 2' ; \
		echo '.05-.10 .05/.10 5 10 5' ; \
		echo '.10-.25 .10/.25 12 25 1' ; \
		echo '.25-.50 .25/.50 25 50 5' ; \
		echo '.50-1 .50/1 50 100 50' ; \
		echo '1-2 1/2 100 200 100' ; \
		echo '2-4 2/4 200 400 100' ; \
		echo '3-6 3/6 300 600 100' ; \
		echo '5-10 5/10 500 1000 500' ; \
		echo '10-20 10/20 1000 2000 1000' ; \
		echo '30-60 30/60 3000 6000 1000' ; \
		echo '50-100 50/100 5000 10000 5000' ; \
		echo '100-200 100/200 10000 20000 10000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 10` ; \
		best_buy_in=`expr $$big \* 50` ; \
		max_buy_in=`expr $$big \* 100` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" < conf/pot-limit.template > conf/poker.$${name}-pot-limit.xml ; \
	done

	( \
		echo '.02-.04 .02/.04 1 2 1' ; \
		echo '.05-.10 .05/.10 2 5 1' ; \
		echo '.10-.25 .10/.25 5 10 5' ; \
		echo '.25-.50 .25/.50 12 25 1' ; \
		echo '.50-1 .50/1 25 50 5' ; \
		echo '1-2 1/2 50 100 50' ; \
		echo '2-4 2/4 100 200 100' ; \
		echo '3-6 3/6 150 300 50' ; \
		echo '5-10 5/10 250 500 50' ; \
		echo '10-20 10/20 500 1000 500' ; \
		echo '30-60 30/60 1500 3000 500' ; \
		echo '50-100 50/100 2500 5000 500' ; \
		echo '100-200 100/200 5000 10000 5000' ; \
	) | while read name desc small big unit ; do \
		buy_in=`expr $$big \* 5` ; \
		best_buy_in=`expr $$big \* 30` ; \
		max_buy_in=`expr $$big \* 100000` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" < conf/limit.template > conf/poker.$${name}-limit.xml ; \
	done

	( \
		echo '.04-.08 .04/.08 4 8 1 2 1' ; \
		echo '.10-.20 .10/.20 10 20 2 5 2' ; \
		echo '.25-.50 .25/.50 25 50 5 10 5' ; \
		echo '.50-1 .50/1 50 100 5 25 5' ; \
		echo '1-2 1/2 100 200 10 50 10' ; \
		echo '2-4 2/4 200 400 25 100 25' ; \
		echo '3-6 3/6 300 600 25 150 25' ; \
		echo '5-10 5/10 500 1000 50 200 50' ; \
		echo '10-20 10/20 1000 2000 100 500 100' ; \
		echo '30-60 30/60 3000 6000 500 1500 500' ; \
	) | while read name desc small big ante bringin unit ; do \
		buy_in=`expr $$big \* 5` ; \
		best_buy_in=`expr $$big \* 30` ; \
		max_buy_in=`expr $$big \* 100000` ; \
		sed -e "s;_NAME_;$$name;g" -e "s;_DESC_;$$desc;g" -e "s/_UNIT_/$$unit/g" -e "s/_BEST_BUY_IN_/$$best_buy_in/g" -e "s/_MAX_BUY_IN_/$$max_buy_in/g" -e "s/_BUY_IN_/$$buy_in/g" -e "s/_SMALL_/$$small/g" -e "s/_BIG_/$$big/g" -e "s/_ANTE_/$$ante/g" -e "s/_BRINGIN_/$$bringin/g" < conf/ante-limit.template > conf/poker.ante-$${name}-limit.xml ; \
	done
