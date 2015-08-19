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
import ConfigParser
import os
import logging as log
import string
import stat

from convert import dependency, coordinates, utils

SCRIPT_FILE = 'runcss.sh'
SCRIPT_TEMPLATE = 'res/runcss.template'
ESCAPE_CHARS = ['.', ':']
PATH_PREFIX = '${prefix}'

VERSION_FILE = 'configure/VERSION'
MODULE_INI = 'configure/module.ini'


def get_version(configuration_path):
    """ Read the 'new' version number for the VERSION file

        :return Version string (e.g. '4-2dls2')
    """
    version = ""
    path = os.path.join(configuration_path, VERSION_FILE)
    if os.path.exists(path):
        with open(path, 'r') as content_file:
            version = content_file.read()

    return version.rstrip()


def parse_config(base_path):
    """

    :param base_path: Path to module folder containing configure dir
    :return:
    """
    print "Reading opiPath from %s" % base_path

    module_ini_path = os.path.join(base_path, MODULE_INI)

    if not os.path.exists(module_ini_path):
        raise utils.ConfigError('Cannot find module.ini {}'.format(module_ini_path))

    parser = ConfigParser.ConfigParser()
    parser.read(module_ini_path)
    return parser


def get_module_name(parser):

    try:
        module = parser.get('general', 'name')
    except ConfigParser.NoSectionError:
        # file doesn't exist so...
        raise utils.ConfigError("No module name [general/name] specified in module.ini file")

    return module

def get_opi_path(coord):
    """ Extract the opi-file location in the module from the module.ini file

    :raises:
    :param coord: Module coordinate (inc. version)
    :return: Relative path to OPI files, e.g. MyModuleApp/opi/opi
    """
    path = coordinates.as_path(coord)
    if coord.version is None:
        raise ValueError("Dependency with unspecified version: %s", path)

    # plausible default...
    opi_path = "%sApp/opi/opi" % coord.module

    try:
        parser = parse_config(path)
        opi_path = parser.get('general', 'opi-location')
    except utils.ConfigError:
        print "No module.ini file in %s using default %s" % (path, opi_path)
    except ConfigParser.NoSectionError:
        # file doesn't exist so...
        print "No [files] in module.ini file in %s using default %s" % (path, opi_path)

    return opi_path


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


def gen_run_script(coord, cwd):
    '''
    Generate a wrapper script which updates the appropriate
    links before opening a CSS window.

    :param coord: coordindate of module being released, including the release
                    version number. Root should specify the *build* location
    '''
    opi_dir = get_opi_path(coord)

    script_dir = os.path.join(coordinates.as_path(coord), opi_dir)
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    script_path = os.path.join(script_dir, SCRIPT_FILE)

    dependencies = dependency.DependencyParser(coord)

    project_name = "%s_%s" % (coord.module.replace(os.path.sep, '_'), coord.version)
    links_string = build_links(dependencies.find_dependencies(), project_name)

    with open(script_path, 'w') as f:
        with open(os.path.join(cwd, SCRIPT_TEMPLATE)) as template:
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

    script_path = os.path.dirname(os.path.realpath(__file__))
    print("Running from: {}").format(script_path)

    root, area = parse_working_path(working_path)
    print("ROOT: {}, AREA: {}").format(root, area)

    configuration_path = os.path.join(working_path, rel_configuration_path)
    parser = parse_config(configuration_path)

    module_name = get_module_name(parser)
    version = get_version(configuration_path)
    print("MODULE: {}, VERSION: {}").format(module_name, version)

    module_coord = coordinates.create(root, area, module_name, version)
    gen_run_script(module_coord, script_path)
