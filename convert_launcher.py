#!/usr/bin/env dls-python
'''
Simple script to walk through the Launcher's applications.xml file
and convert EDM files referenced by each script it finds.
'''

import xml.etree.ElementTree as et
import os
import sys
import collections
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import converter
from convert import launcher
from convert import utils
from convert import spoof
from convert import files
from convert import layers
from convert import groups
from convert import mmux
from convert import patches
from convert import colourtweak

APPS_XML = os.path.join(launcher.LAUNCHER_DIR, 'applications.xml')
OUTDIR = 'output'
OUTPATH = os.path.abspath(os.path.join(os.path.dirname(__file__), OUTDIR))
NEW_APPS = os.path.join(OUTPATH, 'css_apps.xml')

SYMBOLS_CONF = 'res/symbols.conf'
LAYERS_CONF = 'conf/layers.path'
GROUPS_CONF = 'conf/groups.path'


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
        print('About to process %s symbol files.' % len(symbol_paths))
        print('Press y to continue, n to quit')
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


def convert_apps(apps, symbols, pp_dict, force):
    app_dict = {}
    symbol_paths = {}
    for name, cmd, args in apps:
        try:
            launcher_cmd = launcher.LauncherCommand(cmd, args.split())
            launcher_cmd.interpret()
            script_path = launcher.gen_run_script(launcher_cmd, OUTPATH)
            run_cmd = launcher.gen_run_cmd(launcher_cmd)
            try:
                c = converter.Converter(launcher_cmd.all_dirs, symbols, OUTPATH, pp_dict)
                c.convert(force)
                new_symbol_paths = c.get_symbol_paths()
            except OSError as e:
                log.warn('Exception converting %s: %s', cmd, e)

            symbol_paths = merge_symbol_paths(symbol_paths, new_symbol_paths)
            log.info('%s gave new command %s %s', cmd, script_path, run_cmd)
            log.debug('%s gave these symbols: %s', cmd, new_symbol_paths)
            app_dict[(name, cmd, args)] = (script_path, [run_cmd])
        except spoof.SpoofError as e:
            log.warn('Could not understand launcher script %s', cmd)
            log.warn(e)
            continue
        except Exception as e:
            log.fatal('Unexpected exception: %s', e)
            log.fatal('Unexpected exception: %s', type(e))
            continue

    return app_dict, symbol_paths


def run_conversion(force, convert_symbols):
    '''
    Iterate over the launcher XML file and fetch each command.
    Convert files referenced by EDM scripts.
    If the command is an EDM script, update XML with new command.
    '''
    tree = et.parse(APPS_XML)
    root = tree.getroot()

    apps = launcher.get_apps(root)
    pp_dict = get_pp_paths()

    symbols = utils.read_symbols_file(SYMBOLS_CONF)
    log.info('Symbols found: %s', symbols)

    # Convert each application from the launcher.
    app_dict, symbol_paths = convert_apps(apps, symbols, pp_dict, force)
    # Update applications.xml and write out to a new file.
    launcher.update_xml(root, app_dict)
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
