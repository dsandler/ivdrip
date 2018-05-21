# BallotLog.py - part of the Rice iV Drip package
# Copyright (C) 2006 Rice University
# 
# AUTHORS:
#     Daniel R. Sandler  and  Bryce Eakin
#     {dsandler,beakin}@rice.edu
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

import struct

"""Utility for extracting ballot data (votes) from iVotronic(TM)-style audit
records in raw (.BIN) format.

When run from the command line, will generate a report of all the ballots cast
on the machine from which the audit data was taken, as well as a list of
summary totals per candidate.  (Candidate IDs start from 1 in the printed
output, to match the text files output by official tabulation software.)

Command-line usage:
    $ python BallotLog.py <.BIN file>

Example output:
    BALLOTS:
      [6 21 22 25 29 31 32 34 35 36 40 42 44 45 49 59 69 74 82 122 124]
      [66]
      ...
      TALLY:
      Candidate #1     13
      Candidate #2      7
      Candidate #3     18
      ...

Programmatic usage:
    bl = BallotLog('XXXXXXX')
    bl.read_audit_file(open('VXXXXXXX.BIN'))
    print str(bl)
    # ... bl.ballots ...

"""

class BallotLog:
    # Format discovered by Bryce Eakin, Nov. 2006.
    def __init__(self, machine_id):
        self.ballots = None
        self.machine_id = machine_id
    
    def read_audit_file(self, fn):
        fp = open(fn)

        ballots = []
        
        for bucket_pos in range(0x50000, 0x1f0000, 0x10000):
            # 26 buckets offset by 0x10000 starting at 0x50000
            #print "BUCKET: %08lx" % bucket_pos
            fp.seek(bucket_pos)
            while True:
                len_raw = fp.read(2)
                if len_raw == '\xff\xff': 
                    # end of bucket; no more ballots
                    break
                # Record length (2 bytes): length of ballot (including the 2
                # length bytes); this will include a lot of garbage in
                # addition to individual votes
                record_len = struct.unpack("<H", len_raw)[0]
                #print "DEBUG: record_len = 0x%04x" % record_len
                
                # Extract the entire ballot record
                rec_raw = fp.read(record_len - 2)
                
                # Number of votes in this ballot (the rest is junk)
                num_votes = struct.unpack("<H", rec_raw[9:11])[0]
                #print "DEBUG: num_votes = 0x%04x" % num_votes
                
                ballot = []
                for i in range(0,num_votes):
                    # Ballots contain 0-indexed candidate IDs.  Add 1 to get
                    # the number printed alongside the candidate in the
                    # IMAGELOG.
                    ballot.append(
                        struct.unpack("<H", rec_raw[11+2*i:11+2*i+2])[0])
                ballots.append(ballot)

        self.ballots = ballots

    def __str__(self):
        # Not reproducing the entire IMAGELOG format yet since we're not
        # currently reading out candidate names. Can be cross-referenced with
        # text ballot log or hex dump of .BIN file.
        
        candidates = {}
        
        s = 'BALLOTS:\n'
        for b in self.ballots:
            s += '  [' + ' '.join(['%d' % (1+vote) for vote in b]) + ']\n'
            for vote in b:
                candidates[vote] = candidates.get(vote,0) + 1
            
        s += '\n'
        s += 'TALLY:\n'
        for cand in sorted(candidates.keys()):
            s += "Candidate #%-3d\t%3d\n" % (1+cand, candidates[cand])

        return s

if __name__ == '__main__':
    import sys, os
    for fn in sys.argv[1:]:
        machine_id = os.path.basename(fn)
        if len(machine_id) > 15:
            machine_id = '...' + machine_id[-12:]
        bl = BallotLog(machine_id = machine_id)
        bl.read_audit_file(fn)
        print str(bl)