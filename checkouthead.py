#!/usr/bin/env dls-python
'''
Input: IOC name, mirror root.
Output: checkout IOC and dependencies to mirror location.
'''
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
    try:
        os.makedirs(mirror_location)
    except OSError:
        log.info('%s already present at %s; skipping', name, mirror_location)
        return

    module_type = utils.AREA_IOC if 'ioc' in path else utils.AREA_SUPPORT
    module_name = name if name is not None else ''

    if git:
        vcs_location = os.path.join(GIT_ROOT, module_type, module_name)
        ret_val = subprocess.call(['git', 'clone', vcs_location, mirror_location])
    else:
        vcs_location = os.path.join(SVN_ROOT, TRUNK, module_type, module_name)
        ret_val = subprocess.call(['svn', 'checkout', vcs_location, mirror_location])
        # call returns '1' if the SVN checkout 'fails'
        if ret_val != 0:
            log.error("SVN checkout of %s/%s failed. Module may have moved to Git", module_type, module_name)

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


def checkout_coords(coords, cfg, include_deps=True, extra_deps=None, force=False):
    log.info('Checking out module at: %s', coords)
    log.info('Extra dependencies: %s', extra_deps)
    if include_deps:
        dp = dependency.DependencyParser(coords, additional_depends=extra_deps)
        log.info('Finding dependencies of %s', coords)
        to_checkout = dp.find_dependencies()
    else:
        to_checkout = {}

    to_checkout[coords.module] = coords

    for module, mcoords in to_checkout.items():
        try:

            dep_cfg = cfg.get_mod_cfg(mcoords.module)

            if not dep_cfg.has_opi:
                log.info('Skipping checkout of module with no OPIs: %s/%s (%s)',
                            mcoords.area, mcoords.module, mcoords.version)
                continue

            new_version = utils.increment_version(mcoords.version)
            log.info('Updated version %s/%s: %s', mcoords.area, mcoords.module, new_version)
            new_coords = coordinates.update_version(mcoords, new_version)

            new_path = coordinates.as_path(new_coords)
            checkout_path = os.path.join(cfg.mirror_root, new_path[1:])
            if force and os.path.exists(checkout_path):
                log.info('Removing %s before checking out', new_path)
                shutil.rmtree(checkout_path)

            checkout_module(new_coords.module, new_version, new_path,
                            cfg.mirror_root, dep_cfg.is_git())

            if not opi_dir_is_empty(checkout_path, dep_cfg):
                log.warning("Files may be overwritten in conversion - module OPI directory exists (%s).", checkout_path)

            extra_deps = coordinates.update_version_from_files(
                dep_cfg.extra_deps, coords.root)
            configuration.create_module_ini_file(
                new_coords, cfg.mirror_root, dep_cfg.opi_dir, extra_deps, force)

        except ValueError:
            log.warn('Cannot handle coordinates %s', mcoords)
    log.info('Finished checking out all modules.')


def opi_dir_is_empty(checkout_path, dep_cfg):
    """ Determine if the opi directory used in the conversion exists and is
        non-empty

    Args:
        checkout_path: Full path to module (in shadow file system)
        dep_cfg: Module configuration, including opi_dir

    Returns:
        False if directory exists and is not empty
    """
    mirror_location = os.path.join(checkout_path, dep_cfg.opi_dir)
    files = []
    try:
        files = os.listdir(mirror_location)
    except OSError:
        # thrown if path doesn't exist
        pass

    # not <empty> is True, not <non-empty> is False
    return not files


if __name__ == '__main__':
    args = arguments.parse_arguments()
    cfg = configuration.GeneralConfig(args.general_config, args.module_config)
    area = utils.AREA_IOC if args.ioc else utils.AREA_SUPPORT

    if args.all:
        log.info("Searching for all '%s' modules for checkout.", area)
        all_mods = utils.find_modules(os.path.join(cfg.prod_root, area))
        log.info('Dependency checkout suppressed')
        get_depends = False
    else:
        all_mods = [args.module]
        get_depends = True

    for mod in all_mods:
        module_cfg = cfg.get_mod_cfg(mod)
        version = utils.get_module_version(
            cfg.prod_root, area, mod, module_cfg.version)
        coords = coordinates.create(cfg.prod_root, area, mod, version)
        versioned_deps = coordinates.update_version_from_files(
            module_cfg.extra_deps, cfg.prod_root)

        mod_path = coordinates.as_path(coords)
        if os.path.exists(mod_path):
            checkout_coords(coords, cfg, get_depends, versioned_deps, args.force)
        else:
            log.error("Module doesn't exist: {}".format(mod_path))
