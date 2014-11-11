'''
Utility functions used for replacing paths in EDM files with paths in
CSS OPI files.
'''

import os
import re
import xml.etree.ElementTree as et
import utils
import logging as log

TAGS_TO_UPDATE = ['path', 'image_file']


def _index_dir(root, directory, recurse):
    '''
    Index directory as described in index_paths().
    Ignore hidden files.

    Arguments:
     - root:    the EDMDATAFILES or PATH variable inside which this
                dir resides
     - dir:     the directory to index
     - recurse: whether to recursively index subdirectories
    is relative to this directory.
    '''
    index = {}
    root = os.path.normpath(root)
    directory = os.path.normpath(directory)
    log.debug('Indexing directory %s', directory)
    # path_within_module is always relative to root - the EDMDATAFILE
    # or path variable.
    module, _version, path_within_module = utils.parse_module_name(root)
    if path_within_module is None:
        path_within_module = ''
    for entry in os.listdir(directory):
        if entry.startswith('.'):
            continue
        else:
            if os.path.isdir(os.path.join(directory, entry)) and recurse:
                new_index = _index_dir(root, os.path.join(directory, entry), True)
                for new_entry in new_index:
                    if new_entry not in index:
                        index[new_entry] = new_index[new_entry]
                    else:
                        log.warn('clash: %s in %s and %s',
                                entry, module, index[entry])
            else:
                # Get the path of the file relative to the root.
                relative_path = os.path.relpath(os.path.join(directory, entry),
                                                root)
                if relative_path.endswith('edl'):
                    relative_path = relative_path[:-3] + 'opi'
                index[relative_path] = (module, path_within_module)
    return index


def index_paths(directories, recurse):
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
    Also changes 'edl' extension to 'opi'

    Arguments:
     - directories: a list of directories to index
     - recurse:     whether to index all subdirectories

    Return a dictionary:
        relative-filename: (module, path-within-module)

    Example:
        EDMDATAFILES entry: .../Libera/<version>/data/
        full path:          .../Libera/<version>/data/libera/overview.edl
        key, value:         'libera/overview.opi': ('Libera', 'data')

    '''
    index = {}

    for directory in directories:
        try:
            new_index = _index_dir(directory, directory, recurse)
            for entry in new_index:
                if entry not in index:
                    index[entry] = new_index[entry]
                else:
                    log.warn('clash: %s in %s and %s',
                            file, new_index[entry], index[entry])
        except (OSError, ValueError) as e:
            log.warn('Skipping indexing for %s: %s', directory, e)
            continue

    log.info('Indexed OPI paths: %s', index)
    return index


def _update_opi_path(filename, depth, opi_index, module):
    '''
    Return the corrected path according to the contents of the
    opi_index.

    Note that if the 'module' of a file is nested directories, we
    only need to put ../<lastdir>/relative/path
    '''
    # Remove a leading './' if necessary.
    filename = os.path.normpath(filename)
    # Symbol files are converted to pngs with different names
    # We have to update the new filenames, but the old ones are
    # in the index.
    if filename.endswith('png'):
        # Remove everything after the last -
        stub = '-'.join(p for p in filename.split('-')[:-1])
        original_name = stub + '.opi'
        if original_name in opi_index:
            opi_index[filename] = opi_index[original_name]
        log.debug('Updated opi_index for %s', filename)
    if filename in opi_index:
        if opi_index[filename][0] != module:
            log.info('Correcting filename %s', filename)
            # we only need the last part of the path
            # i.e. CS/CS-DI-IOC-09  ->  CS-DI-IOC-09
            module_path = opi_index[filename][0]
            collapsed_path = module_path.split('/')[-1]
            down = '/'.join(['..'] * depth)
            rel = os.path.join(down, collapsed_path,
                               opi_index[filename][1], filename)
        else:
            rel = os.path.join(opi_index[filename][1], filename)
    else:
        log.debug('Not correcting %s', filename)

        rel = filename

    log.info('Updated path is %s', rel)
    return rel


def _update_script(script_text, depth, opi_index, module):
    if 'opi_file' in script_text:
        # Regex group the contents of the quotes containing the filename.
        pattern = 'widget.setPropertyValue *\( *"opi_file" *, *"(.*)"'
        p = re.compile(pattern)
        m = p.search(script_text)
        old_path = m.group(1)
        new_path = _update_opi_path(old_path, depth, opi_index, module)
        log.info('Updated path in script: %s', new_path)
        script_text = script_text.replace(m.group(1), new_path)

    return script_text


def _update_paths(node, depth, opi_index, path_index, module):
    '''
    Recursively update all paths in the opi file to project-relative ones.
    '''
    if node.tag in TAGS_TO_UPDATE:
        node.text = _update_opi_path(node.text, depth, opi_index, module)
    if node.tag == 'command':
        cmd_parts = node.text.split()
        updated_cmd = _update_opi_path(cmd_parts[0], depth, path_index, module)
        node.text = ' '.join([updated_cmd] + cmd_parts[1:])
    if node.tag == 'scriptText':
        node.text = _update_script(node.text, depth, opi_index, module)
    for child in node:
        _update_paths(child, depth, opi_index, path_index, module)


def update_opi_file(path, depth, opi_index, path_index, module):
    log.debug('Starting to update paths in %s; depth %s', path, depth)
    tree = et.parse(path)
    root = tree.getroot()

    _update_paths(root, depth, opi_index, path_index, module)

    # write the new tree out to the same file
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    utils.make_read_only(path)

