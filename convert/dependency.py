import dls_epicsparser.releaseparser
import os

CONFIGURE_RELEASE = 'configure/RELEASE'
EPICS_BASE = '/dls_sw/epics/R3.14.12.3/base'


class DependencyParser(object):

    def __init__(self, root, area, module_name, version):
        """ Parse dependencies for IOC

        :param root: Base path to search ('/dls_sw/prod/R3.14.12.3')
        :param area: Module area: 'support' or 'ioc'
        :param module_name: IOC/support module name (e.g. "LI/TI")
        :param version: Version number to inspect (e.g. "5-4")
        """
        self._module_path = os.path.join(root, area, module_name, version)

    def find_dependencies(self):
        """ Generate a dictionary of dependencies for this module

        :return Dictionary of {dependency name => (path to module, version)
        """
        dependencies = {}

        cr_path = os.path.join(self._module_path, CONFIGURE_RELEASE)
        r = dls_epicsparser.releaseparser.Release(cr_path)

        for dependency in r.flatten():
            if self.is_valid(dependency):
                dependencies[dependency.name] = (os.path.split(dependency.path))

        return dependencies

    def is_valid(self, dependency):
        """ Simple test that dependency is 'valid'.
            i.e path and name defined,
                not EPICS base, or a child
                not the searched module

        :param dependency: Dependency to check with .path and .name attributes
        :return: True if valid dependency
        """
        valid = dependency.path is not None
        valid = valid and dependency.name is not None
        valid = valid and not dependency.path.startswith(EPICS_BASE)
        valid = valid and not dependency.path == self._module_path

        return valid
