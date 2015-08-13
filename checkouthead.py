'''
Input: IOC name, mirror root.
Output: checkout IOC and dependencies to mirror location.
'''
import pkg_resources
pkg_resources.require('dls_epicsparser')

from convert import utils
from convert import coordinates
from convert import dependency
import os
import subprocess


SVN_ROOT = 'svn+ssh://serv0002.cs.diamond.ac.uk/home/subversion/repos/controls'
TRUNK = 'diamond/trunk'
MIRROR_ROOT = '/scratch/will/css/converter/output/mirror_root'

PROD_ROOT = '/dls_sw/prod/R3.14.12.3/'
AREA = 'support'
MODULE = 'diagOpi'
VERSION = '2-48'


def checkout_module(name, path):
    mirror_location = os.path.join(MIRROR_ROOT, path[1:])
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


def checkout_coords(coords, include_deps=True):
    print(coordinates.as_path(coords))
    if include_deps:
        dp = dependency.DependencyParser(coords)
        to_checkout = dp.find_dependencies()
    else:
        to_checkout = {}

    to_checkout[MODULE] = coords

    for module, mcoords in to_checkout.items():
        try:
            new_version = utils.increment_version(mcoords.version)
            print('new version {}'.format(new_version))
            new_coords = coordinates.create(mcoords.root, mcoords.area,
                                                  mcoords.module, new_version)
            new_path = coordinates.as_path(new_coords)
            checkout_module(new_coords.module, new_path)
        except ValueError:
            print("Can't handle coordinates {}".format(mcoords))


if __name__ == '__main__':
    coords = coordinates.create(PROD_ROOT, AREA, MODULE, VERSION)
    checkout_coords(coords, True)
