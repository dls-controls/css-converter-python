import configuration
import coordinates
import dependency
import utils

import os
import stat
import string
import logging as log


SCRIPT_FILE = 'runcss.sh'
DEFAULT_OPI_PATH = "%sApp/opi/opi"
PATH_PREFIX = '${prefix}'
SCRIPT_TEMPLATE = 'res/runcss.template'
SCRIPT_PERMISSIONS = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | \
    stat.S_IROTH | stat.S_IXOTH  # 0o755


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
    dep_cfg = config.get_mod_cfg(dep)
    try:
        opi_path = dep_cfg.opi_dir
    except (KeyError, AttributeError):
        opi_path = get_opi_path(dep_coord)

    if dep_cfg.has_opi:
        log.info("Adding link to :%s:%s:", dep_coord.area, dep_coord.module)
        new_version = utils.increment_version(dep_coord.version)
        mod_path = coordinates.as_path(
            coordinates.update_version(dep_coord, new_version))
        opi_dir = os.path.join(mod_path, opi_path)
    else:
        log.info("Skipping link to :%s:%s: - no OPIs", dep_coord.area, dep_coord.module)
        opi_dir = None

    return opi_dir


def build_links(dependencies, project_name, prefix, config=None):
    """ Construct a formatted 'links' string.

        This is comma separated list of
        <full-path-to-versioned-dependency/opi/opi>=<module_name>_<module_version>

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

    return links


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


def generate(coord, new_version=None, prefix="/",
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
    if opi_dir is None:
        opi_dir = get_opi_path(coord)

    if new_version is None:
        new_version = coord.version

    # creating working module coord with updated version
    shadow_coord = coordinates.update_version(coord, new_version)

    script_dir = os.path.join(prefix,
                              coordinates.as_path(shadow_coord, True)[1:],
                              opi_dir)

    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    script_path = os.path.join(script_dir, SCRIPT_FILE)

    if config is not None:
        mod_config = config.get_mod_cfg(shadow_coord.module)
        extra_depends = coordinates.update_version_from_files(mod_config.extra_deps,
                                                              shadow_coord.root)
    if extra_depends is None:
        extra_depends = []

    dependencies = dependency.DependencyParser(
        shadow_coord, mirror_root=prefix, additional_depends=extra_depends)

    project_name = "%s_%s" % (shadow_coord.module.replace(os.path.sep, '_'), shadow_coord.version)

    deps = dependencies.find_dependencies()
    # a reference to THIS module needed in the links string is required for
    # correct navigation to add to the dict.
    # Pass the *un-incremented version* as build_links will do an increment
    deps[shadow_coord.module] = coord
    links_string = build_links(deps, project_name, prefix, config)

    with open(script_path, 'w') as f:
        with open(os.path.join(os.getcwd(), SCRIPT_TEMPLATE)) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(links=links_string,
                                           project=project_name,
                                           module=shadow_coord.module)
            f.write(updated_content)

    # Give everyone read/execute permissions
    try:
        os.chmod(script_path, SCRIPT_PERMISSIONS)
    except OSError:
        log.error("Failed to update file permissions for %s", script_path)
    log.info('Run script written to %s', script_path)
    return script_path
