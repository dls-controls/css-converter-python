import pkg_resources
import build_runcss

pkg_resources.require('dls_epicsparser')

import os
import sys

from convert import module, utils, coordinates, paths, arguments, configuration

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


def get_modules(args, gen_cfg, area):
    """
    :param args: conversion arguments (uses .all and .module)
    :param module_cfg: configuration containing area
    :param gen_cfg: configuration containing general/prod_root and general/mirror_root
    :return: list of Modules
    """
    modules = []

    root = gen_cfg.get('general', 'prod_root')
    mirror = gen_cfg.get('general', 'mirror_root')

    if args.all:
        all_mods = utils.find_modules(os.path.join(root, area))
    else:
        all_mods = [args.module]

    for module_name in all_mods:
        module_cfg = configuration.get_config_section(cfg, module_name)
        # use latest version unless set explicitly in config file
        version = module_cfg.get('version')
        if version is None:
            version = utils.get_latest_version(os.path.join(root, area, module_name))

        coords = coordinates.create(root, area, module_name, version)
        modules.append(module.Module(coords, module_cfg, mirror))

    return modules


def convert_one_module(mod, cfg, mirror_root):
    """
    :param mod: module (object) to convert
    :param cfg: parsed modules configuration
    :param mirror_root: base bath for converted files
    """
    log.info('Preparing conversion of module %s', mod)
    dependencies = mod.get_dependencies()
    edl_dirs = [mod.get_edl_path()]
    for dep, dep_coords in dependencies.items():
        new_version = utils.increment_version(dep_coords.version)
        dep_cfg = configuration.get_config_section(cfg, dep)
        dep_edl_path = os.path.join(mirror_root,
                                coordinates.as_path(dep_coords, False)[1:],
                                new_version,
                                dep_cfg['edl_dir'])
        edl_dirs.append(dep_edl_path)

    file_dict = paths.index_paths(edl_dirs, True)
    try:
        mod.convert(file_dict, args.force)

        new_version = utils.increment_version(mod.coords.version)
        build_runcss.gen_run_script(mod.coords,
                                    new_version,
                                    mirror_root,
                                    mod.get_opi_path(),
                                    cfg)
    except ValueError as e:
        log.warn('Conversion of %s failed:', mod)
        log.warn('%s', e)

if __name__ == '__main__':
    args = arguments.parse_arguments()
    gen_cfg = configuration.parse_configuration(args.general_config)
    cfg = configuration.parse_configuration(args.module_config)
    area = utils.AREA_IOC if args.ioc else utils.AREA_SUPPORT
    mirror_root = gen_cfg.get('general', 'mirror_root')

    try:
        modules = get_modules(args, gen_cfg, area)
    except ValueError as e:
        log.fatal('Failed to load modules: %s', e)
        sys.exit()

    try:
        for mod in modules:
            convert_one_module(mod, cfg, mirror_root)
    except utils.ConfigError as e:
        log.fatal('Incorrect configuration: %s', e)
        log.fatal('System will exit.')
