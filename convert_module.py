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


def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument('module', metavar='<module>',
                    help='IOC or support module')
    ap.add_argument('-i', help='module is an ioc', action='store_true')
    ap.add_argument('-s', help='module is support module', action='store_true')
    ap.add_argument('-c', help='configuration file directory',
                    metavar='<config-file>',
                    default='conf/')
    args = ap.parse_args()
    if args.s == args.i:
        print('Please choose either IOC [-i] or support module [-s].')
        sys.exit()
    if args.s:
        args.module_config = os.path.join(args.c, SUPPORT_CONFIG)
    else:
        args.module_config = os.path.join(args.c, IOC_CONFIG)
    args.general_config = os.path.join(args.c, GENERAL_CONFIG)
    if not os.path.exists(args.general_config):
        print('Could not locate configuration file {}'.format(args.general_config))
        sys.exit()

    return args


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

    m = module.Module(args.module, module_cfg.get('version', None),
                      gen_cfg.get('general', 'root'),
                      gen_cfg.get('general', 'mirror_root'), args.i)
    print(m.get_dependencies())
