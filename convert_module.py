

import argparse

def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument('module', metavar='<module>', nargs=1,
                    help='IOC or support module')
    ap.add_argument('-i', help='module is an ioc', action='store_true')
    ap.add_argument('-s', help='module is support module', action='store_true')
    ap.add_argument('-c', help='configuration file directory',
                    metavar='<config-file>',
                    default='conf/')
    return ap.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
