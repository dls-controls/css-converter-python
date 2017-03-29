
import logging as log
import os
import ConfigParser

from dls_css_utils import config, utils


VCS_SVN = 'svn'
VCS_GIT = 'git'


GEN_CONF = 'conf/converter.ini'
MODULE_CONF = 'conf/modules.ini'


class ModuleConfig(object):
    """ Data class holding information parsed from the converter's module
        configuration file for a SINGLE MODULE

        Keys read from the config file section are added as instance
        attributes. All instances contain a default set of configuration items.
    """

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
            # Perform post-processing on configuration values
            for key, value in config_parser.items(name):
                if key in ('layers', 'groups', 'symbols', 'path_dirs'):
                    cfg_section[key] = config.split_value_list(value)
                elif key == 'extra_deps':
                    dependencies = config.split_value_list(value)
                    cfg_section[key] = config.parse_dependency_list(
                        dependencies)
                elif key == 'has_opi':
                    cfg_section[key] = config_parser.getboolean(name, key)
                else:
                    cfg_section[key] = value
        except ConfigParser.NoSectionError:
            log.debug('Failed to find configuration for {}'.format(name))

        # Set items in dict as attributes of the object
        for key, value in cfg_section.iteritems():
            setattr(self, key, value)

    def is_git(self):
        return self.vcs == VCS_GIT


class GeneralConfig(object):
    """ Data class holding information parsed from the general converter
        configuration file and the module configuration

        Keys read from the general config files are added as instance
        attributes, individual modules configurations from the config file
        are accessed via a getter.

    """

    def __init__(self, gen_cfg_file=GEN_CONF, mod_cfg_file=MODULE_CONF):
        self._gen_cfg_file = gen_cfg_file
        self._mod_cfg_file = mod_cfg_file
        self._module_cfgs = {}

        # Add all items in the general configuration as attributes of this
        # object.
        gen_cfg_parser = config.parse_configuration(gen_cfg_file)
        for section in gen_cfg_parser.sections():
            for key, value in gen_cfg_parser.items(section):
                setattr(self, key, value)

        # Honour relative or absolute paths for converter output.
        if not os.path.isabs(self.mirror_root):
            self.mirror_root = os.path.join(os.getcwd(), self.mirror_root)

        # Each section of the module configuration becomes a struct in the
        # self._module_cfgs dict.
        self._mod_cfg_parser = config.parse_configuration(mod_cfg_file)
        for section in self._mod_cfg_parser.sections():
            self._module_cfgs[section] = ModuleConfig(self._mod_cfg_parser, section)

    def get_mod_cfg(self, name):
        try:
            return self._module_cfgs[name]
        except KeyError:
            return ModuleConfig(self._mod_cfg_parser, name)
