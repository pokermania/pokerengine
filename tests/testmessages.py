#
# Copyright (C) 2006, 2007, 2008 Loic Dachary <loic@dachary.org>
# Copyright (C) 2006 Mekensleep <licensing@mekensleep.com>
#                    24 rue vieille du temple, 75004 Paris
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU General Public License (GPL) as published by the Free Software
# Foundation (FSF), either version 3 of the License, or (at your option)
# any later version of the GPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program in a file in the toplevel directory called
# "GPLv3".  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#  Loic Dachary <loic@dachary.org>
#
import sys, os

classes = []

from pokerengine import pokergame
classes.append(pokergame.PokerGame)

from pokerengine import pokerprizes
classes.append(pokerprizes.PokerPrizes)

verbose = int(os.environ.get('VERBOSE_T', '-1'))

#
# for coverage purpose, make sure all message functions
# are called at least once
#
def call_messages():
    import StringIO
    for a_class in classes:
        stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        class F(a_class):
            def __init__(self, *args, **kwargs):
                self._prefix = 'P'
                self.prefix = 'P'
                self.id = 1
                self.name = 'name'
        F().message('')
        sys.stdout = stdout
call_messages()

def messages_append(string):
    if verbose > 3:
        print "OUTPUT: " + string
    if not hasattr(string, '__str__'):
        raise Exception, "Message comes in as non-stringifiable object" 
    string = string.__str__()
    messages_out.append(string)

class2message = {
    pokergame.PokerGame: lambda self, string: messages_append(self.prefix + "[PokerGame " + str(self.id) + "] " + string)
    }
messages_out = []

def redirect_messages(a_class):
    if not hasattr(a_class, 'orig_message'):
        a_class.orig_message = [ ]
    a_class.orig_message.append(a_class.message)
    a_class.message = class2message.get(a_class, lambda self, string: messages_append(string))
    
def silence_all_messages():
    messages_out = []
    for a_class in classes:
        redirect_messages(a_class)

def restore_all_messages():
    for a_class in classes:
        a_class.message = a_class.orig_message.pop()

def search_output(what):
    if verbose > 1:
        print "search_output: " + what
    for message in messages_out:
        if message.find(what) >= 0:
            return True
        if verbose > 1:
            print "\tnot in " + message
    return False

def clear_all_messages():
    global messages_out
    messages_out = []

def get_messages():
    return messages_out
