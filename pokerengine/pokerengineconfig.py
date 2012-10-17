#
# Copyright (C) 2006 - 2010 Loic Dachary <loic@dachary.org>
# Copyright (C) 2004, 2005, 2006 Mekensleep
#
# Mekensleep
# 26 rue des rosiers
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
#  Loic Dachary <loic@dachary.org>
#
import os
from os.path import exists, expanduser, abspath, isfile
from pokerengine.version import Version, version
from pokerengine import log as engine_log
log = engine_log.get_child('config')
import re

import libxml2
import libxslt

class Config:

    upgrades_repository = None
    upgrade_dry_run = False

    def __init__(self, dirs):
        self.path = None
        self.header = None
        self.doc = None
        self.dirs = [ expanduser(dir) for dir in dirs ]
        self.version = version

    def __del__(self):
        self.free()
        
    def free(self):
        if self.doc: self.doc.freeDoc()
        self.doc = None
        if self.header: self.header.xpathFreeContext()
        self.header = None
        
    def reload(self):
        self.free()
        self.doc = libxml2.parseFile(self.path)
        self.header = self.doc.xpathNewContext()

    def load(self, path):
        for prefix in self.dirs:
            tmppath = abspath(expanduser((prefix + "/" + path) if prefix and path[0] != "/" else path ))
            if exists(tmppath):
                self.path = tmppath
                break
        self.free()
        if self.path:
            self.doc = libxml2.parseFile(self.path)
            self.header = self.doc.xpathNewContext()
            if Config.upgrades_repository:
                self.checkVersion("poker_engine_version", version, Config.upgrades_repository)
            return True
        else:
            log.warn("load: unable to find '%s' in directories %s", path, self.dirs)
            return False

    def checkVersion(self, version_attribute, software_version, upgrades_repository, default_version = "1.0.5"):
        version_node = self.header.xpathEval("/child::*/@" + version_attribute)
        if not version_node:
            root_node = self.doc.getRootElement()
            root_node.newProp(version_attribute, default_version)
            if not self.upgrade_dry_run:
                self.save()
            file_version = Version(default_version)
            log.inform("chackVersion: '%s': set default version to %s", self.path, default_version)
        else:
            file_version = Version(version_node[0].content)

        if software_version != file_version:
            if software_version > file_version:
                log.inform("checkVersion: '%s': launch upgrade from %s to %s using repository %s",
                    self.path,
                    file_version,
                    software_version,
                    upgrades_repository
                )
                self.upgrade(version_attribute, file_version, software_version, upgrades_repository)
                return False
            else:
                raise Exception, "Config: %s requires an upgrade to software version %s or better" % ( self.path, str(file_version) )
        else:
            log.inform("checkVersion: '%s': up to date", self.path)
            return True

    def upgrade(self, version_attribute, file_version, software_version, upgrades_repository):
        if upgrades_repository and os.path.exists(upgrades_repository):
            files = map(lambda f: upgrades_repository + "/" + f, os.listdir(upgrades_repository))
            files = filter(lambda f: isfile(f) and ".xsl" in f, files)
            for upgradefile in file_version.upgradeChain(software_version, files):
                log.inform("upgrade: '%s' with '%s'", self.path, upgradefile)
                styledoc = libxml2.parseFile(upgradefile)
                style = libxslt.parseStylesheetDoc(styledoc)
                result = style.applyStylesheet(self.doc, None)
                if not self.upgrade_dry_run:
                    style.saveResultToFilename(self.path, result, compression = 0)
                result.freeDoc()
                # apparently deallocated by freeStylesheet
                # styledoc.freeDoc()
                style.freeStylesheet()
                if not self.upgrade_dry_run:
                    self.reload()
        else:
            log.inform("upgrade: '%s' is not a directory, ignored", upgrades_repository)
        if not self.upgrade_dry_run:
            self.headerSet("/child::*/@" + version_attribute, str(software_version))
            self.save()
        
    def save(self):
        if not self.path:
            log.error("save: unable to write back, invalid path")
            return
        self.doc.saveFile(self.path)
        
    def headerGetList(self, name):
        result = self.header.xpathEval(name)
        return [o.content for o in result]

    def headerGetInt(self, name):
        string = self.headerGet(name)
        if re.match("[0-9]+$", string):
            return int(string)
        else:
            return 0
        
    def headerGet(self, name):
        results = self.header.xpathEval(name)
        return results[0].content if results else ""
        
    def headerSet(self, name, value):
        results = self.header.xpathEval(name)
        results[0].setContent(value)
        
    def headerGetProperties(self, name):
        results = []
        for node in self.header.xpathEval(name):
            results.append(self.headerNodeProperties(node))
        return results

    def headerNodeProperties(self, node):
        result = {}
        properties = node.properties
        while properties != None:
            result[properties.name] = properties.content
            properties = properties.next
        return result
