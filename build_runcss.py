#!/usr/bin/env dls-python

# from pkg_resources import require
# require("dls_css_converter")
import pkg_resources
import sys

pkg_resources.require('dls_epicsparser')


""" This script populates a runcss.template with

- location of released CSS executable
- list of all module dependencies as { full-path-to-module-version=module-version/moduleApp }
- take launch opi as an argument 'xxx.opi' or 'yyy/xxx.opi'
"""
import os
import logging as log
import string
import stat

from convert import dependency, coordinates, utils, configuration

SCRIPT_FILE = 'runcss.sh'
SCRIPT_TEMPLATE = 'res/runcss.template'
ESCAPE_CHARS = ['.', ':']
PATH_PREFIX = '${prefix}'
DEFAULT_OPI_PATH = "%sApp/opi/opi"


def build_links(dependencies, project_name):
    """ Construct a formatted 'links' string.

        This is comma separated list of
        <full-path-to-versioned-dependency/opi/opi>=<module_name>_<module_version>

        Set of characters, e.g. '.' are replaced with the ascii representations

    :param dependencies: dictionary of dependencies (name, coordinate)
    :param project_name:
    :return: Formatted links string
    """

    links_strings = []
    for dep, dep_coord in dependencies.iteritems():
        opi_path = get_opi_path(dep_coord)
        links_strings.append('%s%s=%s' % (PATH_PREFIX,
                                          os.path.join(coordinates.as_path(dep_coord), opi_path),
                                          os.path.join('/', project_name, dep)))

    links = ',\\\n'.join(links_strings)

    for c in ESCAPE_CHARS:
        links = links.replace(c, '[\%d]' % ord(c))

    return links


def get_opi_path(coord):
    """ Extract the relative path to opi files from a module configuration file

    :param coord: Fully qualified Module coord
    :return: Relative path from module root to the opi files directory
    :raises ValueError: when <coord> does not include version information
    """
    path = coordinates.as_path(coord)
    if coord.version is None:
        raise ValueError("Cannot find data for module with unspecified version: %s", path)

    opi_path = DEFAULT_OPI_PATH % coord.module
    try:
        mod_parser = configuration.parse_module_config(path)
        opi_path = configuration.opi_path(mod_parser, opi_path)
    except utils.ConfigError as ex:
        log.warn("%s in %s", ex.message, path)
        pass

    return opi_path


def gen_run_script(coord, new_version=None, prefix="/", opi_dir=None):
    '''
    Generate a wrapper script which updates the appropriate
    links before opening a CSS window.

    :param coord: coordindate of module being released, including the release
                    version number. Root should specify the *build* location
    '''

    builder_script_path = os.path.dirname(os.path.realpath(__file__))

    if opi_dir is None:
        opi_dir = get_opi_path(coord)

    if new_version is None:
        new_version = coord.version

    script_dir = os.path.join(prefix,
                              coordinates.as_path(coord, False)[1:],
                              new_version,
                              opi_dir)

    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    script_path = os.path.join(script_dir, SCRIPT_FILE)

    dependencies = dependency.DependencyParser(coord)

    project_name = "%s_%s" % (coord.module.replace(os.path.sep, '_'), new_version)
    deps = dependencies.find_dependencies()
    deps[coord.module] = coord
    links_string = build_links(deps, project_name)

    with open(script_path, 'w') as f:
        with open(os.path.join(builder_script_path, SCRIPT_TEMPLATE)) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(links=links_string)
            f.write(updated_content)

    # Give owner and group execute permissions.
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP)
    log.info('Run script written to %s', script_path)
    return script_path


def parse_working_path(path):
    path_root = path
    module_area = ""
    while module_area not in ('support', 'ioc'):
        path_root, module_area = os.path.split(path_root)

    return path_root, module_area

if __name__ == '__main__':
    # Call with:
    #   current working directory (inside the module) and a relative path
    #   to 'parent of the configure' dirctory
    assert len(sys.argv) == 3, "Require modulepath, TOP as arguments"
    working_path = sys.argv[1]
    rel_configuration_path = sys.argv[2]

    root, area = parse_working_path(working_path)
    print("ROOT: {}, AREA: {}").format(root, area)

    configuration_path = os.path.join(working_path, rel_configuration_path)
    module_name = None
    try:
        parser = configuration.parse_module_config(configuration_path)
        module_name = configuration.module_name(parser)
    except utils.ConfigError as ex:
        log.error("Error parsing module.ini %s. Aborting", ex.message)

    if module_name is not None:
        version = utils.get_version(configuration_path)
        print("MODULE: {}, VERSION: {}").format(module_name, version)

        module_coord = coordinates.create(root, area, module_name, version)
        gen_run_script(module_coord)
