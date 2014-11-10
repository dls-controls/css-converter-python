#!/usr/bin/env dls-python

# 1. index files
#  - resolve clashes by order of paths
# 2. index edm files
# 3. parse opi file
# 4. replace files with indexed versions

import os
import re
import xml.etree.ElementTree as et
import utils
import logging as log

TAGS_TO_UPDATE = ['path', 'image_file']


def index_path(root, path, recurse):
    filepaths = {}
    log.debug("Indexing path %s", path)
    files = os.listdir(path)
    module, version, path_within_module = utils.parse_module_name(path)
    if path_within_module is None:
        path_within_module = ''
    for f in files:
        if f.startswith('.'):
            continue
        else:
            if os.path.isdir(f) and recurse:
                filepaths.update(index_path(root, os.path.join(path, f), True))
            else:
                relative_path = os.path.join(root[len(path) + 1:], f)
                if relative_path.endswith('edl'):
                    relative_path = relative_path[:-3] + 'opi'
                if relative_path in filepaths:
                    log.warn("clash: %s in %s and %s",
                            relative_path, module, filepaths[relative_path])
                else:
                    filepaths[relative_path] = (module, path_within_module)
    return filepaths


def index_paths(paths, recurse):
    '''
    Index all files available to EDM given the list of paths
    which correspond to the EDMDATAFILES variable.
    Assume any path points to a location within a 'module'
    (either a support module or an IOC).
    The keys in the returned dictionary are paths relative
    to EDMDATAFILES - that is, what will be found in an
    EDM screen.  The values are a tuple (module, path-within-module)
    which allow full construction of a relative path in
    CSS.

    Return a dictionary:
        relative-filename: (module, path-within-module)

    Also changes 'edl' extension to 'opi'

    Example:
        EDMDATAFILES entry: .../Libera/<version>/data/
        full path:          .../Libera/<version>/data/libera/overview.edl
        key, value:         'libera/overview.opi': ('Libera', 'data')

    '''
    filepaths = {}

    for path in paths:
        try:
            filepaths.update(index_path(path, path, recurse))
        except ValueError:
            continue

    log.info("Indexed OPI paths: %s", filepaths)
    return filepaths


def update_opi_path(filename, depth, opi_dict, module):
    '''
    Return the corrected path according to the contents of the
    opi_dict.

    Note that if the 'module' of a file is nested directories, we
    only need to put ../<lastdir>/relative/path
    '''
    if filename.startswith('./'):
        filename = filename[2:]
    # Symbol files are converted to pngs with different names
    # We have to update the new filenames, but the old ones are
    # in the index.
    if filename.endswith('png'):
        # Remove everything after the last -
        stub = '-'.join(p for p in filename.split('-')[:-1])
        original_name = stub + '.opi'
        if original_name in opi_dict:
            opi_dict[filename] = opi_dict[original_name]
        log.debug("Updated opi_dict for %s", filename)
    if filename in opi_dict:
        if opi_dict[filename][0] != module:
            log.info('Correcting filename %s', filename)
            # we only need the last part of the path
            # i.e. CS/CS-DI-IOC-09  ->  CS-DI-IOC-09
            module_path = opi_dict[filename][0]
            collapsed_path = module_path.split('/')[-1]
            down = '/'.join(['..'] * depth)
            rel = os.path.join(down, collapsed_path, opi_dict[filename][1], filename)
        else:
            rel = os.path.join(opi_dict[filename][1], filename)
    else:
        log.debug("Not correcting %s", filename)

        rel = filename

    log.info("Updated path is %s", rel)
    return rel


def update_paths(node, depth, file_dict, path_dict, module):
    '''
    Recursively update all paths in the opi file to project-relative ones.
    '''
    if node.tag in TAGS_TO_UPDATE:
        node.text = update_opi_path(node.text, depth, file_dict, module)
    elif node.tag == 'command':
        cmd_parts = node.text.split()
        updated_cmd = update_opi_path(cmd_parts[0], depth, path_dict, module)
        node.text = ' '.join([updated_cmd] + cmd_parts[1:])
    else:
        for child in node:
            update_paths(child, depth, file_dict, path_dict, module)


def parse(path, depth, file_dict, path_dict, module):
    log.debug('Starting to update paths in %s', path)
    tree = et.parse(path)
    root = tree.getroot()

    update_paths(root, depth, file_dict, path_dict, module)

    # write the new tree out to the same file
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    utils.make_read_only(path)

