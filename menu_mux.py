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
import subprocess

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

    for filepath in build_filelist(search_path):
        try:
            print 'Parsing file', filepath
            mmux.parse(filepath)
        except OSError as e:
            print 'Update failed: %s' % e
            continue


def build_filelist(basepath):
    """ Execute a grep on the basepath to find all files that contain a menumux
        control

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    proc = subprocess.Popen("find " + basepath + " | xargs grep -sl " + mmux.MENU_MUX_ID,
                            stdout=subprocess.PIPE,
                            shell=True)

    for line in iter(proc.stdout.readline, ''):
        filepath = line.rstrip()
        yield filepath

if __name__ == '__main__':
    perform_postprocess()
