"""
Inspired by Tom's /dls/cs-www/reports/scripts/list_ioc_support_modules.py
"""

import pkg_resources
pkg_resources.require('jinja2')
import jinja2

from convert import configuration
from convert import coordinates
from convert import dependency
from convert import launcher
from convert import utils
import update_launcher

import os
import subprocess
import ConfigParser
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.WARNING
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

SUPPORT = '/dls_sw/prod/R3.14.12.3/support'
IOC = '/dls_sw/prod/R3.14.12.3/ioc'
REPORT = 'deps.html'
CFG_IOC_CMD = ["configure-ioc", "l"]


class ModDetails(object):
    OK = 'ok'
    OUT_OF_DATE = 'out-of-date'
    CONFIGURED = 'configured'

    def __init__(self, name, requested, latest_release, config_version):
        self.name = name
        self.requested = requested
        self.latest_release = latest_release
        self.config_version = config_version
        self.launcher_version = None
        self.cfg_ioc_version = None
        self.deps = {}
        self.version_class = ModDetails.OK
        self.lversion_class = ModDetails.OK
        self.cversion_class = ModDetails.OK
        self.rversion_class = ModDetails.OK

    def assess_versions(self):
        if self.config_version is not None:
            if utils.newer_version(self.latest_release, self.config_version):
                self.version_class = ModDetails.OUT_OF_DATE
            else:
                self.version_class = ModDetails.CONFIGURED
        if self.launcher_version is not None:
            if utils.newer_version(self.latest_release, self.launcher_version):
                self.lversion_class = ModDetails.OUT_OF_DATE
        if self.requested is not None:
            if utils.newer_version(self.latest_release, self.requested):
                self.rversion_class = ModDetails.OUT_OF_DATE


def get_config_item(cfg, section, option):
    try:
        value = cfg.get(section, option)
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        value = None
    return value


def get_versions(module_cfg, coords):
    try:
        latest_release = utils.get_latest_version(coordinates.as_path(coords, False))
    except ValueError:
        latest_release = '99999'
    config_version = get_config_item(module_cfg, coords.module, 'version')
    return latest_release, config_version


def find_iocs():
    iocs = set()
    for (dirpath, dirnames, filenames) in os.walk(IOC):
        parts = tuple(dirpath.split('/')[1:-1])
        if parts in iocs:
            dirnames[:] = []
            continue
        depth = len(parts)
        if depth > 8:
            dirnames[:] = []
            continue
        else:
            if os.path.exists(os.path.join(dirpath, 'configure/RELEASE')):
                dirnames[:] = []
                iocs.add(parts)

    ioc_names = []
    for path_parts in iocs:
        ioc_index = path_parts.index('ioc')
        ioc_names.append(os.path.sep.join(path_parts[ioc_index + 1:]))

    return ioc_names


def find_support_modules():
    return os.listdir(SUPPORT)


def handle_one_module(module_cfg, module_name, launcher_version, cfg_ioc_version, area):
    coords = coordinates.ModCoord('/dls_sw/prod/R3.14.12.3/', area, module_name, None)
    latest_release, config_version = get_versions(module_cfg, coords)
    extra_deps = configuration.get_config_section(module_cfg, module_name)['extra_deps']
    if config_version is not None:
        vcoords = coordinates.update_version(coords, config_version)
    else:
        vcoords = coordinates.update_version(coords, latest_release)

    log.debug('Dependencies of {} plus {}'.format(vcoords, extra_deps))
    dp = dependency.DependencyParser(vcoords, extra_deps)
    deps = dp.find_dependencies()
    version_deps = {}
    log.debug('{}: {}, {}'.format(module_name, latest_release, config_version))
    for dep_coord in deps.values():
        # find versions here too.
        dep_latest, dep_cfg = get_versions(module_cfg, dep_coord)
        dep_requested = dep_coord.version
        dmd = ModDetails(dep_coord.module, dep_requested, dep_latest, dep_cfg)
        dmd.launcher_version = launcher_version
        dmd.assess_versions()
        version_deps[dep_coord.module] = dmd
        log.debug('{}: {}, {}'.format(dep_coord.module, dep_latest, dep_cfg))

    md = ModDetails(module_name, None, latest_release, config_version)
    md.launcher_version = launcher_version
    md.cfg_ioc_version = cfg_ioc_version
    md.deps = version_deps
    md.assess_versions()
    return md


def get_module_details(module_cfg, launcher_versions):
    """Locate all support modules and iocs and return their dependencies.

    Returns:
        dict mapping module name (e.g. 'LI/TI') to ModDetails tuple
    """
    support_modules = find_support_modules()
    cfg_ioc_versions = get_configure_ioc_versions(support_modules)
    iocs = find_iocs()
    cfg_ioc_versions.update(get_configure_ioc_versions(iocs))

    module_details = {}
    for module in support_modules:
        launcher_version = launcher_versions.get(module, None)
        cfg_ioc_version = cfg_ioc_versions.get(module, None)
        try:
            module_details[module] = handle_one_module(module_cfg, module, launcher_version, cfg_ioc_version, 'support')
        except AssertionError as e:
            log.warn('Failed on {}: {}'.format(module, e))

    for module in iocs:
        launcher_version = launcher_versions.get(module, None)
        cfg_ioc_version = cfg_ioc_versions.get(module, None)
        try:
            module_details[module] = handle_one_module(module_cfg, module, launcher_version, cfg_ioc_version, 'ioc')
        except AssertionError as e:
            log.warn('Failed on {}: {}'.format(module, e))

    return module_details


def render(max_deps, table):
    env = jinja2.Environment(loader=jinja2.PackageLoader('html_versions', 'res'))
    template = env.get_template('template.html')
    header_tags = ['thead', 'tfoot']
    full_html = template.render(header_tags=header_tags, nheaders=max_deps,
                                mod_details=table)

    with open(REPORT, 'w') as f:
        f.write(full_html)


def get_max_deps(module_details):
    return max(len(val.deps) for mod, val in module_details.iteritems())


def generate_headers(max_deps):
    header = ''
    for tag in ('thead', 'tfoot'):
        header += '<{}><tr><th>Module</th><th>Latest Version</th><th>Launcher Version</th>'.format(tag)
        for d in range(max_deps):
            header += DEPENDENCY_HEADERS.format(d + 1)
        header += '</tr></{}>'.format(tag)
    return header


def versions_from_cmd_dict(cmd_dict):
    versions = {}
    for cmd in cmd_dict:
        script, args = cmd_dict[cmd]
        module = cmd.module_name
        version = cmd.version
        versions[module] = version
    return versions


def get_launcher_versions(gen_cfg, module_cfg):
    mirror_root = gen_cfg.get('general', 'mirror_root')
    apps_xml = gen_cfg.get('launcher', 'apps_xml')
    new_apps_xml = gen_cfg.get('launcher', 'new_apps_xml')
    lxml = launcher.LauncherXml(apps_xml, new_apps_xml)
    cmds = lxml.get_cmds()
    cmd_dict = update_launcher.get_updated_cmds(cmds, module_cfg, mirror_root)
    launcher_versions = versions_from_cmd_dict(cmd_dict)
    return launcher_versions


def get_configure_ioc_versions(ioc_names):
    cfg_ioc = subprocess.check_output(CFG_IOC_CMD).strip().split('\n')
    ioc_paths = [path for _, path in (line.split() for line in cfg_ioc)]
    versions = {}
    for ioc_name in ioc_names:
        for ioc_path in ioc_paths:
            if ioc_name in ioc_path:
                if '/work/' in ioc_path:
                    versions[ioc_name] = 'work'
                else:
                    index = ioc_path.index(ioc_name)
                    end = ioc_path[index+len(ioc_name)+1:]
                    version = end.split(os.path.sep)[0]
                    versions[ioc_name] = version
    return versions


def sort_module_details(module_details):
    lines = []
    for module in sorted(module_details.keys()):
        mod_details = module_details[module]
        lines.append(mod_details)
    return lines


def start():
    gen_cfg, module_cfg = configuration.get_configs()
    launcher_versions = get_launcher_versions(gen_cfg, module_cfg)
    module_details = get_module_details(module_cfg, launcher_versions)
    max_deps = get_max_deps(module_details)
    table = sort_module_details(module_details)
    render(max_deps, table)


if __name__ == '__main__':
    start()
