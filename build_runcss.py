#!/usr/bin/env dls-python

# from pkg_resources import require
# require("dls_css_converter")
import sys

""" This script populates a runcss.template with

- location of released CSS executable
- list of all module dependencies as { full-path-to-module-version=module-version/moduleApp }
- take launch opi as an argument 'xxx.opi' or 'yyy/xxx.opi'
"""
import os
import logging as log

from convert import coordinates, utils, configuration, run_script


def parse_working_path(path):
    path_root = path
    module_area = ""
    while module_area not in (utils.AREA_SUPPORT, utils.AREA_IOC):
        path_root, module_area = os.path.split(path_root)

    return path_root, module_area


if __name__ == '__main__':
    # Call with:
    #   current working directory (inside the module) and a relative path
    #   to 'parent of the configure' dirctory
    assert len(sys.argv) == 3, "Require modulepath, TOP as arguments"
    # Set up logging if run as script.
    log.basicConfig(level=log.INFO)
    working_path = sys.argv[1]
    rel_configuration_path = sys.argv[2]

    root, area = parse_working_path(working_path)
    log.info("ROOT: %s AREA: %s", root, area)

    configuration_path = os.path.join(working_path, rel_configuration_path)
    module_name = None
    extra_deps = None
    try:
        parser = configuration.parse_module_config(configuration_path)
        module_name = configuration.module_name(parser)
        extra_deps = configuration.opi_depends(parser)
    except utils.ConfigError as ex:
        log.error("Error parsing module.ini %s. Aborting", ex.message)

    if module_name is not None:
        version = utils.get_version(configuration_path)
        log.info("MODULE: %s, VERSION: %s", module_name, version)

        module_coord = coordinates.create(root, area, module_name, version)
        run_script.generate(module_coord, extra_depends=extra_deps)
