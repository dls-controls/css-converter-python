#!/usr/bin/env dls-python
"""
Ordering of elements in BOY screens are determined only by their 
position in the xml file.

Create an invisible Rectangle on top of any clickable 
area which has the same click action.  Keep track of x and y
position of any parent grouping containers, so that the 
new Rectangle ends up in the correct place.

Run this script after transforming all the relevant areas.  Note 
that since the widgets it makes are clickable, running this 
script again will make yet more widgets!
"""

import sys
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import layers
from convert import utils


if __name__ == '__main__':

    try:
        path_file = sys.argv[1]
    except IndexError:
        print "Usage: ", sys.argv[0], "<path-file>"
        sys.exit()

    with open(path_file) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == '']

    lines = utils.read_conf_file(path_file)

    for filepath in lines:
        log.info("Parsing file %s", filepath)
        try:
            layers.parse(filepath)
        except (OSError, IOError) as e:
            log.warn("Failed to parse file %s: %s", filepath, e)


