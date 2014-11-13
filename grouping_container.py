#!/usr/bin/env dls-python
'''
In both EDM and CSS grouping contained hold mutiple objects.
The general principle is the same, however: in EDM widgets which
have dimensions exceeding the grouping container are drawn, in
CSS these widgets are clipped to the grouping container area.

This script searches for grouping containers and modifies thier
dimensions so that they match the contents.
'''


import sys
from convert import groups


if __name__ == '__main__':
    try:
        path_file = sys.argv[1]
    except IndexError:
        print "Usage: ", sys.argv[0], "<path-file>"
        sys.exit(-1)

    with open(path_file) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == ''] 

    for file in lines:
        print "Parsing file ", file
        groups.parse(file)
