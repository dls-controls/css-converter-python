import os
import sys
import argparse
import ConfigParser


IOC_CONFIG = 'ioc.ini'
SUPPORT_CONFIG = 'support.ini'
GENERAL_CONFIG = 'converter.ini'


def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument('module', metavar='<module>', nargs=1,
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
        args.support_config = os.path.join(args.c, SUPPORT_CONFIG)
    else:
        args.ioc_config = os.path.join(args.c, IOC_CONFIG)
    args.general_config = os.path.join(args.c, GENERAL_CONFIG)
    if not os.path.exists(args.general_config):
        print('Could not locate configuration file {}'.format(args.general_config))
        sys.exit()

    return args


def parse_configuration(filepath):
    config = ConfigParser.ConfigParser()
    config.read(filepath)
    return config


if __name__ == '__main__':
    args = parse_arguments()
    gen_cfg = parse_configuration(args.general_config)
    if args.i:
        ioc_cfg = parse_configuration(args.ioc_config)
    else:
        support_cfg = parse_configuration(args.support_config)
    print(gen_cfg.get('general', 'java'))
