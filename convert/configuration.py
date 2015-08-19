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
            if key in ('layers', 'groups', 'symbols', 'extra_deps'):
                cfg_section[key] = [val.strip() for val in value.split(';')
                                    if val != '']
                if key == 'extra_deps':
                    cfg_section[key] = [os.path.split(val) for val in
                                        cfg_section[key]]
            else:
                cfg_section[key] = value
    except ConfigParser.NoSectionError:
        pass
    return cfg_section

