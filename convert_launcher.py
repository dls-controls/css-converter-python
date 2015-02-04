#!/usr/bin/env dls-python
'''
Simple script to walk through the Launcher's applications.xml file
and convert EDM files referenced by each script it finds.
'''

import xml.etree.ElementTree as et
import os
import stat
import sys
import string
import collections
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import converter
from convert import launcher
from convert import utils
from convert import spoof
from convert import files
from convert import paths
from convert import layers
from convert import groups
from convert import mmux
from convert import patches
from convert import colourtweak

APPS_XML = os.path.join(launcher.LAUNCHER_DIR, 'applications.xml')
OUTDIR = 'output'
OUTPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), OUTDIR))
NEW_APPS = os.path.join(OUTPATH, 'css_apps.xml')
SCRIPT_TEMPLATE = 'res/runcss.template'

SYMBOLS_CONF = 'res/symbols.conf'
LAYERS_CONF = 'conf/layers.path'
GROUPS_CONF = 'conf/groups.path'

ESCAPE_CHARS = ['.', ':']


def get_module_dict(launcher_cmd):
    '''
    Create a mapping from output path to module name.
    '''
    module_dict = {}
    for directory in launcher_cmd.all_dirs:
        try:
            module_path, module_name, mversion, _ = utils.parse_module_name(directory)
            if mversion is None:
                mversion = ''
            p = os.path.join(OUTPATH, module_path.lstrip('/'), module_name, mversion)
            module_dict[p] = module_name
        except ValueError:
            continue
    return module_dict


def gen_run_script(launcher_cmd):
    '''
    Generate a wrapper script which updates the appropriate
    links before opening a CSS window.

    Arguments:
        - script_path - the location of the script to write
        - project - the Eclipse project any links are contained by
        - all_dirs - all directories that may be referenced from this script
    '''
    script_path = os.path.join(OUTPATH, os.path.dirname(launcher_cmd.path_to_run.lstrip('/')), 'runcss.sh')
    try:
        os.makedirs(os.path.dirname(script_path))
    except OSError:
        pass
    links_strings = []
    module_dict = get_module_dict(launcher_cmd)
    for path, m in module_dict.iteritems():
        links_strings.append('%s=%s' % (path, os.path.join('/', launcher_cmd.project, m)))
    links_string = ',\\\n'.join(links_strings)
    for c in ESCAPE_CHARS:
        links_string = links_string.replace(c, '[\%d]' % ord(c))
    with open(script_path, 'w') as f:
        with open(SCRIPT_TEMPLATE) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(links=links_string)
            f.write(updated_content)
    # Give owner and group execute permissions.
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP)
    log.info('Run script written to %s', script_path)
    return script_path


def gen_run_cmd(launcher_cmd):
    # Add OPI shell macro to those already there
    launcher_cmd.macros['OPI_SHELL'] = 'true'
    macros_strings = []
    for key, value in launcher_cmd.macros.iteritems():
        macros_strings.append('%s=%s' % (key, value))
    macros_string = ','.join(macros_strings)
    for c in ESCAPE_CHARS:
        macros_string = macros_string.replace(c, '[\%d]' % ord(c))

    run_cmd = '"%s %s"' % (launcher_cmd.launch_opi, macros_string)
    return run_cmd


def get_apps(node):
    '''
    Recursively retrieve all commands and arguments from the specified
    node in the launcher XML file.

    Return a list of tuples (name, cmd, args).
    '''
    apps = []
    if node.tag == 'button':
        name = node.get('text')
        cmd = node.get('command')
        args = node.get('args', default="")
        apps.append((name, cmd, args))
    else:
        for child in node:
            apps.extend(get_apps(child))
    return apps


def update_xml(node, apps_dict):
    '''
    Given updated commands in apps_dict, recursively update the
    launcher XML file.
    '''
    if node.tag == 'button':
        name = node.get('text')
        cmd = node.get('command')
        args = node.get('args', default="")
        if (name, cmd, args) in apps_dict:
            new_cmd, new_args = apps_dict[(name, cmd, args)]
            node.set('command', new_cmd)
            node.set('args', ' '.join(new_args))
    else:
        for child in node:
            update_xml(child, apps_dict)


def merge_symbol_paths(paths_dict1, paths_dict2):
    for symbol in paths_dict1:
        if symbol in paths_dict2:
            paths_dict2[symbol].update(paths_dict1[symbol])
        else:
            paths_dict2[symbol] = paths_dict1[symbol]
    return paths_dict2


def process_symbol_files(symbol_paths, convert_symbols):
    input = "y" if convert_symbols else ""
    while input.lower() not in ('y', 'n'):
        log.warn('About to process %s symbol files.', len(symbol_paths))
        log.warn('Press y to continue, n to quit')
        input = raw_input()
    if input.lower() == 'y':
        log.info('Post-processing %s symbol files', len(symbol_paths))
        symbol_count = 0
        for path, destinations in symbol_paths.iteritems():
            symbol_count += 1
            log.info('Processed %s of %s symbol files.', symbol_count, len(symbol_paths))
            try:
                files.convert_symbol(path, destinations)
            except (IndexError, AssertionError) as e:
                log.warn('Failed to convert symbol %s: %s', path, e)
                continue
    else:
        log.warn('Not processing symbol files.')


def get_pp_paths():
    layers_paths = [os.path.abspath(p) for p in utils.read_conf_file(LAYERS_CONF)]
    group_paths = [os.path.abspath(p) for p in utils.read_conf_file(GROUPS_CONF)]
    pp_dict = collections.OrderedDict({layers.parse: layers_paths,
                groups.parse: group_paths})
    return pp_dict


def run_conversion(force, convert_symbols):
    '''
    Iterate over the launcher XML file and fetch each command.
    Convert files referenced by EDM scripts.
    If the command is an EDM script, update XML with new command.
    '''
    tree = et.parse(APPS_XML)
    root = tree.getroot()

    apps = get_apps(root)
    pp_dict = get_pp_paths()
    app_dict = {}

    symbols = utils.read_symbols_file(SYMBOLS_CONF)
    log.info('Symbols found: %s', symbols)
    symbol_paths = {}
    for name, cmd, args in apps:
        try:
            launcher_cmd = launcher.LauncherCommand(cmd, args.split())
            launcher_cmd.interpret()
            script_path = gen_run_script(launcher_cmd)
            run_cmd = gen_run_cmd(launcher_cmd)
            try:
                c = converter.Converter(launcher_cmd.all_dirs, symbols, OUTPATH, pp_dict)
                c.convert(force)
                new_symbol_paths = c.get_symbol_paths()
            except OSError as e:
                log.warn('Exception converting %s: %s', cmd, e)

            log.warn('%s gave new command %s %s', cmd, script_path, run_cmd)
            log.warn('%s gave these symbols: %s', cmd, new_symbol_paths)
            symbol_paths = merge_symbol_paths(symbol_paths, new_symbol_paths)
            app_dict[(name, cmd, args)] = (script_path, [run_cmd])
        except spoof.SpoofError as e:
            log.warn('Could not understand launcher script %s', cmd)
            log.warn(e)
            continue
        except Exception as e:
            log.fatal('Unexpected exception: %s', e)
            log.fatal('Unexpected exception: %s', type(e))
            continue

    # Update applications.xml and write out to a new file.
    update_xml(root, app_dict)
    tree.write(NEW_APPS, encoding='utf-8', xml_declaration=True)

    # Post-process menu-mux files
    mmux_paths = [os.path.abspath(p) for p in mmux.build_filelist(OUTDIR)]
    for path in sorted(mmux_paths):
        log.debug('mmpath: %s', path)
        mmux.parse(path)

    # Apply any relevant patches.
    patches.apply_patches_to_directory(OUTPATH)

    # Now change all the colours
    colourtweak_paths = [os.path.abspath(p) for p in colourtweak.build_filelist(OUTDIR)]
    for path in sorted(colourtweak_paths):
        log.debug('colourtweakpath: %s', path)
        colourtweak.parse(path)    

    # Process symbol files at end.
    if symbol_paths:
        process_symbol_files(symbol_paths, convert_symbols)

    log.warn('Conversion finished.')


if __name__ == '__main__':
    force = '-f' in sys.argv
    convert_symbols = "-y" in sys.argv
    run_conversion(force, convert_symbols)
