from convert import coordinates
import dls_epicsparser.releaseparser
import os

CONFIGURE_RELEASE = 'configure/RELEASE'
EPICS_BASE = '/dls_sw/epics/R3.14.12.3/base'
EPICS_11_BASE = '/dls_sw/epics/R3.14.11/base'


class DependencyParser(object):

    def __init__(self, module_coord, additional_depends=None):
        """ Parse dependencies for IOC

        :param module_coord: tuple containing path to search area, mod name and version
        :param additional_depends: list of rootless coords for dependencies not in RELEASE
        """
        assert module_coord.version is not None, \
            "Cannot find dependencies of module (%s) with no version" % module_coord.module
        self._additional = additional_depends
        self._module_path = coordinates.as_path(module_coord)
        self._root = module_coord.root

    def find_dependencies(self):
        """ Generate a dictionary of dependencies for this module

        :return Dictionary of {dependency name => (path to module, version)
        """
        dependencies = {}

        cr_path = os.path.join(self._module_path, CONFIGURE_RELEASE)
        r = dls_epicsparser.releaseparser.Release(cr_path)

        for dependency in r.flatten():
            if self.is_valid(dependency):
                dependencies[dependency.name] = coordinates.from_path(dependency.path)

        if self._additional is not None:
            for acoord in self._additional:
                dependencies[acoord.module] = coordinates.update_root(acoord, self._root)

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
        valid = valid and not dependency.path.startswith(EPICS_11_BASE)
        valid = valid and not dependency.path == self._module_path

        return valid
