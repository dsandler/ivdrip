# rwalk.py - part of the Rice iV Drip package
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

import os

def rwalk(p):
    for root, dirs, files in os.walk(p):
        yield root, dirs, files
        for f in dirs:
            fp = os.path.join(root,f)
            if os.path.islink(fp):
                for r, d, f in os.walk(fp): yield r,d,f

if __name__ == '__main__':
    import sys
    print list(os.walk(sys.argv[1]))
    print list(rwalk(sys.argv[1]))
