"""
Inspired by Tom's /dls/cs-www/reports/scripts/list_ioc_support_modules.py
"""

from convert import configuration
from convert import coordinates
from convert import dependency
from convert import launcher
from convert import utils
import update_launcher

import os
from collections import namedtuple
import string
import ConfigParser
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.WARNING
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

SUPPORT = '/dls_sw/prod/R3.14.12.3/support'
IOC = '/dls_sw/prod/R3.14.12.3/ioc'
HTML_TEMPLATE = 'res/template.html'
REPORT = 'deps.html'

# HTML templates
DEPENDENCY_HEADERS = '<th class="dep-col">Dependency {}</th><th>Requested Version</th>'
DEPENDENCY_CELLS = '<td class="dep-col">{name}</td><td title="Latest version {latest}" class="{req_class}">{requested}</td>'
EMPTY_DEP_CELLS = '<td class="dep-col"></td><td></td>'
MODULE_CELLS = '<tr><td>{name}</td><td class="{version_class}">{latest}</td><td class="{lversion_class}">{lversion}</td>'

# CSS classes
OUT_OF_DATE = 'out-of-date'
CONFIGURED = 'configured'

# Named tuple to store details about a module, versions and dependencies.
ModDetails = namedtuple('ModDetails', 'name, requested, latest_release, config_version, launcher_version, deps')

# Start with support modules.


def get_config():
    gen_cfg = configuration.parse_configuration('conf/converter.ini')
    module_cfg = configuration.parse_configuration('conf/modules.ini')
    return gen_cfg, module_cfg


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


def handle_one_module(module_cfg, module_name, launcher_version, area):
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
        version_deps[dep_coord] = ModDetails(dep_coord.module, dep_requested,
                                             dep_latest, dep_cfg,
                                             launcher_version, None)
        log.debug('{}: {}, {}'.format(dep_coord.module, dep_latest, dep_cfg))

    return ModDetails(module_name, None, latest_release, config_version,
                      launcher_version, version_deps)


def get_deps(module_cfg, cmd_dict):
    """Locate all support modules and iocs and return their dependencies.

    Returns:
        dict mapping module name (e.g. 'LI/TI') to dict of dependencies.
    """
    support_modules = find_support_modules()
    iocs = find_iocs()

    module_details = {}
    for module in support_modules:
        launcher_version = cmd_dict.get(module, None)
        print('Launcher version {}'.format(launcher_version))
        try:
            module_details[module] = handle_one_module(module_cfg, module, launcher_version, 'support')
        except AssertionError as e:
            print(e.__class__)
            log.warn('Failed on {}: {}'.format(module, e))

    for module in iocs:
        launcher_version = cmd_dict.get(module, None)
        try:
            module_details[module] = handle_one_module(module_cfg, module, launcher_version, 'ioc')
        except AssertionError as e:
            print(e.__class__)
            log.warn('Failed on {}: {}'.format(module, e))

    return module_details


def render(table_headers, table_content):
    with open(HTML_TEMPLATE) as f:
        html = f.read()
        template = string.Template(html)
        full_html = template.substitute(headers=table_headers,
                                        table=table_content)
    with open(REPORT, 'w') as f:
        f.write(full_html)


def table_line(mod_details, max_deps):
    subs = {'name': mod_details.name,
            'latest': mod_details.latest_release,
            'config': mod_details.config_version,
            'lversion': mod_details.launcher_version,
            'version_class': 'ok',
            'lversion_class': 'ok'}
    if mod_details.config_version is not None:
        if utils.newer_version(mod_details.latest_release,
                               mod_details.config_version):
            subs['version_class'] = OUT_OF_DATE
        else:
            subs['version_class'] = CONFIGURED
    if mod_details.launcher_version is not None:
        if utils.newer_version(mod_details.latest_release,
                               mod_details.launcher_version):
            subs['lversion_class'] = OUT_OF_DATE
    line = MODULE_CELLS.format(**subs)
    for dep in mod_details.deps:
        mod_version = mod_details.deps[dep]
        dep_subs = {'name': mod_version.name,
                    'latest': mod_version.latest_release,
                    'requested': mod_version.requested,
                    'req_class': 'ok'}
        if utils.newer_version(mod_version.latest_release, mod_version.requested):
            dep_subs['req_class'] = OUT_OF_DATE
        line += DEPENDENCY_CELLS.format(**dep_subs)
    for i in range(max_deps - len(mod_details.deps)):
        line += EMPTY_DEP_CELLS
    line += '</tr>'
    return line


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


def generate_table(module_details, max_deps):
    lines = []
    for module in sorted(module_details.keys()):
        mod_details = module_details[module]
        lines.append(table_line(mod_details, max_deps))
    return '\n'.join(lines)


def start():
    gen_cfg, module_cfg = get_config()
    launcher_versions = get_launcher_versions(gen_cfg)
    module_details = get_deps(module_cfg, launcher_versions)
    max_deps = get_max_deps(module_details)
    print('Max dependencies: {}'.format(max_deps))
    headers = generate_headers(max_deps)
    table = generate_table(module_details, max_deps)
    render(headers, table)

if __name__ == '__main__':
     start()
