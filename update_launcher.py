#!/usr/bin/env dls-python
"""
Script that iterates over the items in the Launcher's applications.xml file
and converts any commands it determines to be running EDM to equivalent
commands to run a CSS screen.

Updates are only made if the converted CSS screen is located in the
mirror filesystem.
"""
from __future__ import print_function
from convert import configuration
from convert import launcher

import sys
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def summarise_updates(cmd_dict):
    """Log all the entries in the cmd_dict.

    This is useful to show which conversions have been picked up by the
    launcher update.

    Args:
        cmd_dict: command object => (path, [args])
    """
    print('', file=sys.stderr)
    if cmd_dict:
        log.info('The following launcher items have been updated:\n')
        for item in cmd_dict:
            log.info('    %s:%s', item.name, cmd_dict[item])
    else:
        log.info('No launcher items have been updated.')
    print('', file=sys.stderr)


def update_xml():
    """
    Parse configuration files, create a LauncherXml object and use its
    command objects to determine the new commands.

    Write the new commands back to a new XML file.
    """
    cfg = configuration.GeneralConfig()
    lxml = launcher.LauncherXml(cfg.apps_xml, cfg.new_apps_xml)
    cmds = lxml.get_cmds()
    cmd_dict = launcher.get_updated_cmds(cmds, cfg)
    lxml.write_new(cmd_dict)
    summarise_updates(cmd_dict)
    print('Wrote new launcher XML file to {}\n'.format(cfg.new_apps_xml), file=sys.stderr)


if __name__ == '__main__':
    update_xml()
