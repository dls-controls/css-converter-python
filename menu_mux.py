#!/usr/bin/env dls-python
"""
Menu mux widgets in EDM can't be automatically translated by the
converter, because they rely on dynamic macros which do not exist
in CSS.

What can be done is to achieve the same effect with a local PV.
However, the problem with this is that the converter doesn't know
which macros in an OPI file need to be changed to local PVs.

Process:

1. Find all the symbols used by a menu mux button.
2. Find any references to these symbols.
3. Replace the reference with the appropriate expression.
"""

import sys
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import mmux


def perform_postprocess():
    """ Entry point for the MenuMux post-process code

        Converts all mmux controls found under the search directory passed
        as a command line argument (usually project/opi)
    """

    try:
        search_path = sys.argv[1]
    except IndexError:
        print 'Usage: ', sys.argv[0], '<search-path>'
        sys.exit()

    for filepath in mmux.build_filelist(search_path):
        try:
            log.info('Parsing file %s', filepath)
            mmux.parse(filepath)
        except OSError as e:
            log.warn('Menu mux update failed: %s', e)
            continue



if __name__ == '__main__':
    perform_postprocess()
