import pkg_resources
pkg_resources.require('dls_epicsparser')

import os
import sys
import argparse
import ConfigParser

from convert import module, utils, coordinates, paths

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


IOC_CONFIG = 'ioc.ini'
SUPPORT_CONFIG = 'support.ini'
GENERAL_CONFIG = 'converter.ini'


def build_parser():
    """ Construct argument parser for converter

            [-a | -m <module>] -- all or specified module
            [-i | -s] -- IOC or support module
            [-c] -- configuration file location, default "conf/"

    :return: ArgumentParser
    """
    ap = argparse.ArgumentParser()

    target_group = ap.add_mutually_exclusive_group(required=True)
    target_group.add_argument('-a', "--all",
        help='all support or IOC modules', action='store_true')
    target_group.add_argument('-m', "--module",
        help='IOC or support module', metavar='<module>')

    module_type_group = ap.add_mutually_exclusive_group(required=True)
    module_type_group.add_argument('-i', "--ioc",
        help='module is an ioc', action='store_true')
    module_type_group.add_argument('-s', "--support",
        help='module is support module', action='store_true')

    ap.add_argument('-c', "--config",
        help='configuration file directory', metavar='<config-file>', default='conf/')

    return ap


def parse_arguments():
    """ Parse and process user arguments
            - verify required configuration files exist
            - creates 'general_config' and 'module_config' keys based on config path

    :return: processed argument list
    """
    ap = build_parser()
    arguments = ap.parse_args()

    arguments.general_config = os.path.join(arguments.config, GENERAL_CONFIG)

    if arguments.support:
        arguments.module_config = os.path.join(arguments.config, SUPPORT_CONFIG)
    else:  # arguments.ioc
        arguments.module_config = os.path.join(arguments.config, IOC_CONFIG)


    if not os.path.exists(arguments.general_config):
        print('Could not locate configuration file {}'.format(arguments.general_config))
        sys.exit()

    if not os.path.exists(arguments.module_config):
        print('Could not locate configuration file {}'.format(arguments.module_config))
        sys.exit()

    return arguments


def parse_configuration(filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)
    return config


def get_config_section(cfg, name):
    cfg_section = {'datapath': 'data',
                   'opipath': name + 'App/opi/opi',
                   'layers': [],
                   'groups': [],
                   'symbols': [],
                   'version': None}
    try:
        items = cfg.items(name)
        for key, value in items:
            if key in ('layers', 'groups', 'symbols'):
                cfg_section[key] = [val.strip() for val in value.split(';')
                                    if val != '']
            else:
                cfg_section[key] = value
    except ConfigParser.NoSectionError:
        pass
    return cfg_section


def get_modules(args, gen_cfg, area):
    """
    :param args: conversion arguments (uses .all and .module)
    :param module_cfg: configuration containing area
    :param gen_cfg: configuration containing general/prod_root and general/mirror_root
    :return: list of Modules
    """
    modules = []

    root = gen_cfg.get('general', 'prod_root')
    mirror = gen_cfg.get('general', 'mirror_root')

    if args.all:
        #TODO: update to return list of modcoord instead of (name,area,version,root)
        all_mods = utils.find_modules(os.path.join(root, area))
    else:
        all_mods = [args.module]

    for m in all_mods:
        print('The module is {}'.format(m))
        module_cfg = get_config_section(cfg, m)
        version = utils.get_latest_version(os.path.join(root, area, m))
        coords = coordinates.create(root, area, m, version)
        modules.append(module.Module(coords, module_cfg['datapath'],
                                     module_cfg['opipath'], mirror))

    return modules

if __name__ == '__main__':
    force = False
    args = parse_arguments()
    gen_cfg = parse_configuration(args.general_config)
    cfg = parse_configuration(args.module_config)  #ioc.conf or support.conf
    area = 'ioc' if args.ioc else 'support'

    print(gen_cfg.get('general', 'java'))

    modules = get_modules(args, gen_cfg, area)

    for mod in modules:
        dependencies = mod.get_dependencies()
        print('The dependencies are {}'.format(dependencies))
        dirs = [mod.get_datadir()]
        for dep, dep_coords in dependencies.items():
            mod_cfg = get_config_section(cfg, mod.coords.module)
            print('The dep is {}'.format(dep))
            dep_mod = module.Module(dep_coords, mod_cfg['datapath'], mod_cfg['opipath'],
                                    gen_cfg.get('general', 'mirror_root'))
            dirs.append(dep_mod.get_datadir())
        file_index = paths.index_paths(dirs, True)
        mod.convert(file_index, force)
