#!/usr/bin/env dls-python

# from pkg_resources import require
# require("dls_css_converter")

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


def build_links(dependencies, project_name, prefix, config=None):
    """ Construct a formatted 'links' string.

        This is comma separated list of
        <full-path-to-versioned-dependency/opi/opi>=<module_name>_<module_version>

        Set of characters, e.g. '.' are replaced with the ascii representations

        Links are NOT added for any module marked as containing no OPIs
        e.g. support/utilities

    :param dependencies: dictionary of dependencies (name, coordinate)
    :param project_name:
    :return: Formatted links string
    """

    links_strings = []
    for dep, dep_coord in dependencies.iteritems():

        opi_dir = get_link_opi_path(config, dep, dep_coord)
        if opi_dir is not None:
            links_strings.append('%s%s=%s' % (PATH_PREFIX,
                                              opi_dir,
                                              os.path.join('/', project_name, dep)))

            if not os.path.exists(os.path.join(prefix, opi_dir[1:])):
                log.warn('Creating link for non-existent path %s%s', prefix, opi_dir)

    links = ',\\\n'.join(links_strings)

    for c in ESCAPE_CHARS:
        links = links.replace(c, '[\%d]' % ord(c))

    return links


def get_link_opi_path(config, dep, dep_coord):
    """ Generate the path to opi files for use in a dependency.

        This uses relative opi-path extracted, and an incremented version number
        The opi-path is extracted from:
        i) the converter's modules.ini file
        ii) the module's module.ini
        iii) best guess from the module path

        If the link doesn't contain OPIs, None is returned.

    :param coord: Fully qualified Module coord
    :return: None or relative path from module root to the opi files directory
    :raises ValueError: when <coord> does not include version information
    """
    config_section = configuration.get_config_section(config, dep)
    try:
        opi_path = config_section['opi_dir']
    except (KeyError, AttributeError):
        opi_path = get_opi_path(dep_coord)

    if configuration.has_opis(config_section):
        new_version = utils.increment_version(dep_coord.version)
        mod_path = coordinates.as_path(
            coordinates.update_version(dep_coord, new_version))
        opi_dir = os.path.join(mod_path, opi_path)
    else:
        opi_dir = None

    return opi_dir


def get_opi_path(coord):
    """ Extract the relative path to opi files from a module configuration file.

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


def gen_run_script(coord, new_version=None, prefix="/",
                   opi_dir=None, config=None, extra_depends=None):
    '''
    Generate a wrapper script which updates the appropriate
    links before opening a CSS window.

    :param coord: coordindate of module being released, including the release
                    version number. Root should specify the *build* location
    :param new_version: explicit version to override that set in the coord
    :param prefix: prefix to use in front of coord fullpath
    :param opi_dir: explicit relative path to opi files, overrides module.ini
    :param config:
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

    if config is not None:
        cfg_section = configuration.get_config_section(config, coord.module)
        extra_depends = cfg_section.get('extra_deps', [])
    if extra_depends is None:
        extra_depends = []

    dependencies = dependency.DependencyParser(coord, extra_depends)

    project_name = "%s_%s" % (coord.module.replace(os.path.sep, '_'), new_version)

    # a reference to THIS module needed in the links string is required for
    # correct navigation to add to the dict of
    deps = dependencies.find_dependencies()
    deps[coord.module] = coord
    links_string = build_links(deps, project_name, prefix, config)

    with open(script_path, 'w') as f:
        with open(os.path.join(builder_script_path, SCRIPT_TEMPLATE)) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(links=links_string,
                                           project=project_name,
                                           module=coord.module)
            f.write(updated_content)

    # Give owner and group execute permissions.
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP)
    log.info('Run script written to %s', script_path)
    return script_path


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
        gen_run_script(module_coord, extra_depends=extra_deps)
