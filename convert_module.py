import pkg_resources
pkg_resources.require('dls_epicsparser')
import os
import sys
import argparse
import ConfigParser


from convert import module


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

    print arguments

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
    cfg_section = {}
    try:
        items = cfg.items(name)
        for i in items:
            cfg_section[i[0]] = i[1]
    except ConfigParser.NoSectionError:
        pass
    return cfg_section


if __name__ == '__main__':
    args = parse_arguments()
    gen_cfg = parse_configuration(args.general_config)
    cfg = parse_configuration(args.module_config)
    print(gen_cfg.get('general', 'java'))

    module_cfg = get_config_section(cfg, args.module)

    m = module.Module(args.module,
                      module_cfg.get('version', None),
                      gen_cfg.get('general', 'root'),
                      gen_cfg.get('general', 'mirror_root'),
                      args.ioc)

    print(m.get_dependencies())
