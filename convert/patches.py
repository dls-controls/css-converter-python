'''
Sometimes it isn't pratically possible to correctly convert
files programmatically. For a subset of files we have to apply
a patch to them manually.

These functions provide the ability to determine where a file is
in the output structure and patch it, assuming the patch has
been contributed to the ./res directory.
'''


import os
from subprocess import Popen, PIPE
import utils


RELATIVE_PATCH_DIR = '../res/patches'


def extract_paths_from_patch_file(patch_file_path):
    '''
    Returns a list of paths that are given in the provided path file.
    '''
    MATCH = '+++ b'
    contents = [line.strip() for line in open(patch_file_path)]
    return [l[len(MATCH):] for l in contents if l.startswith(MATCH)]


def find_file(part_name, root_dir):
    '''
    Uses system based find command to determine which files in the
    root directory match the provided part file path.
    '''
    command = 'find ' + root_dir + ' -wholename "*' + part_name + '"'
    output = Popen(command, shell=True, stdout=PIPE).stdout.read().split('\n')
    return [x for x in output if x]  # Remove empty strings


def patch_file(file_to_patch, patch_file):
    '''
    Applies the patch file patch_file to the specified file.
    Prints the results to stdout.
    '''
    command = ('patch -r - -d ' +
            os.path.dirname(file_to_patch) + ' <' + patch_file)
    utils.make_writeable(file_to_patch)
    print Popen(command, shell=True, stdout=PIPE).stdout.read()


def get_patch_files():
    '''
    Returns the absoloute patchs of each patch file present
    in RELATIVE_PATCH_DIR.
    '''
    this_dir = os.path.dirname(os.path.realpath(__file__))
    patch_dir = os.path.join(this_dir, RELATIVE_PATCH_DIR)
    patches = [p for p in os.listdir(patch_dir) if '.patch' in p]
    return [os.path.join(patch_dir, p) for p in patches]


def apply_patches_to_directory(root_dir):
    '''
    Use the internal res/patches directory to determine which patches to apply
    to the root directory.
    '''
    for patch in get_patch_files():
        paths = extract_paths_from_patch_file(patch)
        find_path = paths[0]  # Only use the first path from the patch file
        file_paths = find_file(find_path, root_dir)
        if len(file_paths) == 0:
            print 'Error: Could not find file to patch:', patch, ":",  find_path
        for file_path in file_paths:
            print 'Patching file', file_path, 'with patch', patch
            patch_file(file_path, patch)

