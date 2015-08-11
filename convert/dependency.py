from pkg_resources import require

require("dls_environment")

import dls_epicsparser.releaseparser
import os

from convert.utils import increment_version


SVN_ROOT = 'svn+ssh://serv0002.cs.diamond.ac.uk/home/subversion/repos/controls'
TRUNK = 'diamond/trunk'
IOC_DIR = '/dls_sw/prod/R3.14.12.3/ioc/'
CONFIGURE_RELEASE = 'configure/RELEASE'
MIRROR_ROOT = '/dls_sw/work/common/CSS/converter/output/mirror_root'


class DependencyParser(object):

    def __init__(self, ioc_name, version):
        """ Parse dependencies for IOC

        :param ioc_name: IOC name (e.g. "LI/TI")
        :param version: Version number to inspect (e.g. "5-4")
        """
        self._ioc_name = ioc_name
        self._ioc_version = version
        self.dependencies = {}

        self.find_dependencies()

    def find_dependencies(self):
        """ Generate a dictionary of dependencies for this module
            {dependency name => path to version+1}
        """
        cr_path = os.path.join(
            IOC_DIR, self._ioc_name, self._ioc_version, CONFIGURE_RELEASE)

        r = dls_epicsparser.releaseparser.Release(cr_path)

        for p in r.flatten():
            if p.path is not None:
                print p.path
                self.dependencies[p.name] = os.path.join('/', increment_version(p.path[1:]))
