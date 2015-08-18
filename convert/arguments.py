import argparse
import ConfigParser
import logging as log
import os
import sys



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
    target_group.add_argument('-a', '--all',
        help='all support or IOC modules', action='store_true')
    target_group.add_argument('-m', '--module',
        help='IOC or support module', metavar='<module>')

    module_type_group = ap.add_mutually_exclusive_group(required=True)
    module_type_group.add_argument('-i', '--ioc',
        help='module is an ioc', action='store_true')
    module_type_group.add_argument('-s', '--support',
        help='module is support module', action='store_true')

    ap.add_argument('-c', '--config',
        help='configuration file directory', metavar='<config-file>', default='conf/')

    ap.add_argument('-f', '--force', help='Replace all files', action='store_true')
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
        log.warn('Could not locate configuration file %s', arguments.general_config)
        sys.exit()

    if not os.path.exists(arguments.module_config):
        log.warn('Could not locate configuration file %s', arguments.module_config)
        sys.exit()

    return arguments


def parse_configuration(filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)
    return config


def get_config_section(cfg, name):
    # In some cases, the new opi dir will be at moduleNameApp/opi/opi.
    # In some of those cases, the IOC name may be prefix/moduleName
    # e.g. CS/CS-RF-IOC-01 but the leading CS needs removing
    opi_dir = name.split(os.sep)[-1] + 'App/opi/opi'
    cfg_section = {'edl_dir': 'data',
                   'opi_dir': opi_dir,
                   'layers': [],
                   'groups': [],
                   'symbols': [],
                   'extra_deps': [],
                   'version': None}
    try:
        items = cfg.items(name)
        for key, value in items:
            if key in ('layers', 'groups', 'symbols', 'extra_deps'):
                cfg_section[key] = [val.strip() for val in value.split(';')
                                    if val != '']
                if key == 'extra_deps':
                    cfg_section[key] = [os.path.split(val) for val in
                                        cfg_section[key]]
            else:
                cfg_section[key] = value
    except ConfigParser.NoSectionError:
        pass
    return cfg_section

