#!/usr/bin/env dls-python
import build_runcss

import os
import sys

from convert import module, utils, coordinates, paths, arguments, configuration

import logging as log
LOG_FORMAT = '%(levelname)s:%(pathname)s: %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def get_modules(args, gen_cfg, cfg, area):
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

    root = gen_cfg.get('general', 'prod_root')
    mirror = gen_cfg.get('general', 'mirror_root')

    if args.all:
        mirror_root_dir = os.path.join(mirror, root[1:])
        log.info("Searching for all '{}' modules in {} for conversion...".format(area, mirror_root_dir))
        all_mods = utils.find_modules(os.path.join(mirror_root_dir, area))

        log.info("Found: {}".format(', '.join(all_mods)))
    else:
        log.info("Converting single '%s' module: %s", area, args.module)
        all_mods = [args.module]

    for module_name in all_mods:
        module_cfg = configuration.get_config_section(cfg, module_name)
        version = utils.get_module_version(root, area, module_name, module_cfg.get('version'))
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
                module, _ = old_value
                new_key = os.path.relpath(old_key, path)
                path_dict[new_key] = (module, path)
    return path_dict


def convert_one_module(mod, cfg, mirror_root):
    """Convert files in one module.

    Args:
        mod: module (object) to convert
        cfg: parsed module configuration
        mirror_root: base bath for converted files
    """
    log.info('Preparing conversion of module %s', mod)
    mod_config = configuration.get_config_section(cfg, mod.coords.module)
    extra_depends = []

    if configuration.has_opis(mod_config):
        dependencies = mod.get_dependencies()
        edl_dirs = [mod.get_edl_path()]
        path_dirs = mod.get_path_dirs()
        for dep, dep_coords in dependencies.items():
            dep_cfg = configuration.get_config_section(cfg, dep)
            new_version = utils.increment_version(dep_coords.version)
            dep_edl_path = os.path.join(mirror_root,
                                    coordinates.as_path(dep_coords, False)[1:],
                                    new_version,
                                    dep_cfg['edl_dir'])
            edl_dirs.append(dep_edl_path)
            for p in dep_cfg['path_dirs']:
                dep_path = os.path.join(mirror_root,
                                        coordinates.as_path(dep_coords, False)[1:],
                                        new_version,
                                        p)
                path_dirs.append(dep_path)
            extra_depends.append(dep_cfg.get('extra_deps', []))

        mod.file_dict = paths.index_paths(edl_dirs, True)
        # path_dict is a reshaped subset of file_dict
        mod.path_dict = file_dict_to_path_dict(mod.file_dict, path_dirs)
        try:
            mod.convert(args.force)

            new_version = utils.increment_version(mod.coords.version)
            build_runcss.gen_run_script(mod.coords,
                                        new_version,
                                        prefix=mirror_root,
                                        opi_dir=mod.get_opi_path(),
                                        config=cfg,
                                        extra_depends=extra_depends)
        except ValueError as e:
            log.warn('Conversion of %s failed:', mod)
            log.warn('%s', e)
    else:
        log.info('Skipping conversion, no OPIs in module %s', mod)


if __name__ == '__main__':
    args = arguments.parse_arguments()
    gen_cfg = configuration.parse_configuration(args.general_config)
    cfg = configuration.parse_configuration(args.module_config)
    area = utils.AREA_IOC if args.ioc else utils.AREA_SUPPORT
    mirror_root = gen_cfg.get('general', 'mirror_root')

    try:
        modules = get_modules(args, gen_cfg, cfg, area)
    except ValueError as e:
        log.fatal('Failed to load modules: %s', e)
        sys.exit()

    try:
        for mod in modules:
            convert_one_module(mod, cfg, mirror_root)
    except utils.ConfigError as e:
        log.fatal('Incorrect configuration: %s', e)
        log.fatal('System will exit.')
