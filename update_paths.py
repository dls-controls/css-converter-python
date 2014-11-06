#!/usr/bin/env dls-python

# 1. index files
#  - resolve clashes by order of paths
# 2. index edm files
# 3. parse opi file
# 4. replace files with indexed versions

import os
import xml.etree.ElementTree as et
import utils
import logging as log

TAGS_TO_UPDATE = ['path', 'image_file']

def index_opi_paths(paths):
    '''
    Return a dictionary:
        relative-filename: (module, path-within-module)

    Also changes 'edl' extension to 'opi'

    Example:
        full path:  .../Libera/<version>/data/libera/overview.edl
        key, value: libera/overview.opi: (Libera, data)

    '''
    filepaths = {}

    for path in paths:
        log.debug("Indexing path %s", path)
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d[0] == '.']
            if root.startswith('.'):
                continue
            else:
                try:
                    module, version, rel_path = utils.parse_module_name(path)
                    if rel_path is None:
                        rel_path = ''
                except ValueError:
                    continue
                for f in files:
                    rel_path2 = os.path.join(root[len(path) + 1:], f)
                    if rel_path2.endswith('edl'):
                        rel_path2 = rel_path2[:-3] + 'opi'
                    if rel_path2 in filepaths:
                        log.warn("clash: %s in %s and %s",
                                rel_path2, module, filepaths[rel_path2])
                    else:
                        filepaths[rel_path2] = (module, rel_path)

    log.debug("Indexed OPI paths: %s", filepaths)
    return filepaths


def index_paths(paths):
    '''
    Return a dictionary:
        filename: (module, path-within-module)

    Example:
        full path:  .../diagOpi/<version>/scripts/diagnostics-help
        key, value: diagnostics-help: (diagOpi, scripts)

    '''
    executables = {}
    for path in paths:
        try:
            module, version, rel_path = utils.parse_module_name(path)
        except Exception as e:
            log.warn("Failed to parse module: %s: %s", path, e)
            continue
        files = os.listdir(path)
        for f in files:
            if not f.startswith('.') and not os.path.isdir(f):
                if f in executables:
                    log.warn("clash: %s in %s and %s",
                            rel_path, path, executables[f])
                else:
                    executables[f] = (module, rel_path)

    return executables


def update_opi_path(filename, opi_dict, module):
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
            log.debug("Correcting %s", filename)
            log.debug(opi_dict[filename])
            # we only need the last part of the path
            # i.e. CS/CS-DI-IOC-09  ->  CS-DI-IOC-09
            module_path = opi_dict[filename][0]
            collapsed_path = module_path.split('/')[-1]
            rel = os.path.join('..', collapsed_path, opi_dict[filename][1], filename)
        else:
            rel = os.path.join(opi_dict[filename][1], filename)
    else:
        log.debug("Not correcting %s", filename)

        rel = filename

    log.info("Updated path is %s", rel)
    return rel


def update_paths(node, file_dict, path_dict, module):
    '''
    Recursively update all paths in the opi file to project-relative ones.
    '''
    if node.tag in TAGS_TO_UPDATE:
        node.text = update_opi_path(node.text, file_dict, module)
    elif node.tag == 'command':
        cmd_parts = node.text.split()
        updated_cmd = update_opi_path(cmd_parts[0], path_dict, module)
        node.text = ' '.join([updated_cmd] + cmd_parts[1:])
    else:
        for child in node:
            update_paths(child, file_dict, path_dict, module)


def parse(path, file_dict, path_dict, module):
    log.debug('Starting to update paths in %s', path)
    tree = et.parse(path)
    root = tree.getroot()

    update_paths(root, file_dict, path_dict, module)

    # write the new tree out to the same file
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    utils.make_read_only(path)

