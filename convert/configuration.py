import os
import ConfigParser
from convert import utils, coordinates


MODULE_INI = 'configure/module.ini'


def parse_module_config(base_path):
    """ Parse the module configuration file

    :param base_path: Path to module folder containing configure dir
    :return: ConfigParser
    :raises utils.ConfigError if module.ini file not found
    """
    print "Reading opiPath from %s" % base_path
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

    :raises:
    :param coord: Module coordinate (inc. version)
    :return: Relative path to OPI files, e.g. MyModuleApp/opi/opi
    """

    try:
        opi_path = parser.get('general', 'opi-location')
    except ConfigParser.NoSectionError:
        # file doesn't exist so...
        opi_path = default
        print "No opi-location in module.ini file, using default %s" % (default)

    return opi_path


def parse_configuration(filepath):
    """ Open and parse a configuration file (*.ini)

    :param filepath: File to open
    :return: ConfigParser object
    :raises ConfigError: when specified file does not exist
    """

    if not os.path.exists(filepath):
        raise utils.ConfigError('Cannot find {}'.format(filepath))

    config = ConfigParser.ConfigParser()
    config.read(filepath)
    return config


def split_value_list(value):
    """ Split a list of ';' separated strings into a list.
        Empty elements are removed.
    :param value: Formatted string list of values
    :return: List of string values
    """
    return filter(None, [val.strip() for val in value.split(';')])


def parse_dependency_list(dependencies, cfg):
    """ Parse a list of dependencies, converting into list of
        'dependency tuples'.

        Note: these are NOT coordinates as they do not
        include root path information.

        Area is set to 'support' if no information can be found in the config
        file for dependency module, of config argument is None.

    :param dependencies: List of dependency strings (module/version)
    :param cfg: Converter modules config data (may be None)
    :return: List of tuples (mod,area,version)
    """
    deps = []
    for dep in dependencies:
        module, version = os.path.split(dep)
        area = utils.AREA_SUPPORT

        if cfg is not None:
            try:
                area = cfg.get(module, 'area')
            except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                pass

        deps.append((module, area, version))
    return deps


def get_config_section(cfg, name):
    # In some cases, the new opi dir will be at moduleNameApp/opi/opi.
    # In some of those cases, the IOC name may be prefix/moduleName
    # e.g. CS/CS-RF-IOC-01 but the leading CS needs removing
    opi_dir = name.split(os.sep)[-1] + 'App/opi/opi'
    cfg_section = {'edl_dir': 'data',
                   'opi_dir': opi_dir,
                   'layers': [],
                   'groups': [],
                   'symbols': [],
                   'extra_deps': [],
                   'version': None}
    try:
        items = cfg.items(name)
        for key, value in items:
            if key in ('layers', 'groups', 'symbols'):
                cfg_section[key] = split_value_list(value)
            elif key == 'extra_deps':
                dependencies = split_value_list(value)
                cfg_section[key] = parse_dependency_list(dependencies, cfg)
            else:
                cfg_section[key] = value
    except ConfigParser.NoSectionError:
        pass
    return cfg_section

