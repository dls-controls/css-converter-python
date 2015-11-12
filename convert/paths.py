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
    _, module, _, path_within_module = utils.parse_module_name(root)
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
                            entry, new_index[entry], index[entry])
        except (OSError, ValueError) as e:
            log.warn('Skipping indexing: %s', e)
            continue

    log.debug('Indexed OPI paths: %s', index)
    return index


def update_opi_path(filename, depth, file_index, module, use_rel):
    '''
    Return the corrected path according to the contents of the
    file_index.

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
        if original_name in file_index:
            file_index[filename] = file_index[original_name]
        log.debug("Updated file_index for %s", filename)

    pair = file_index.get(filename)
    if pair is not None:
        (file_module, path_in_module) = pair
        # Path in module is not relevant if Eclipse links are directly to
        # the opi directory.
        path_in_module = path_in_module if use_rel else ''
        # If the file is in the same module, go down one less directory
        # and don't put the module name in the relative path.
        if file_module == module:
            file_module = ''
            pieces_in_module_name = len(module.strip(os.path.sep).split(os.path.sep))
            depth -= pieces_in_module_name
        log.debug('Correcting filename %s depth %s', filename, depth)
        down = os.sep.join(['..'] * depth)
        if down == '':
            down = './'
        rel = os.path.join(down, file_module, path_in_module, filename)
    else:
        log.debug('Not correcting %s', filename)

        rel = filename

    log.info('Updated path is %s', rel)
    return rel


def _update_script(script_text, depth, file_index, module, use_rel):
    if 'opi_file' in script_text:
        # Regex group the contents of the quotes containing the filename.
        pattern = 'widget.setPropertyValue *\( *"opi_file" *, *"(.*)"'
        p = re.compile(pattern)
        m = p.search(script_text)
        old_path = m.group(1)
        new_path = update_opi_path(old_path, depth, file_index, module, use_rel)
        log.debug("Updated path in script: %s" % new_path)
        script_text = script_text.replace(m.group(1), new_path)

    return script_text


def _update_paths(node, depth, file_index, module, use_rel):
    """
    Recursively update all paths in the opi file to project-relative ones.
    """
    if node.tag in TAGS_TO_UPDATE:
        node.text = update_opi_path(node.text, depth, file_index, module, use_rel)
    if node.tag == 'command':
        cmd_parts = node.text.split()
        updated_cmd = update_opi_path(cmd_parts[0], depth, file_index, module, use_rel)
        node.text = ' '.join([updated_cmd] + cmd_parts[1:])
    if node.tag == 'scriptText':
        node.text = _update_script(node.text, depth, file_index, module, use_rel)
    for child in node:
        _update_paths(child, depth, file_index, module, use_rel)


def update_opi_file(path, depth, file_index, module, use_rel=True):
    log.debug('Starting to update paths in %s; depth %s', path, depth)
    tree = et.parse(path)
    root = tree.getroot()

    _update_paths(root, depth, file_index, module, use_rel)

    # write the new tree out to the same file
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)


def full_path(dirs, relative_path):
    """
    If the combination of one of the dirs and the relative path
    corresponds to an existing file, return the combined path
    of the first match.
    Otherwise raise ValueError.
    """
    log.debug('Locating %s in directories %s', relative_path, dirs)
    for directory in dirs:
        full_path = os.path.join(directory, relative_path)
        if os.path.exists(full_path):
            return os.path.realpath(full_path)

    raise ValueError('Relative path %s not found in EDMDATAFILES' % relative_path)
