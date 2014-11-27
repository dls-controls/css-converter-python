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
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.WARN
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import converter
from convert import utils
from convert import spoof
from convert import files
from convert import paths

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'
APPS_XML = os.path.join(LAUNCHER_DIR, 'applications.xml')
APPS_XML = 'applications.xml'
NEW_APPS = 'new_apps.xml'
OUTDIR = '/home/hgs15624/code/converter/project/opi2'


ESCAPE_CHARS = ['.', ':']

def generate_run_script(script_path, module, project, relative_path, module_dict, macros):
    try:
        os.makedirs(os.path.dirname(script_path))
    except OSError:
        pass
    links_strings = []
    for path, m in module_dict.iteritems():
        m = m.split('/')[-1]
        links_strings.append('%s=%s' % (path, os.path.join('/', project, m)))
    links_string = ',\\\n'.join(links_strings)
    macros_strings = []
    for key, value in macros.iteritems():
        macros_strings.append('%s=%s' % (key, value))
    macros_string = ','.join(macros_strings)
    for c in ESCAPE_CHARS:
        macros_string = macros_string.replace(c, '[\%d]' % ord(c))
        links_string = links_string.replace(c, '[\%d]' % ord(c))
    with open(script_path, 'w') as f:
        with open('res/runcss.template') as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(macros=macros_string,
                                           links=links_string)
            f.write(updated_content)
    # Give owner and group execute permissions.
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP)


def get_module_dict(dirs):
    module_dict = {}
    for directory in dirs:
        log.warn('parsing %s', directory)
        try:
            module_path, module_name, mversion, _ = utils.parse_module_name(directory)
            if mversion is None:
                mversion = ''
            p = os.path.join(OUTDIR, module_path.lstrip('/'), module_name, mversion)
            log.warn(p)
            module_dict[p] = module_name
        except ValueError:
            continue
    return module_dict


def update_cmd(cmd, args, symbols, force):
    try:
        log.warn("%s, %s", cmd, args)
        all_dirs, module_name, version, file_to_run, macros = utils.interpret_command(cmd, args, LAUNCHER_DIR)
    except spoof.SpoofError as e:
        log.warn('Could not understand launcher script %s', cmd)
        log.warn(e)
        return "", [], {}

    file_index = paths.index_paths(all_dirs, True)
    path_to_run = paths.full_path(all_dirs, file_to_run)
    path_to_run = os.path.realpath(path_to_run)
    module_path, module, version, rel_path = utils.parse_module_name(path_to_run)
    # For the purposes of the project name, use only the last directory of the module
    module = module.split('/')[-1]
    project = '%s_%s' % (module, version)
    # Convert file extension
    if rel_path.endswith('edl'):
        rel_path = rel_path[:-3] + 'opi'

    module_dict = get_module_dict(all_dirs)

    script_path = os.path.join(OUTDIR, os.path.dirname(path_to_run.lstrip('/')), 'runcss.sh')
    generate_run_script(script_path, module, project, rel_path, module_dict, macros)
    # Convert file extension
    if file_to_run.endswith('edl'):
        file_to_run = file_to_run[:-3] + 'opi'
    else:
        file_to_run += '.opi'

    symbol_paths = {}
    try:
        c = converter.Converter(all_dirs, symbols, OUTDIR)
        c.convert(force)
        symbol_paths = c.get_symbol_paths()
    except OSError as e:
        log.warn('Exception converting %s: %s', cmd, e)

    launch_opi = os.path.join('/', project, module, rel_path)
    return script_path, [launch_opi], symbol_paths


def get_apps(node):
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


def run_conversion(force):

    tree = et.parse(APPS_XML)
    root = tree.getroot()

    apps = get_apps(root)
    app_dict = {}

    symbols = utils.read_symbols_file('res/symbols.conf')
    log.info('Symbols found: %s', symbols)
    symbol_paths = {}
    for name, cmd, args in apps:
        try:
            new_cmd, new_args, new_symbol_paths = update_cmd(cmd, args.split(), symbols, force)
            symbol_paths = merge_symbol_paths(symbol_paths, new_symbol_paths)
            app_dict[(name, cmd, args)] = (new_cmd, new_args)
        except Exception as e:
            log.fatal('Unexpected exception: %s', e)
            log.fatal('Unexpected exception: %s', type(e))
            continue

    update_xml(root, app_dict)
    tree.write(NEW_APPS, encoding='utf-8', xml_declaration=True)

    if symbol_paths:
        log.info("Post-processing symbol files")
        for path, destinations in symbol_paths.iteritems():
            try:
                files.convert_symbol(path, destinations)
            except (IndexError, AssertionError) as e:
                log.warn('Failed to convert symbol %s: %s', path, e)
                continue


if __name__ == '__main__':
    force = '-f' in sys.argv
    run_conversion(force)
