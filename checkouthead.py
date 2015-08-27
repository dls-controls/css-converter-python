#!/usr/bin/env dls-python
'''
Input: IOC name, mirror root.
Output: checkout IOC and dependencies to mirror location.
'''
import pkg_resources
pkg_resources.require('dls_epicsparser')

from convert import arguments
from convert import coordinates
from convert import configuration
from convert import dependency
from convert import utils
import os
import shutil
import subprocess

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

SVN_ROOT = 'svn+ssh://serv0002.cs.diamond.ac.uk/home/subversion/repos/controls'
TRUNK = 'diamond/trunk'

GIT_ROOT = 'ssh://dascgitolite@dasc-git.diamond.ac.uk/controls'


def checkout_module(name, version, path, mirror_root, git):
    mirror_location = os.path.join(mirror_root, path[1:])
    module_type = utils.AREA_IOC if 'ioc' in path else utils.AREA_SUPPORT
    module_name = name if name is not None else ''
    try:
        os.makedirs(mirror_location)
    except OSError:
        log.info('%s already present at %s; skipping', name, mirror_location)
        return
    if git:
        vcs_location = os.path.join(GIT_ROOT, module_type, module_name)
        ret_val = subprocess.call(['git', 'clone', vcs_location, mirror_location])
    else:
        vcs_location = os.path.join(SVN_ROOT, TRUNK, module_type, module_name)
        ret_val = subprocess.call(['svn', 'checkout', vcs_location, mirror_location])
    log.info('Checkout %s to %s', vcs_location, mirror_location)
    # Drop VERSION file into configure directory
    configure_dir = os.path.join(mirror_location, 'configure')
    try:
        os.mkdir(configure_dir)
    except OSError:
        # configure directory is in SVN
        pass

    with open(os.path.join(configure_dir, 'VERSION'), 'w') as f:
        f.write(version)
        f.write('\n')

    if ret_val == 0:
        current_dir = os.curdir
        try:
            os.chdir(mirror_location)
            subprocess.call(['make'])
        finally:
            os.chdir(current_dir)


def checkout_coords(coords, mirror_root, include_deps=True, extra_deps=None,
                    force=False):
    log.info('Coordinates: %s', coords)
    log.info('Extra dependencies: %s', extra_deps)
    if include_deps:
        dp = dependency.DependencyParser(coords, extra_deps)
        to_checkout = dp.find_dependencies()
    else:
        to_checkout = {}

    to_checkout[coords.module] = coords

    for module, mcoords in to_checkout.items():
        try:
            new_version = utils.increment_version(mcoords.version)
            log.info('New version %s', new_version)
            new_coords = coordinates.update_version(mcoords, new_version)
            new_path = coordinates.as_path(new_coords)
            if force:
                log.info('Removing %s before checking out', new_path)
                shutil.rmtree(os.path.join(mirror_root, new_path[1:]))

            dep_cfg = configuration.get_config_section(cfg, new_coords.module)
            checkout_module(new_coords.module, new_version, new_path,
                            mirror_root, dep_cfg.get('vcs') == 'git')

            configuration.create_module_ini_file(new_coords, mirror_root,
                    dep_cfg.get('opi_dir'), dep_cfg.get('extra_deps'), force)

        except ValueError:
            log.warn('Cannot handle coordinates %s', mcoords)
    log.info('Finished checking out all modules.')

if __name__ == '__main__':
    args = arguments.parse_arguments()

    gen_cfg = configuration.parse_configuration(args.general_config)
    cfg = configuration.parse_configuration(args.module_config)
    area = utils.AREA_IOC if args.ioc else utils.AREA_SUPPORT

    prod_root = gen_cfg.get('general', 'prod_root')
    mirror_root = gen_cfg.get('general', 'mirror_root')

    if args.all:
        log.info("Searching for all '%s' modules for checkout.", area)
        all_mods = utils.find_modules(os.path.join(prod_root, area))
        log.info('Dependency checkout suppressed')
        get_depends = False
    else:
        all_mods = [args.module]
        get_depends = True

    for mod in all_mods:
        module_cfg = configuration.get_config_section(cfg, mod)
        coords = coordinates.create(prod_root, area, mod)
        if module_cfg.get('version') is not None:
            version = module_cfg.get('version')
        else:
            version = utils.get_latest_version(coordinates.as_path(coords))
        full_coords = coordinates.update_version(coords, version)

        checkout_coords(full_coords, mirror_root, get_depends,
                        module_cfg.get('extra_deps', []),
                        args.force)
