import sys
sys.path.append('/dls_sw/work/common/python/dls_epicsparser')

from convert import coordinates, configuration, utils
import dls_epicsparser.releaseparser
import os

import logging as log

CONFIGURE_RELEASE = 'configure/RELEASE'
EPICS_BASE = '/dls_sw/epics/R3.14.12.3/base'
EPICS_11_BASE = '/dls_sw/epics/R3.14.11/base'

KNOWN_PARSE_ISSUES = [
    "/dls_sw/prod/R3.14.12.3/ioc/BL18B/BL/3-47/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/ioc/BL03I/BL03I-MO-IOC-02/3-0/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/ioc/BL24I/BL/3-1/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ADBinaries/2-2dls2/configure/RELEASE", #EPICS_HOST_ARCH
    "/dls_sw/prod/R3.14.12.3/support/adUtil/2-0/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/adUtil/2-4/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/aravisGigE/2-0/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ffmpegServer/3-0dls0-1/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ADPilatus/2-1dls5/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ADCore/2-2dls3/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ADCore/2-3dls4/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/ADCore/2-3dls5/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/dxp/3-5dls2/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/dxp/3-5dls4/configure/RELEASE",
    "/dls_sw/prod/R3.14.12.3/support/dtacq_adc/2-0/configure/RELEASE"]


class DependencyParser(object):

    def __init__(self, module_coord, mirror_root="", additional_depends=None):
        """ Parse dependencies for IOC

        Args:
            module_coord: tuple containing path to search area, mod name and version
            additional_depends: list of rootless coords for dependencies not in RELEASE
        """
        assert module_coord.version is not None, \
            "Cannot find dependencies of module (%s) with no version" % module_coord.module
        self._additional = additional_depends
        self._module_path = coordinates.as_path(module_coord)
        self._mirror = mirror_root
        self._root = module_coord.root

        log.info('Preparing conversion of module %s', module_coord)
        if mirror_root:
            log.info("Prefix set for %s to %s" % (module_coord.module, mirror_root))

        if self._mirror and not self._module_path.startswith(self._mirror):
            # Create a working coordinate pointing at the new release, i.e.
            # shadow version. This allows the dependency parser to pull the
            # correct dependencies
            # shadow_coord = coordinates.update_version(
            #     module_coord, utils.increment_version(module_coord.version))
            # log.info("Updating version %s" % shadow_coord.version)

            log.info("Prefixing shadow %s" % self._mirror)
            self._module_path = os.path.join(
                self._mirror, coordinates.as_path(module_coord)[1:])
    def find_dependencies(self):
        """ Generate a dictionary of dependencies for this module

        Returns:
            Dictionary of {dependency name => ModCoord}
        """
        dependencies = {}

        cr_path = os.path.join(self._module_path, CONFIGURE_RELEASE)
        log.debug(">Parsing %s", cr_path)

        try:
            r = dls_epicsparser.releaseparser.Release(cr_path)

            for dependency in r.flatten():
                if self.is_valid(dependency):
                    try:
                        module_cfg = configuration.parse_module_config(dependency.path)
                        name = configuration.module_name(module_cfg)
                    except utils.ConfigError:
                        name = dependency.name

                    dependencies[name] = coordinates.from_path(dependency.path)

            if self._additional is not None:
                for acoord in self._additional:
                    log.info("Additional dependency %s/%s", acoord.module, acoord.version)
                    dependencies[acoord.module] = coordinates.update_root(acoord, self._root)

        except (dls_epicsparser.releaseparser.ParseException, KeyError, AssertionError) as ex:
            log.error("Failed to parse RELEASE for %s: %s", cr_path, ex.message)

            if cr_path not in KNOWN_PARSE_ISSUES:
                raise ex

        return dependencies

    def is_valid(self, dependency):
        """ Simple test that dependency is 'valid'.
            i.e path and name defined,
                not EPICS base, or a child
                not the searched module

        Args:
            dependency: Dependency to check with .path and .name attributes

        Returns:
            True if valid dependency
        """
        valid = (dependency.path is not None
                 and dependency.name is not None
                 and not dependency.path.startswith(EPICS_BASE)
                 and not dependency.path.startswith(EPICS_11_BASE)
                 and not dependency.path == self._module_path)

        return valid
