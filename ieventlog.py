# ieventlog.py - part of the Rice iV Drip package
# Copyright (C) 2006 Rice University
# 
# AUTHORS:
#     Daniel R. Sandler
#     dsandler@rice.edu
# VERSION: 
#     0.1
# CREATED:
#     2006-Nov-14
# LICENSE:
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Utility for extracting event log data from iVotronic(TM)-style audit records
in raw (.BIN) format and text (tabular) format.

When invoked from the command line, will read an event log text file and scan
a directory for BIN files.  The contents of the text file will be parsed into 
the internal EventLog representation; the same operation will be done with
the binary log files.  The two data sets will be sorted and compared for any
discrepancies (missing events in one or the other).

Command-line usage:
    $ python ieventlog.py <eventlog.txt> <root-path>
    where:
        <eventlog.txt>  : text tabulation of records
        <root-path>     : ancestor directory of *.BIN files to compare 
                          against text tabulation
                          
Programmatic usage: 
    log = EventLog()
    log.read_mem(open('VXXXXXXX.BIN', 'XXXXXXX'))
    log.write_report(sys.stdout)
    # ... log.events ... log.events_per_machine ...
"""

import re
import time

## FORMAT:
#Votronic  PEB#   Type    Date       Time     Event
#5117865  161061  SUP   03/06/2006 16:31:12   01 Terminal clear and test
#         161126  SUP   03/07/2006 07:09:37   09 Terminal open
#                       03/07/2006 07:13:50   13 Print zero tape

re_record = re.compile(
#r'(\d{7})  (\d{6})  (...)   ([0-9/]{10} [0-9:]{8})   (\d{2}) (.......................)\r'
r'(.{7})  (.{6})  (...)   ([0-9/]{10} [0-9:]{8})   (\d{2}) ([^\r]*)\r'
)
(COL_MACHINE, COL_PEBNO, COL_PEBTYPE, COL_DATETIME, COL_EVENTCODE, COL_DESC) \
    = range(6)

re_ws = re.compile(r'^\s*$')
time_fmt = '%m/%d/%Y %H:%M:%S'

# ----- globals -----
(g_current_machine, g_current_peb) = (None, (None, None))

g_event_codes = {}

g_line_no = 0

events = []
events_per_machine = {}
events_per_peb = {}
events_per_code = {}

def reset():
    global events, events_per_peb, events_per_machine, events_per_code, \
        g_line_no, g_current_machine, g_current_peb, g_event_codes
    g_line_no = 0
    events = []
    events_per_machine = {}
    events_per_peb = {}
    events_per_code = {}
    (g_current_machine, g_current_peb) = (None, (None, None))
    g_event_codes = {}

# NEW: Code to analyze memory dumps.
import struct
TIMEBASE = 757404000 # 01/01/94 00:00:00
EVENT_LEN = 10 # bytes
EVENT_OFFSET = 0x30000
class EventLog:
    def __init__(self):
        self.events = []
        self.events_per_machine = {}
    def read_mem(self, fn, mach='(unknown)'):
        fp = open(fn)
        fp.seek(EVENT_OFFSET)
        if not mach in self.events_per_machine:
            self.events_per_machine[mach] = []
        while True:
            eventdata = fp.read(EVENT_LEN)
            if ord(eventdata[0]) == 0xff: break
            e = Event.new_from_buf(eventdata, mach)
            self.events.append(e)
            self.events_per_machine[mach].append(e)
        fp.close()
    def write_report(self, out):
        out.write('Votronic  PEB#   Type    Date       Time     Event\n')
        lastpeb = ''
        lastmach = ''
        for e in self.events:

            peb = "%6d  %3s" % (e.pebno, e.pebtype)
            if peb == lastpeb: peb = ''
            else: lastpeb = peb

            mach = e.machine
            if mach == lastmach: mach = ''
            else:
                out.write('\n')
                lastmach = mach

            out.write("%7s  %11s   %s   %02d %s\n" % (
                mach,
                peb,
                time.strftime("%m/%d/%Y %H:%M:%S",
                        time.localtime(e.timestamp)),
                e.eventcode,
                e.codestr(),
            ))
        out.write('\n')

class Event(object):
    # NEW: Code to analyze memory dumps.
    CODES = {
         1:'Terminal clear and test',
         2:'Terminal screen calibrate',
         3:'Terminal contrast adjust',
         4:'Enter service menu',
         5:'Service password fail',
         6:'Enter ECA menu',
         7:'ECA password fail',
         8:'Date/time change',
         9:'Terminal open',
        10:'Terminal close',
        11:'Precinct upload',
        12:'Audit upload',
        13:'Print zero tape',
        14:'Print Precinct results',
        15:'Modem Precinct results',
        16:'Test vote',
        17:'Votes recollect',
        18:'Invalid vote PEB',
        19:'Invalid super PEB',
        20:'Normal ballot cast',
        21:'Super ballot cast',
        22:'Super ballot cancel',
        23:'Vote PEB load',
        24:'Vote PEB code load',
        25:'Open with super votes',
        26:'Terminal left open',
        27:'Override',
        28:'Override fail',
        29:'EQC start',
        30:'EQC password fail',
        31:'Term, clear/test password fail',
        32:'Clear protective count',
        33:'Print individual zero tape',
        34:'Print individual results',
        35:'Modem Precinct results fail',
        36:'Low battery lockout',
        37:'Nonmaster PEB collection',
        38:'Voter did not select ballot',
        39:'Ballot upload',
        40:'Protective count password OK',
        41:'Protective count password fail',
        42:'Upload firmware password OK',
        43:'Upload firmware password fail',
        44:'Logic and accuracy test',
        45:'Print event log',
        46:'Terminal full',
        47:'Print logic and accuracy report',
        48:'Print vote summary report',
        49:'Internal malfunction',
        50:'Election ID mismatch',
        51:'PEB removed during collection',
    }
    
    def __repr__(self):
        return "<Event at %s: %02d (%s) PEB=%d M=%s>" % (
            time.strftime("%x %X", self.getTimeTuple()),
            self.eventcode, self.codestr(), int(self.pebno),
            str(self.machine)
        )
    def codestr(self):
        return Event.CODES[self.eventcode]
    def unpack(self, buf, machine):
        self.machine = machine
        (self.eventcode, ts, unknown1, self.pebno) = \
            struct.unpack("<bLbL", buf)
        self.timestamp = ts + TIMEBASE
        self.time_tuple = time.localtime(self.timestamp)
        self.datetime = time.strftime(time_fmt, self.time_tuple)
        self.pebtype = ('SUP','VTR')[int(self.pebno==0)]
        self.desc = self.codestr()
    def new_from_buf(buf, machine):
        e = Event.__new__(Event)
        e.unpack(buf, machine)
        return e
    new_from_buf = staticmethod(new_from_buf)

    def __eq__(self, him):
        return self.machine == him.machine \
           and self.eventcode == him.eventcode \
           and self.getTimestamp() == him.getTimestamp() \
           and int(self.pebno) == int(him.pebno)
    
    # Begin code written in Laredo.
    def __init__(self, machine, pebno, pebtype, datetime, eventcode, desc):
        self.machine = machine
        self.pebno = pebno
        self.pebtype = pebtype
        self.datetime = datetime
        self.eventcode = int(eventcode)
        self.desc = desc
        self.timestamp = self.time_tuple = None # lazy

    def construct(params):
        return apply(Event, params)
    construct = staticmethod(construct)

    def parse(line):
        global g_current_machine, g_current_peb, g_event_codes
        match = re_record.match(line)
        if not match:
            return None
        args = list(match.groups())

        if re_ws.match(args[COL_MACHINE]):
            args[COL_MACHINE] = g_current_machine
        elif args[COL_MACHINE] != g_current_machine:
            g_current_machine = args[COL_MACHINE]

        if re_ws.match(args[COL_PEBNO]):
            (args[COL_PEBNO], args[COL_PEBTYPE]) = g_current_peb
        elif args[COL_PEBNO] != g_current_peb[0]:
            g_current_peb = (args[COL_PEBNO], args[COL_PEBTYPE])
        
        eventcode = int(args[COL_EVENTCODE])
        if not eventcode in g_event_codes:
            g_event_codes[eventcode] = args[COL_DESC]
        elif g_event_codes[eventcode] != args[COL_DESC]:
            print "*** LINE %d: WEIRD: old eventcode %d (%s) != new eventcode %d (%s)" \
                % (g_line_no,
                   eventcode, g_event_codes[eventcode],
                   eventcode, args[COL_DESC])

        return Event.construct(args)
    parse = staticmethod(parse)

    def getTimeTuple(self):
        if not self.time_tuple:
            self.time_tuple = time.strptime(self.datetime, time_fmt)
        return self.time_tuple

    def getTimestamp(self):
        if not self.timestamp: 
            self.timestamp = time.mktime(self.getTimeTuple())
        return self.timestamp

def read_event(infile):
    global g_line_no
    for line in infile:
        g_line_no += 1
        evt = Event.parse(line)
        if evt: yield evt

def tabulate(infile):
    global events, events_per_peb, events_per_machine, events_per_code
    reset()

    for event in read_event(infile):
        events.append(event)

        if not event.machine in events_per_machine:
            events_per_machine[event.machine] = []
        events_per_machine[event.machine].append(event)

        pebspec = (event.pebno, event.pebtype)
        if not pebspec in events_per_peb:
            events_per_peb[pebspec] = []
        events_per_peb[pebspec].append(event)

        events_per_code[event.eventcode] = \
            events_per_code.get(event.eventcode, 0) + 1
    
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 2:
        text_event_log = sys.argv[1]
        mem_root = sys.argv[2]
    else:
        print "usage: ieventlog.py <eventlog.txt> <root-path>"
        print "  <eventlog.txt> : text tabulation of records"
        print "  <root-path> : ancestor directory of *.BIN files to compare against text"
        sys.exit(1)

    #text_event_log = 'eveventlog.txt'
    print "Reading and tabulating: " + text_event_log
    tabulate(open(text_event_log))
    print "Done."

    print "Events counted: %d" % len(events)
    print "Machines counted: %d" % len(events_per_machine)
    print "Machines: %s" % ', '.join(events_per_machine.keys())
    print "PEBs counted: %d" % len(events_per_peb)
    print "PEBs: %s" % ', '.join([str(x[0]) for x in events_per_peb.keys()])
    print "Event codes: %d" % len(g_event_codes)
    print "   ID  Count  Desc"
    codes = g_event_codes.keys() ; codes.sort()
    print '\n'.join(["   %02d  %5d %s" % (x, events_per_code[x], 
        g_event_codes[x]) for x in codes])
    print "-" * 60
    print "Normal ballots cast (by machine):"
    total = 0
    machines = events_per_machine.keys() ; machines.sort()
    zeroed = 0
    zeroed_ballots = 0
    for mid in machines:
        extra = " NO ZERO!"
        num = len([evt for evt in events_per_machine[mid] 
                        if evt.eventcode == 20])
        for evt in events_per_machine[mid]:
            if evt.eventcode == 13:
                extra = ""
                zeroed += 1
                zeroed_ballots += num
        print "   %s: %3d%s" % (mid, num, extra)
        total += num
    print "Total ballots: %d" % total
    print "Number of machines where zero-tape was printed: %d (%.1f%%)" % (zeroed,
        ((100.*zeroed)/len(machines)))
    print "Number of ballots from zero-taped machines: %d (%.1f%%)" \
        % (zeroed_ballots, (100.*zeroed_ballots)/total)

    print "-" * 70

    #mem_root = "evflash"
    from rwalk import rwalk
    import os
    from seqdiff import *

    print "Scanning for memories: " + mem_root
    log = EventLog()

    machines = []
    for root, dirs, files in rwalk(mem_root):
        for fn in files:
            m = re.match(r'V(.......)\.BIN$', fn)
            if m:
                machines.append((os.path.join(root,fn), m.group(1)))

    machines.sort(lambda a,b: cmp(a[1],b[1]))
    for path, machine in machines:
        print "  " + machine
        log.read_mem(path, machine)

    print "%d machines; %d events" % (len(machines), len(log.events))

    eventlog_from_mem = open('eventlog_from_mem.txt','w')
    eventlog_from_mem.write("Event log generated from .BIN files at " + time.strftime("%x %X") + " by ieventlog.py\n")
    log.write_report(eventlog_from_mem)

    print "Wrote report to eventlog_from_mem.txt"

    print '-' * 70

    print "Looking for discrepancies..."
    disc_count = 0

    for m1, events1 in events_per_machine.items():
        if not m1 in log.events_per_machine:
            print "!!! don't have memory records for machine " + m1
        else:
            diffs = seqdiff(events1, log.events_per_machine[m1])
            if len(diffs) > 0:
                print "!!! diffs for machine " + m1
                disc_count += 1
                for d in diffs:
                    if d.left:
                        print "<<< in logs only: " + `d.left[1]`
                    if d.right:
                        print ">>> in memory only: " + `d.right[1]`
    if disc_count == 0:
        print "None found."
