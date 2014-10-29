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
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def index_opi_paths(paths):
    '''
    Return a dictionary:
        relative-filename: (module, path-within-module)

    Example:
        libera/overview.opi: (Libera, data)

    full path is .../Libera/<version>/data/libera/overview.opi
    '''
    filepaths = {}

    NUM_FILES = 0

    for path in paths:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d[0] == '.']
            if root.startswith('.'):
                continue
            else:
                NUM_FILES += len(files)
                module, version, rel_path = utils.parse_module_name(path)
                for file in files:
                    rel_path2 = os.path.join(root[len(path) + 1:], file)
                    if rel_path2.endswith('edl'):
                        rel_path2 = rel_path2[:-3] + 'opi'
                    if rel_path2 in filepaths:
                        log.warn("clash: %s in %s and %s",
                                rel_path2, module, filepaths[rel_path2])
                    else:
                        filepaths[rel_path2] = (module, rel_path)

    return filepaths

def index_paths(paths):
    '''
    Return a dictionary:
        filename: (module, path-within-module)

    Example:
        diagnostics-help: (diagOpi, scripts)

    full path is .../diagOpi/<version>/scripts/diagnostics-help
    '''
    executables = {}
    for path in paths:
        try:
            module, version, rel_path = utils.parse_module_name(path)
        except Exception as e:
            log.warn("Failed to parse module: %s: %s", module, e)
            continue
        files = os.listdir(path)
        for f in files:
            index = path.index(module) + len(module) + 1
            #rel_path = os.path.join(path[index:], f)
            if not f.startswith('.') and not os.path.isdir(f):
                if f in executables:
                    log.warn("clash: %s in %s and %s",
                            (rel_path, path, executables[rel_path]))
                else:
                    print f, rel_path
                    executables[f] = (module, rel_path)

    return executables

def update_opi_path(filename, opi_dict, module):
    if filename in opi_dict:
        if opi_dict[filename][0] != module:
            log.info("correcting %s", filename)
            log.debug(opi_dict[filename])
            rel = os.path.join('..', opi_dict[filename][0], opi_dict[filename][1], filename)
        else:
            rel = os.path.join(opi_dict[filename][1], filename)
    else:
        log.info("not correcting %s", filename)

        rel = filename

    log.info("output is %s", rel)
    return rel


def update_paths(node, file_dict, path_dict, module):
    '''
    Recursively update all paths in the opi file to project-relative ones.
    '''
    UPDATEABLES = ['path', 'image_file']
    if node.tag in UPDATEABLES:
        node.text = update_opi_path(node.text, file_dict, module)
    elif node.tag == 'command':
        cmd_parts = node.text.split()
        updated_cmd = update_opi_path(cmd_parts[0], path_dict, module)
        node.text = ' '.join([updated_cmd] + cmd_parts[1:])
    else:
        for child in node:
            update_paths(child, file_dict, path_dict, module)


def parse(path, file_dict, path_dict, module):
    print 'starting to update paths in', path
    tree = et.parse(path)
    root = tree.getroot()

    update_paths(root, file_dict, path_dict, module)

    # write the new tree out to the same file
    print "making %s writeable" % path
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    utils.make_read_only(path)


if __name__ == '__main__':

    SCRIPT_FILE = "/dls_sw/prod/R3.14.12.3/support/diagOpi/2-44/runedm"
    edmdatafiles, paths = utils.spoof_edm(SCRIPT_FILE)

    file_dict = index_opi_paths(edmdatafiles)
    path_dict = index_paths(paths)
    print "\nOPI PATHS:\n"
    for p in sorted(file_dict):
        print p, file_dict[p]
    print "\nPATHS:\n"
    for p in sorted(path_dict):
        print p, path_dict[p]
    print

    import sys
    root = 'opi/diagOpi/shared'
    opi_files = [os.path.join(root, f) for f in os.listdir(root) if f.endswith('opi')]
    module = 'diagOpi'
    for opi_file in opi_files:
        parse(opi_file, file_dict, path_dict, module)
    # 1. find the root module
    # 2. for all opi files in the root module:
    #  - deduce the relative path
    #  - replace path with relative path


