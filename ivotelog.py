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

"""Utility for extracting ballot data (votes) from iVotronic(TM)-style audit
records in text (tabular) format.

Currently generates a (long) report of all candidates and the number of votes
they received, by precinct.  

Command-line usage:
    $ python ivotelog.py <imagelog.txt>

Example output:
    PRECINCT 458 (46 voters)
    CAND VOTES
       1    12
       2    11
       3    17
       4     0
       4    37
       5    30
       [...]

Programmatic usage:
    Don't try.  (Yet.)
"""

import re

#5147971   60 *    3 Gene Kelly                              DEM - United States Senator^M^L....^M
re_vote = re.compile(r'^(\d{7}) (....) (.) (....) (.......................................) (...) - ([^\r]*)\r')
re_precinct_totals = re.compile(r'PRECINCT TOTALS')
re_precinct_num = re.compile(r'PRECINCT .... - PRECINCT (...)')

# TODO
# ----
# Per-candidate -> total
# Per-candidate, per-machine -> total
# Per-office -> total
# Per-office, per-machine -> total
#
# machine -> 'cand' -> candidate -> total
#         -> 'offc' -> office -> total
# 
# While parsing an individual BALLOT: 
#    at most one vote per office
#    tally undervotes, overvotes

class Candidate:
    def __init__(self, name, slot, office):
        self.name = name
        self.slot = slot
        self.office = office
        self.total = 0
        self.machine_totals = {}
        self.precinct_totals = {}

    def vote(self, machine):
        global current_precinct
        self.total += 1
        self.machine_totals[machine] = \
            self.machine_totals.get(machine, 0) + 1
        self.precinct_totals[current_precinct] = \
            self.precinct_totals.get(current_precinct, 0) + 1

class Precinct:
    def __init__(self, name):
        self.name = name
        self.voters = 0
    def vote(self):
        self.voters += 1
    
class Office:
    def __init__(self, name):
        self.name = name
        self.total = 0
        self.machine_totals = {}

    def vote(self, machine):
        self.total += 1
        self.machine_totals[machine] = \
            self.machine_totals.get(machine, 0) + 1

votes = 0
candidates = {}
offices = {}
precincts = {}
current_precinct = ""

def get_candidate(name, slot, office):
    global candidates
    cand_key = '%s:%s' % (name, office)
    if not cand_key in candidates:
        candidates[cand_key] = Candidate(name, slot, office)
    return candidates[cand_key]

def get_office(name):
    global offices
    if not name in offices:
        offices[name] = Office(name)
    return offices[name]

def read_vote(infile):
    global current_precinct, precincts
    for line in infile:
        #print line
        match = re_vote.search(line)
        if match:
            yield match.groups()
            continue
        match = re_precinct_num.search(line)
        if match:
            current_precinct = match.group(1)
            if current_precinct not in precincts:
                precincts[current_precinct] = Precinct(current_precinct)
            continue
        match = re_precinct_totals.search(line)
        if match:
            continue

def tabulate(infile):
    global votes, current_precinct, precincts
    for (vin, bs, star, cand_slot, cand_name, party, race) \
    in read_vote(infile):
        votes += 1
        get_candidate(cand_name, cand_slot, race).vote(vin)
        get_office(race).vote(vin)
        if star == "*": # means a new ballot
            precincts[current_precinct].vote()
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print "usage: ivotelog.py <imagelog.txt>"
        sys.exit(1)
    print "Reading and tabulating..."
    tabulate(open(sys.argv[1]))
    print "Done."
    print "Individual vote items counted: %s" % votes
    print "== Candidates =="
    print " Votes | Candidate ID + Name"
    print "-------|--------------------"
    for name, info in candidates.items():
        print "%6d | %3s %-30s %s" % (info.total, info.slot, info.name, info.office)

    print "\n== Precinct totals (%d precincts) ==" % len(precincts)
    pcts = precincts.keys()
    pcts.sort()
    for pct in pcts:
        pct_voters = 0
        print "=============\nPRECINCT %s (%d voters)" \
            % (pct, precincts[pct].voters)
        print "CAND VOTES"
        cands = candidates.values()
        cands.sort(lambda a,b: cmp(a.slot,b.slot))
        for info in cands:
            cand_votes = info.precinct_totals.get(pct,0)
            pct_voters += cand_votes
            print "%4s %5d" % (info.slot, cand_votes)
