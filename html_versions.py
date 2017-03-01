#!/usr/bin/env dls-python
"""
Inspired by Tom's /dls/cs-www/reports/scripts/list_ioc_support_modules.py
"""

import pkg_resources
pkg_resources.require('jinja2')
pkg_resources.require('dls_css_utils')

import collections
import jinja2
import logging as log
import os
import subprocess
import shutil

from convert import configuration, launcher, spoof, utils
from dls_css_utils import coordinates, dependency, utils as css_utils

LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.WARNING
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


SUPPORT_PATH = os.path.join(css_utils.EPICS_ROOT, css_utils.AREA_SUPPORT)
IOC_PATH = os.path.join(css_utils.EPICS_ROOT, css_utils.AREA_IOC)
RESOURCES_DIR = 'res'
HTML_TEMPLATE = 'template.html'
JSON_TEMPLATE = 'template.json'
MODULE_TEMPLATE = 'module_template.html'
MODULE_PAGE = 'modules.html'
REPORT_DIR = 'html'
REPORT = 'deps.json'
CFG_IOC_CMD = ["configure-ioc", "l"]


class ModDetails(object):
    # CSS classes
    OK = 'ok'
    OUT_OF_DATE = 'out-of-date'
    CONFIGURED = 'configured'
    NO_RELEASE = 'no-release'
    NO_DEPS = 'no-deps'
    # Informational messages
    CONFIGURED_MSG = 'The latest version is specified in modules.ini'
    OUT_OF_DATE_MSG = 'Latest version {}; the older version is in modules.ini'

    def __init__(self, name, requested=None, latest_release=None,
                 config_version=None, launcher_version=None,
                 cfg_ioc_version=None, deps=None):
        self.name = name
        self.requested = requested
        self.latest_release = latest_release
        self.config_version = config_version
        self.launcher_version = launcher_version
        self.cfg_ioc_version = cfg_ioc_version
        self.deps = {} if deps is None else deps
        self.version_class = ModDetails.OK
        self.version_message = ""
        self.launcher_version_class = ModDetails.OK
        self.cfg_ioc_version_class = ModDetails.OK
        self.requested_version_class = ModDetails.OK
        self.deps_class = ModDetails.OK if self.deps else ModDetails.NO_DEPS
        self._assess_versions()

    def _assess_versions(self):
        """ Set variables that describe the state of each assigned version.

        These are used as CSS classes in the HTML.
        """
        if self.config_version is not None:
            if utils.newer_version(self.latest_release, self.config_version):
                self.version_class = ModDetails.OUT_OF_DATE
                msg = ModDetails.OUT_OF_DATE_MSG.format(self.latest_release)
                self.version_message = msg
            else:
                self.version_class = ModDetails.CONFIGURED
                self.version_message = ModDetails.CONFIGURED_MSG
        if self.launcher_version is not None:
            if utils.newer_version(self.latest_release, self.launcher_version):
                self.launcher_version_class = ModDetails.OUT_OF_DATE
        if self.cfg_ioc_version is not None:
            if utils.newer_version(self.latest_release, self.cfg_ioc_version):
                self.cfg_ioc_version_class = ModDetails.OUT_OF_DATE
        if self.requested is not None:
            if self.latest_release is None:
                self.requested_version_class = ModDetails.NO_RELEASE
            elif utils.newer_version(self.latest_release, self.requested):
                self.requested_version_class = ModDetails.OUT_OF_DATE
        for md in self.deps.values():
            if utils.newer_version(md.latest_release, md.requested):
                self.deps_class = ModDetails.OUT_OF_DATE
                break


def get_versions(module_cfg, coords):
    try:
        latest_release = css_utils.get_latest_version(coordinates.as_path(coords,
                                                                      False))
    except ValueError:
        latest_release = None
    config_version = module_cfg.version
    return latest_release, config_version


def find_iocs():
    """Returns a list of IOC names e.g. 'LI/TI' """
    return utils.find_modules(IOC_PATH)


def find_support_modules():
    """Returns a list of support module names e.g. 'diagOpi' """
    return os.listdir(SUPPORT_PATH)


def handle_one_module(module_name, module_cfg, launcher_version, cfg_ioc_version, area):
    coords = coordinates.ModCoord(css_utils.EPICS_ROOT, area, module_name, None)
    latest_release, config_version = get_versions(module_cfg, coords)
    if config_version is not None:
        vcoords = coordinates.update_version(coords, config_version)
    else:
        vcoords = coordinates.update_version(coords, latest_release)

    log.debug('Dependencies of {} plus {}'.format(vcoords, module_cfg.extra_deps))
    dp = dependency.DependencyParser.from_coord(vcoords, additional_depends=module_cfg.extra_deps)
    deps = dp.find_dependencies()
    log.debug('{}: {}, {}'.format(module_name, latest_release, config_version))

    # Sort dependencies by module name so that they render in order.
    version_deps = collections.OrderedDict()
    for dep_coord in sorted(deps.values(), key=lambda d: d.module):
        # find versions here too.
        dep_latest, dep_cfg = get_versions(module_cfg, dep_coord)
        dep_requested = dep_coord.version
        dmd = ModDetails(dep_coord.module, requested=dep_requested,
                         latest_release=dep_latest, config_version=dep_cfg)
        version_deps[dep_coord.module] = dmd
        log.debug('{}: {}, {}'.format(dep_coord.module, dep_latest, dep_cfg))

    md = ModDetails(module_name, requested=None,
                    latest_release=latest_release,
                    config_version=config_version,
                    launcher_version=launcher_version,
                    cfg_ioc_version=cfg_ioc_version,
                    deps=version_deps)
    return md


def get_launcher_versions(gen_cfg):
    """Determine where possible versions of modules used in the launcher.

    Returns:
        dict: module name => version string
    """
    launcher_versions = {}
    apps_xml = gen_cfg.apps_xml
    new_apps_xml = gen_cfg.new_apps_xml
    lxml = launcher.LauncherXml(apps_xml, new_apps_xml)
    cmds = lxml.get_cmds()
    for cmd in cmds:
        try:
            cmd.interpret()
            # Have to change this back, which is a bit awkward.
            cmd.module_name = cmd.module_name.replace('_', '/')
            launcher_versions[cmd.module_name] = cmd.version
        except (spoof.SpoofError, ValueError):
            log.debug('Failed to understand command {}'.format(cmd.cmd))

    return launcher_versions


def get_configure_ioc_versions(module_names):
    """Determine where possible versions of modules used in configure-ioc.

    Returns:
        dict: module name => version string or 'work'
    """
    cfg_ioc = subprocess.check_output(CFG_IOC_CMD).strip().split('\n')
    cfg_ioc_paths = [path for _, path in (line.split() for line in cfg_ioc)]
    versions = {}
    for module_name in module_names:
        for ioc_path in cfg_ioc_paths:
            if module_name in ioc_path:
                if '/work/' in ioc_path:
                    versions[module_name] = 'work'
                else:
                    index = ioc_path.index(module_name)
                    end = ioc_path[index+len(module_name)+1:]
                    version = end.split(os.path.sep)[0]
                    versions[module_name] = version
    return versions


def get_module_details(gen_cfg):
    """Locate all support modules and iocs and return their dependencies.

    Returns:
        List of ModDetails objects
    """
    support_modules = find_support_modules()
    cfg_ioc_versions = get_configure_ioc_versions(support_modules)
    launcher_versions = get_launcher_versions(gen_cfg)
    iocs = find_iocs()
    cfg_ioc_versions.update(get_configure_ioc_versions(iocs))

    module_details = []
    for modules, area in ((support_modules,  css_utils.AREA_SUPPORT),
                          (iocs, css_utils.AREA_IOC)):
        for module in modules:
            launcher_version = launcher_versions.get(module, None)
            cfg_ioc_version = cfg_ioc_versions.get(module, None)
            module_cfg = gen_cfg.get_mod_cfg(module)
            try:
                module_details.append(handle_one_module(module, module_cfg,
                                                        launcher_version,
                                                        cfg_ioc_version, area))
            except AssertionError as e:
                log.warn('Failed to process module {}: {}'.format(module, e))

    return module_details


def render(mod_details, env, template):
    """Use jinja2 to render a string from the provided environment.

    Args:
        mod_details: List of ModDetails objects
        env: jinja2 environment to use
    Returns:
        rendered string
    """
    # The largest number of dependencies for any one module
    max_deps = max(len(details.deps) for details in mod_details)
    # Sort by module name
    sorted_details = sorted(mod_details, key=lambda md: md.name)
    template = env.get_template(template)
    header_tags = ['thead', 'tfoot']
    full_string = template.render(header_tags=header_tags,
                                  nheaders=max_deps,
                                  mod_details=sorted_details)
    return full_string


def create_page(mod_details, env, template):
    """Use jinja2 to render a string from the provided environment.

    Args:
        mod_details: List of ModDetails objects
        env: jinja2 environment to use
    Returns:
        rendered string
    """
    # Sort by module name
    sorted_details = sorted(mod_details.deps)
    template = env.get_template(template)
    full_html = template.render(name=mod_details.name,
                                mod_details=sorted_details)
    return full_html


def start():
    gen_cfg = configuration.GeneralConfig()
    module_details = get_module_details(gen_cfg)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(RESOURCES_DIR))
    out = render(module_details, env, JSON_TEMPLATE)
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)
    shutil.copy2(os.path.join(RESOURCES_DIR, MODULE_PAGE), REPORT_DIR)
    for m in module_details:
        mod_page = create_page(m, env, MODULE_TEMPLATE)
        page_name = m.name.replace('/', '-')
        with open(os.path.join(REPORT_DIR, '{}.html'.format(page_name)), 'w') as f:
            f.write(mod_page)
    report_location = os.path.join(REPORT_DIR, REPORT)
    with open(report_location, 'w') as f:
        f.write(out)
    print('Created HTML report: {}'.format(REPORT))


if __name__ == '__main__':
    start()
