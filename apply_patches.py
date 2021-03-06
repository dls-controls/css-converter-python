#!/bin/env dls-python
'''
Sometimes it isn't practically possible to correctly convert
files programmatically. For a subset of files we have to apply
a patch to them manually.

These functions provide the ability to determine where a file is
in the output structure and patch it, assuming the patch has
been contributed to the converter/res/patchs directory.
'''


import sys
from convert import patches


if __name__ == '__main__':
    try:
        root_dir = sys.argv[1]
    except IndexError:
        print 'Usage:', sys.argv[0], '<root dir>'
        sys.exit(-1)

    patches.apply_patches_to_directory(root_dir)
