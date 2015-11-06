"""
Script that iterates over the items in the Launcher's applications.xml file
and converts any commands it determines to be running EDM to equivalent
commands to run a CSS screen.

Updates are only made if the converted CSS screen is located in the
mirror filesystem.
"""
#!/usr/bin/env dls-python
from convert import configuration
from convert import launcher
from convert import spoof
from convert import utils
import os

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.WARNING
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def update_cmd(cmd_dict, mirror_root):
    '''
    Attempt to convert an EDM command into the appropriate command
    to run the equivalent CSS screen.

    Args:
        cmd_dict: a convert.launcher.LauncherCommand objects
        mirror_root: path to root of mirror filesystem

    Returns:
        (path, [args]): where
             - path is the path of the runcss.sh script
             - args is one string: the opi to run followd by any macros
    '''
    cmd.interpret()
    p, n, v, rp = utils.parse_module_name(cmd.path_to_run)
    # Switch back to edl extension
    edl_rp = rp[:-3] + 'edl'
    nv = utils.increment_version(v)
    updated_edl_path = os.path.join(p, n, nv, edl_rp)
    path_to_module = os.path.join(mirror_root, p[1:], n, nv)
    mirror_path = os.path.join(mirror_root, updated_edl_path[1:])
    if os.path.exists(mirror_path):  # Module has been checked out
        cfg = configuration.get_config_section(module_cfg, n)
        edl_dir = os.path.normpath(os.path.join(path_to_module, cfg['edl_dir']))
        opi_dir = os.path.normpath(os.path.join(path_to_module, cfg['opi_dir']))
        # Filepath relative to EDMDATAFILES directory
        rel_path = os.path.relpath(mirror_path, edl_dir)
        runcss_path = os.path.join(opi_dir, 'runcss.sh')
        if os.path.exists(opi_dir):
            run_opi = rel_path[:-3] + 'opi'
            macros = ','.join('{}={}'.format(a, b) for a, b in cmd.macros.items())
            return runcss_path, ['{} {}'.format(run_opi, macros)]
    else:
        log.warning('No mirror path %s; xml not updated', mirror_path)


if __name__ == '__main__':

    module_cfg = configuration.parse_configuration('conf/modules.ini')
    gen_cfg = configuration.parse_configuration('conf/converter.ini')
    mirror_root = gen_cfg.get('general', 'mirror_root')
    apps_xml = gen_cfg.get('launcher', 'apps_xml')
    new_apps_xml = gen_cfg.get('launcher', 'new_apps_xml')
    lxml = launcher.LauncherXml(apps_xml, new_apps_xml)
    cmds = lxml.get_cmds()
    cmd_dict = {}
    for cmd in cmds:
        try:
            new_cmd = update_cmd(cmd, mirror_root)
            if new_cmd is not None:
                cmd_dict[cmd] = new_cmd
        except (spoof.SpoofError, ValueError, TypeError) as e:
            log.info('Failed interpreting command {}: {}'.format(cmd.cmd, e))
    lxml.write_new(cmd_dict)
    print('Wrote new launcher XML file to {}'.format(new_apps_xml))
