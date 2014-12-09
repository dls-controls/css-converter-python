#!/bin/env dls-python


import os


FIND_DIR = '/scratch/css/converter/output'
PATCH_DIR = '/scratch/css/converter/res/patches'


def paths_from_patch_file(file_path):
    MATCH = '+++ b'
    contents = [line.strip() for line in open(file_path)]
    return [l[len(MATCH):] for l in contents if l.startswith(MATCH)]


def find_file(part_name):
    command = 'find ' + FIND_DIR + ' -wholename "*' + part_name + '"'
    return [x for x in os.popen(command).read().split('\n') if x]


def patch_file(file_to_patch, patch_file):
    abs_patch = os.path.join(PATCH_DIR, patch_file)
    command = ('patch -r - -d ' +
            os.path.dirname(file_to_patch) + ' <' + abs_patch)
    print os.popen(command).read()


patches = [p for p in os.listdir(PATCH_DIR) if '.patch' in p]
print 'Patch files:\n', patches

for patch in patches:
    paths = paths_from_patch_file(patch)
    find_path = paths[0]
    file_paths = find_file(find_path)
    if len(file_paths) == 0:
        print 'Error: Could not find file to patch:', patch, ":",  find_path
    elif len(file_paths) > 1:
        print 'Which file would you like to patch:'
        for i, f in enumerate(file_paths):
            print i, f
        print 'Get some user input here....'
        i = 0  # TODO: Get user command
        patch_file(file_paths[i], patch)
    else:
        print 'Patching file', file_paths[0]
        patch_file(file_paths[0], patch)
