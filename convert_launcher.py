#!/usr/bin/env dls-python
'''
Simple script to walk through the Launcher's applications.xml file
and convert EDM files referenced by each script it finds.
'''

import xml.etree.ElementTree as et
import os
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import converter
from convert import utils
from convert import spoof
from convert import files

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'
APPS_XML = os.path.join(LAUNCHER_DIR, 'applications.xml')
#APPS_XML = '/home/hgs15624/code/converter/applications.xml'

tree = et.parse(APPS_XML)

root = tree.getroot()

def get_apps(node):
    apps = []
    if node.tag == 'button':
        name = node.get('text')
        cmd = node.get('command')
        args = node.get('args', default="").split()
        apps.append((name, cmd, args))
    else:
        for child in node:
            apps.extend(get_apps(child))
    return apps

def run_conversion():
    launcher_apps = get_apps(root)

    symbol_paths = {}

    for app, cmd, args in launcher_apps:

        try:
            log.warn("%s, %s", cmd, args)
            all_dirs, module_name, version = utils.interpret_command(cmd, args, LAUNCHER_DIR)
        except spoof.SpoofError as e:
            log.warn('Could not understand launcher script %s', cmd)
            log.warn(e)
            continue

        outdir = './project/opi2'
        outdir = os.path.join(outdir, "%s_%s" % (module_name, version))
        utils.generate_project_file(outdir, module_name, version)
        try:
            c = converter.Converter(all_dirs, [], outdir)
            c.convert(False)
            new_symbol_paths = c.get_symbol_paths()
            for symbol in new_symbol_paths:
                if symbol in symbol_paths:
                    symbol_paths[symbol].update(new_symbol_paths[symbol])
                else:
                    symbol_paths[symbol] = new_symbol_paths[symbol]
        except OSError as e:
            log.warn('Exception converting %s: %s', cmd, e)
            continue

    if symbol_paths:
        log.info("Post-processing symbol files")
        for path, destinations in symbol_paths.iteritems():
            try:
                files.convert_symbol(path, destinations)
            except IndexError as e:
                log.warn('Failed to convert symbol %s: %s', path, e)
                continue


if __name__ == '__main__':
    run_conversion()
