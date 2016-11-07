#!/usr/bin/env dls-python

import pkg_resources
pkg_resources.require('dls_css_utils')

import logging as log
import os
import sys

from convert import arguments, files, module, paths, configuration, utils
from dls_css_utils import coordinates, run_script, config

LOG_FORMAT = '%(levelname)s:%(pathname)s: %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def get_modules(args, gen_cfg, area):
    """Return either one or all modules for specified area.

    Args:
        args: conversion arguments (uses .all and .module)
        module_cfg: configuration containing area
        gen_cfg: configuration containing general/prod_root and general/mirror_root
        area: 'ioc' or 'support'

    Returns:
        list of Module objects
    """
    modules = []

    root = gen_cfg.prod_root
    mirror = gen_cfg.mirror_root

    if args.all:
        mirror_root_dir = os.path.join(mirror, root[1:])
        log.info("Searching for all '{}' modules in {} for conversion...".format(area, mirror_root_dir))
        all_mods = utils.find_modules(os.path.join(mirror_root_dir, area))

        log.info("Found: {}".format(', '.join(all_mods)))
    else:
        log.info("Converting single '%s' module: %s", area, args.module)
        all_mods = [args.module]

    for module_name in all_mods:
        module_cfg = gen_cfg.get_mod_cfg(module_name)
        version = utils.get_module_version(root, area, module_name, module_cfg.version)
        coords = coordinates.create(root, area, module_name, version)
        modules.append(module.Module(coords, module_cfg, mirror))

    return modules


def file_dict_to_path_dict(file_dict, path_dirs):
    """Create a dict for locating executables originally on EDM path.

    Because the EDM path variable is treated differently to EDMDATAFILES,
    this dict needs the filename as the key.

    Args:
        file_dict: used for indexing opi files
        path_dirs: a list of dirs on EDM path relative to opi dir

    Returns:
        path_dict: filename: (module, path-relative-to-opi-dir)
    """
    path_dict = {}
    for old_key, old_value in file_dict.items():
        for path in path_dirs:
            path = path.strip(os.path.sep)
            if old_key.startswith(path):
                mod, _ = old_value
                new_key = os.path.relpath(old_key, path)
                path_dict[new_key] = (mod, path)
    return path_dict


def convert_module(mod, gen_cfg, force):
    extra_depends = []
    dependencies = mod.get_dependencies()
    edl_dirs = [mod.get_edl_path()]
    path_dirs = mod.get_path_dirs()
    for dep, dep_coords in dependencies.items():
        dep_cfg = gen_cfg.get_mod_cfg(dep)
        new_version = utils.increment_version(dep_coords.version)
        dep_edl_path = os.path.join(gen_cfg.mirror_root,
                                    coordinates.as_path(dep_coords, False)[1:],
                                    new_version,
                                    dep_cfg.edl_dir)
        edl_dirs.append(dep_edl_path)
        for p in dep_cfg.path_dirs:
            dep_path = os.path.join(gen_cfg.mirror_root,
                                    coordinates.as_path(dep_coords, False)[1:],
                                    new_version,
                                    p)
            path_dirs.append(dep_path)
        mod_deps = dep_cfg.extra_deps
        updated_mod_deps = coordinates.update_version_from_files(mod_deps, mod.coords.root)
        extra_depends.append(updated_mod_deps)

    mod.file_dict = paths.index_paths(edl_dirs, True)
    # path_dict is a reshaped subset of file_dict
    mod.path_dict = file_dict_to_path_dict(mod.file_dict, path_dirs)
    try:
        mod.convert(force)
        new_version = utils.increment_version(mod.coords.version)
        run_script.generate(mod.coords, new_version, gen_cfg.mirror_root,
                            opi_dir=mod.opi_dir, converter_config=gen_cfg,
                            extra_depends=extra_depends)
    except ValueError as e:
        log.warn('Conversion of %s failed:', mod)
        log.warn('%s', e)


def already_converted(mod):
    """ If the module has a module.ini file that contains an opi-location key,
    assume that the module has already been converted.

    Returns:
        True if opi-location key is found.
    """
    converted = False
    try:
        module_config = config.parse_module_config(coordinates.as_path(mod.coords))
        if config.opi_path(module_config) is not None:
            converted = True
    except config.ConfigError:
        pass # file not found
    return converted


def prepare_conversion(mod, gen_cfg, force):
    """Convert files in one module.

    Args:
        mod: module (object) to convert
        gen_cfg: parsed module configuration
        force: force conversion
    """
    log.info('Preparing conversion of module %s', mod)
    mod_cfg = gen_cfg.get_mod_cfg(mod.coords.module)

    if not force and already_converted(mod):
        log.info('Skipping conversion, module %s already converted.', mod)
    elif mod_cfg.has_opi:
        convert_module(mod, gen_cfg, force)
    else:
        log.info('Skipping conversion, no OPIs in module %s', mod)


def start_conversion():
    args = arguments.parse_arguments()
    gen_cfg = configuration.GeneralConfig(args.general_config, args.module_config)
    area = utils.AREA_IOC if args.ioc else utils.AREA_SUPPORT

    if not os.path.exists(files.JAVA):
        log.fatal('Cannot find java executable {}'.format(files.JAVA))
        sys.exit()

    if not os.path.exists(files.JAR_FILE):
        log.fatal('Cannot find jar file {}'.format(files.JAR_FILE))
        sys.exit()

    try:
        modules = get_modules(args, gen_cfg, area)
    except ValueError as e:
        log.fatal('Failed to load modules: %s', e)
        sys.exit()

    try:
        for mod in modules:
            prepare_conversion(mod, gen_cfg, args.force)
    except config.ConfigError as e:
        log.fatal('Incorrect configuration: %s', e)
        log.fatal('System will exit.')

if __name__ == '__main__':
    start_conversion()
