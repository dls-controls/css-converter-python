import os
import ConfigParser
from convert import utils, coordinates
import logging as log

MODULE_INI = 'configure/module.ini'

GEN_CONF = 'conf/converter.ini'
MODULE_CONF = 'conf/modules.ini'

SEC_GENERAL = 'general'
OPI_DEPENDS = 'opi-depends'
OPI_LOCATION = 'opi-location'
AREA = 'area'
MODULE_NAME = 'name'

VCS_SVN = 'svn'
VCS_GIT = 'git'


class ModuleConfig(object):

    DEFAULT_CFG = {'edl_dir': 'data',
                       'path_dirs': [],
                       'area': utils.AREA_SUPPORT,
                       'layers': [],
                       'groups': [],
                       'symbols': [],
                       'extra_deps': [],
                       'vcs': VCS_SVN,
                       'has_opi': True,
                       'version': None}

    def __init__(self, config_parser, name):
        # In some cases, the new opi dir will be at moduleNameApp/opi/opi.
        # In some of those cases, the IOC name may be prefix/moduleName
        # e.g. CS/CS-RF-IOC-01 but the leading CS needs removing
        opi_dir = name.split(os.sep)[-1] + 'App/opi/opi'
        cfg_section = dict(ModuleConfig.DEFAULT_CFG)
        cfg_section['opi_dir'] = opi_dir
        try:
            items = config_parser.items(name)
            for key, value in items:
                if key in ('layers', 'groups', 'symbols', 'path_dirs'):
                    cfg_section[key] = split_value_list(value)
                elif key == 'extra_deps':
                    dependencies = split_value_list(value)
                    cfg_section[key] = parse_dependency_list(dependencies,
                                                             config_parser)
                elif key == 'has_opi':
                    cfg_section[key] = config_parser.getboolean(name, key)
                else:
                    cfg_section[key] = value
        except ConfigParser.NoSectionError:
            log.debug('Failed to find configuration for {}'.format(name))
        self.__dict__.update(cfg_section)

    def is_git(self):
        return self.vcs == VCS_GIT


class GeneralConfig(object):

    def __init__(self, gen_cfg_file=GEN_CONF, mod_cfg_file=MODULE_CONF):
        self._gen_cfg_file = gen_cfg_file
        self._mod_cfg_file = mod_cfg_file
        self._module_cfgs = {}

        # Add all items in the general configuration as attributes of this
        # object.
        gen_cfg_parser = parse_configuration(gen_cfg_file)
        for section in gen_cfg_parser.sections():
            cfg_dict = dict(gen_cfg_parser.items(section))
            self.__dict__.update(cfg_dict)

        # Honour relative or absolute paths for converter output.
        if not os.path.isabs(self.mirror_root):
            self.mirror_root = os.path.join(os.getcwd(), self.mirror_root)

        # Each section of the module configuration becomes a struct in the
        # self._module_cfgs dict.
        self._mod_cfg_parser = parse_configuration(mod_cfg_file)
        for section in self._mod_cfg_parser.sections():
            self._module_cfgs[section] = ModuleConfig(self._mod_cfg_parser, section)


    def get_mod_cfg(self, name):
        try:
            return self._module_cfgs[name]
        except KeyError:
            return ModuleConfig(self._mod_cfg_parser, name)


def parse_module_config(base_path):
    """ Parse the module configuration file

    Args:
        base_path: Path to module folder containing configure dir

    Returns:
        ConfigParser

    Raises:
        utils.ConfigError if module.ini file not found
    """
    log.debug("Reading opiPath from %s", base_path)
    module_ini_path = os.path.join(base_path, MODULE_INI)
    return parse_configuration(module_ini_path)


def module_name(parser):
    """ Extract module NAME from the a module.ini parser

    :param parser: Parser
    :return: Module name
    :raises ConfigError: when name not found in parser
    """

    try:
        module = parser.get('general', 'name')
    except ConfigParser.NoSectionError:
        # file doesn't exist so...
        raise utils.ConfigError(
            "No module name [general/name] specified in module.ini file")

    return module


def opi_path(parser, default):
    """ Extract the opi-file location in the module from the module.ini file

    Args:
        parser: Config file parser
        default: Default value, if location key not found

    Returns:
        Relative path to OPI files, e.g. MyModuleApp/opi/opi
    """

    try:
        opis = parser.get('general', 'opi-location')
    except ConfigParser.NoSectionError:
        # file doesn't exist so...
        opis = default
        log.info("No opi-location in module.ini file, using default %s", default)

    return opis


def opi_depends(parser):
    """ Extract the opi-dependencies ("opi-depends") from the module.ini file

    Args:
        parser: Config file parser

    Returns:
        List of root-less coordinates (area, module, version);
            empty if none defined
    """
    depends = []
    try:
        depends_string = parser.get('general', 'opi-depends')
        depends_list = split_value_list(depends_string)
        # assume all depends are 'support' not 'ioc'
        depends = parse_dependency_list(depends_list, None)
    except ConfigParser.NoSectionError:
        log.info("No opi-depends in module.ini file")

    return depends


def parse_configuration(filepath):
    """ Open and parse a configuration file (*.ini)

    Args:
        filepath: File to open

    Returns:
        ConfigParser object

    Raises:
        ConfigError: when specified file does not exist
    """

    if not os.path.exists(filepath):
        raise utils.ConfigError('Cannot find {}'.format(filepath))

    config = ConfigParser.ConfigParser()
    config.read(filepath)
    return config


def split_value_list(value):
    """ Split a list of ';' separated strings into a list.
        Empty elements are removed.

    Args:
        value: Formatted string list of values
    Returns:
        List of string values
    """
    return filter(None, [val.strip() for val in value.split(';')])


def parse_dependency_list(dependencies, cfg):
    """ Parse a list of dependencies, converting into list of
        'dependency tuples'.

        Note: these are NOT coordinates as they do not
        include root path information.

        Area is set to 'support' if no information can be found in the config
        file for dependency module, or config argument is None.

    Args:
        dependencies: List of dependency strings (module or module:version)
        cfg: Converter modules config data (may be None)
    Returns:
        List of root-less coordinates (area,module,version)
    """
    deps = []
    for dep in dependencies:
        if ':' in dep:
            module, version = dep.split(':')
        else:
            module = dep
            version = None

        area = utils.AREA_SUPPORT
        if cfg is not None:
            try:
                area = cfg.get(module, 'area')
            except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                pass

        deps.append(coordinates.create_rootless(area, module, version))
    return deps


def dependency_list_to_string(coord_list):
    """ Convert a list of dependency coords (area, module, version) to
        a semicolon separated list of 'module/version' strings suitable for
        insertion into a module.ini file

        Note: list is NOT terminated by a ';'

    :param coord_list: List to convert
    :return: formatted string list
    """
    return ';'.join(
        [os.sep.join((coord.module, coord.version)) for coord in coord_list])


def create_module_ini_file(coord, mirror_root, opi_location, extra_depends, force):
    """ Create a module.ini file.

        File is *not* overwritten if it already exists UNLESS the force argument
        is set

    :param coord: Used for area and name
    :param opi_location: Relative path to opi files (e.g. xxxApp/opi/opi)
    :param extra_depends: list of all "extra" dependency coords not in RELEASE
    """
    mod_ini_file = os.path.join(mirror_root, coordinates.as_path(coord)[1:], MODULE_INI)
    if force or not os.path.exists(mod_ini_file):

        dependencies = " ; Unable to lookup dependencies in configuration"
        if extra_depends is not None:
            dependencies = dependency_list_to_string(extra_depends)

        config = ConfigParser.ConfigParser()
        config.add_section(SEC_GENERAL)
        config.set(SEC_GENERAL, MODULE_NAME, coord.module)
        config.set(SEC_GENERAL, AREA, coord.area)
        config.set(SEC_GENERAL, OPI_LOCATION, opi_location)
        config.set(SEC_GENERAL, OPI_DEPENDS, dependencies)

        # Writing our configuration file to 'example.cfg'
        with open(mod_ini_file, 'wb') as configfile:
            config.write(configfile)
