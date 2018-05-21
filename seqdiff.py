# seqdiff.py - part of the Rice iV Drip package
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

"""Simplistic differencing engine for use with arbitrary Python sequences.

Usage: 
    diffs = seqdiff(seq1, seq2)     # returns a list of Conflict objects
    printdiff(diffs)

See also: help for seqdiff, Conflict, printdiff
"""

LEFT='<'
RIGHT='>'

DEBUG=False

class Conflict(object):
    """Represents a conflict between two sequences.
    
    left - what was on the "left" (first sequence), or None
    right - what was on the "right" (second sequence) or None
    
    if not (left and right): this conflict is an insertion/deletion
    """
    def __init__(self, left, right):
        self.left, self.right = left, right
        if DEBUG: print "Conflict(%s, %s)" % (`left`,`right`)

def seqdiff(s1, s2, find_insertions=True):
    """Diff two sequences. Returns a list of Conflict objects, or an empty
    list if the sequences were identical.  If find_insertions is set, seqdiff
    will look for insertions or deletions (regions existing in one sequence
    but not the other).  This is usually what you want if there's any chance
    your sequences will differ by anything other than point mutation."""
    i1 = 0
    i2 = 0
    diff = []
    while i1 < len(s1) and i2 < len(s2):
        if DEBUG: print "[%d] %-30s | [%d] %-30s" % (i1, `s1[i1]`, i2, `s2[i2]`)
        if s1[i1] == s2[i2]:
            i1+=1 ; i2+=1
        else:
            j1 = j2 = None
            try:
                j1 = s1.index(s2[i2], i1)
            except ValueError:
                pass
            try:
                j2 = s2.index(s1[i1], i2)
            except ValueError:
                pass
            if find_insertions and ((j1 and not j2) or (j1 and j2 and j1 < j2)):
                diff.append(Conflict((i1, s1[i1:(j1)]), None))
                i1 = j1 # skip past the insertion
            elif find_insertions and ((j2 and not j1) or (j1 and j2 and j2 < j1)):
                diff.append(Conflict(None, (i2, s2[i2:(j2)])))
                i2 = j2 # skip past the insertion
            else:
                # the value could not be found on either side
                diff.append(Conflict((i1, [s1[i1]]), (i2, [s2[i2]])))
                i1+=1 ; i2+=1

    if i1 != len(s1):
        diff.append(Conflict((i1, s1[i1:]), None))
    elif i2 != len(s2):
        diff.append(Conflict(None, (i2, s2[i2:])))

    return diff

def printdiff(l):
    """Pretty-print a list of Conflict objects."""
    for d in l:
        if d.left:
            i = d.left[0]
            for ins in d.left[1]:
                print "%s [%d] %s" % (LEFT, i, `ins`)
                i += 1
        if d.right:
            i = d.right[0]
            for ins in d.right[1]:
                print "%s [%d] %s" % (RIGHT, i, `ins`)
                i += 1

if __name__ == '__main__':
    seq1 = "abcdefg"
    seq2 = "abccdefg"
    seq3 = "abdecfg"

    print '-' * 70
    printdiff(seqdiff(seq1, seq2))
    print '-' * 70
    printdiff(seqdiff(seq1, seq3))

    print '-' * 70
    printdiff(seqdiff("Dan Sandler?", "Daniel Sandler!"))
    
