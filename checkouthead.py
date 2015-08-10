'''
Input: IOC name, mirror root.
Output: checkout IOC and dependencies to mirror location.
'''
import pkg_resources
pkg_resources.require('dls_epicsparser')

from convert import utils
import dls_epicsparser.releaseparser
import os
import subprocess


SVN_ROOT = 'svn+ssh://serv0002.cs.diamond.ac.uk/home/subversion/repos/controls'
TRUNK = 'diamond/trunk'
IOC_DIR = '/dls_sw/prod/R3.14.12.3/ioc/'
CONFIGURE_RELEASE = 'configure/RELEASE'
MIRROR_ROOT = '/dls_sw/work/common/CSS/converter/output/mirror_root'
IOC_NAME = 'LI/TI'
IOC_VERSION = '5-3'


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
    subprocess.call(['svn', 'checkout', svn_location, mirror_location])


if __name__ == '__main__':
    cr_path = os.path.join(IOC_DIR, IOC_NAME, IOC_VERSION, CONFIGURE_RELEASE)
    r = dls_epicsparser.releaseparser.Release(cr_path)
    r.parse(cr_path)

    for p in r.flatten():
        print p.name, p.path
        try:
            _, module_name, _, _ = utils.parse_module_name(p.path)
        except ValueError:
            module_name = p.name
        try:
            version = p.path.split('/')[-1]
            new_version = utils.increment_version(version)
            print('new version {}'.format(new_version))
            new_path = '/'.join(p.path.split('/')[:-1] + [new_version])
            checkout_module(module_name, new_path)
        except ValueError:
            print("Can't handle path {}".format(p.path))
