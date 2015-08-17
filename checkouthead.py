'''
Input: IOC name, mirror root.
Output: checkout IOC and dependencies to mirror location.
'''
import pkg_resources
pkg_resources.require('dls_epicsparser')

from convert import utils
from convert import coordinates
from convert import dependency
import convert_module
import os
import subprocess


SVN_ROOT = 'svn+ssh://serv0002.cs.diamond.ac.uk/home/subversion/repos/controls'
TRUNK = 'diamond/trunk'


def checkout_module(name, path, mirror_root):
    mirror_location = os.path.join(mirror_root, path[1:])
    module_type = 'ioc' if 'ioc' in path else 'support'
    module_name = name if name is not None else ''
    svn_location = os.path.join(SVN_ROOT, TRUNK, module_type, module_name)
    print 'Checkout {} to {}'.format(svn_location, mirror_location)
    try:
        os.makedirs(mirror_location)
    except OSError:
        print 'module already present; skipping'
        return
    ret_val = subprocess.call(['svn', 'checkout', svn_location, mirror_location])
    if ret_val == 0:
        current_dir = os.curdir
        try:
            os.chdir(mirror_location)
            subprocess.call(['make'])
        except OSError:
            os.chdir(current_dir)


def checkout_coords(coords, mirror_root, include_deps=True, extra_deps=None):
    print('Extra dependencies: %s' % extra_deps)
    print(coordinates.as_path(coords))
    if include_deps:
        dp = dependency.DependencyParser(coords, extra_deps)
        to_checkout = dp.find_dependencies()
    else:
        to_checkout = {}

    to_checkout[coords.module] = coords

    for module, mcoords in to_checkout.items():
        try:
            new_version = utils.increment_version(mcoords.version)
            print('new version {}'.format(new_version))
            new_coords = coordinates.create(mcoords.root, mcoords.area,
                                            mcoords.module, new_version)
            new_path = coordinates.as_path(new_coords)
            checkout_module(new_coords.module, new_path, mirror_root)
        except ValueError:
            print("Can't handle coordinates {}".format(mcoords))
    print('Finished checking out all modules.')


if __name__ == '__main__':
    args = convert_module.parse_arguments()
    gen_cfg = convert_module.parse_configuration(args.general_config)
    cfg = convert_module.parse_configuration(args.module_config)
    module_cfg = convert_module.get_config_section(cfg, args.module)
    area = 'ioc' if args.ioc else 'support'
    prod_root = gen_cfg.get('general', 'prod_root')
    mirror_root = gen_cfg.get('general', 'mirror_root')
    coords = coordinates.create(prod_root, area, args.module)
    version = utils.get_latest_version(coordinates.as_path(coords))
    full_coords = coordinates.create(prod_root, area, args.module, version)
    checkout_coords(full_coords, mirror_root, True,
                    module_cfg.get('extra_deps', []))
