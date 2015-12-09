#!/usr/bin/env dls-python
"""
Post processing script to locate all the symbol widgets in converted
EDM panels and change them into DLS symbol widgets.
As part of the process, create the necessary PNG files.

Since this grabs screen attention, it can be run after all other conversion
steps are complete.
"""
from convert import configuration
from convert import coordinates
from convert import files
from convert import module
from convert import paths
from convert import utils

import os
import re
import logging as log
LOG_FORMAT = '%(levelname)s:%(pathname)s: %(message)s'
LOG_LEVEL = log.DEBUG
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
import xml.etree.ElementTree as et


SYMBOL_ID = 'org.csstudio.opibuilder.widgets.edm.symbolwidget'


def get_edl_dirs(mod):
    """ Find list of edl data files in all dependencies for the passed module

    :param mod: Module to search
    :return:
    """
    log.info("Fetching dependencies for %s", coordinates.as_path(mod.coords))
    dependencies = mod.get_dependencies()
    edl_dirs = [mod.get_edl_path()]
    for dep, dep_coords in dependencies.items():
        dep_cfg = configuration.get_config_section(all_cfg, dep)

        log.info("Dependency: %s", coordinates.as_path(dep_coords))
        dep_edl_path = os.path.join(mod.mirror_root,
                                    coordinates.as_path(dep_coords, False)[1:],
                                    utils.increment_version(dep_coords.version),
                                    dep_cfg['edl_dir'])
        edl_dirs.append(dep_edl_path)
    return edl_dirs


def edit_symbol_node(node, filename):
    """ Update the symbol XML node

        NOTE: the input 'node' argument is modified by this function!!
    :param node: Node to update
    :param filename: Image filename
    """
    size = int(re.findall('\d+', filename)[-1])
    log.info('New filename %s; size %s', filename, size)

    node.set('typeId', SYMBOL_ID)
    node.find('name').text = 'DLS symbol'

    pv_name = node.find('.//pv').text
    pv_element = et.Element('pv_name')
    pv_element.text = pv_name
    node.append(pv_element)

    rule_element = node.find('.//rule')
    rule_element.set('prop_id', 'pv_value')
    rule_element.set('out_exp', 'true')

    file_element = et.Element('image_file')
    file_element.text = filename

    num_element = et.Element('symbol_number')
    num_element.text = '0'

    img_size_element = et.Element('sub_image_width')
    img_size_element.text = str(size)

    node.append(file_element)
    node.append(num_element)
    node.append(img_size_element)
    node.remove(node.find('opi_file'))


def update_symbols(filename, depth, file_dict, all_cfg, prod_root, mirror_root):

    symbol_files = {}
    log.info('Updating symbols in %s depth %s', filename, depth)
    tree = et.parse(filename)
    root = tree.getroot()
    for widget in root.findall(".//widget[name='EDM Symbol']"):
        symbol_file = widget.find('opi_file').text
        try:
            smodule, _ = file_dict[symbol_file]
        except KeyError:
            continue

        if (symbol_file, smodule) in symbol_files:
            png_file = symbol_files[(symbol_file, smodule)]
        else:
            png_file = process_symbol(symbol_file, smodule, all_cfg,
                                      prod_root, mirror_root)
            symbol_files[(symbol_file, smodule)] = png_file
            file_dict[png_file] = (smodule, '')

        log.debug('Module for %s is %s', symbol_file, smodule)
        new_path = paths.update_opi_path(symbol_file, depth, file_dict, module, False)
        if png_file is not None:
            new_path = os.sep.join(os.path.split(new_path)[:-1] + (png_file,))
            edit_symbol_node(widget, new_path)

    tree.write(filename, encoding='utf-8', xml_declaration=True)


def build_filelist(basepath):
    """
    Grep on the basepath to find all files that contain an EDM
    symbol widget.
        control

    Arguments:
        basepath - root of search
    Returns:
        iterator over relative filepaths
    """
    log.info("Building list of files containing EDM symbols in %s", basepath)
    symbol_files = []
    for dir_path, _, file_names in os.walk(basepath):
        for filename in file_names:
            if filename.endswith(".opi") and utils.grep(os.path.join(dir_path, filename), "EDM Symbol"):
                symbol_files.append(os.path.join(dir_path, filename))

    return symbol_files


def process_symbol(name, mod, all_cfg, prod_root, mirror_root):
    """
    :param name:
    :param mod:
    :param all_cfg:
    :param prod_root:
    :param mirror_root:
    :return: PNG filename if successful, None if any error occurred
    """
    mod_cfg = configuration.get_config_section(all_cfg, mod)

    area = mod_cfg['area']
    working_path = os.path.join(mirror_root, prod_root[1:])
    mod_version = utils.get_module_version(working_path, area, mod, mod_cfg.get('version'))
    # version = utils.increment_version(version)
    log.debug("%s", working_path)
    log.warning("FOUND VERSION %s", mod_version)
    edl_path = mod_cfg['edl_dir']
    opi_path = mod_cfg['opi_dir']

    coords = coordinates.create(prod_root, area, mod, mod_version)
    mirror_path = os.path.join(mirror_root, coordinates.as_path(coords)[1:])
    full_path = os.path.join(mirror_path, edl_path, name[:-3] + 'edl')
    destination = os.path.dirname(os.path.join(mirror_path, opi_path, name))
    log.info('Destination directory is {}'.format(destination))
    if os.path.exists(destination):
        for f in os.listdir(destination):
            n = os.path.split(name)[1]
            n = '.'.join(n.split('.')[:-1])
            if f.startswith(n) and f.endswith('png'):
                log.info('Symbol png already exists: %s', f)
                return f
    else:
        log.warn('Failed to process symbol: %s does not exist', destination)
        return

    if os.path.exists(full_path):
        return files.convert_symbol(full_path, [destination])
    else:
        log.warn('Symbol %s does not exist', full_path)


if __name__ == '__main__':
    all_cfg = configuration.parse_configuration('conf/modules.ini')
    gen_cfg = configuration.parse_configuration('conf/converter.ini')
    mirror_root = gen_cfg.get('general', 'mirror_root')
    prod_root = gen_cfg.get('general', 'prod_root')
    symbol_opis = build_filelist(mirror_root)

    for opi_path in symbol_opis:
        _, mod_name, version, rel_path = utils.parse_module_name(opi_path)
        module_cfg = configuration.get_config_section(all_cfg, mod_name)
        area = module_cfg.get('area')

        # shadow_path = os.path.join(mirror_root, prod_root[1:])
        coords = coordinates.create(prod_root, area, mod_name, version)
        depth = len(os.path.split(rel_path))
        try:
            mod = module.Module(coords, module_cfg, mirror_root, increment_version=False)
            edl_dirs = get_edl_dirs(mod)

            file_dict = paths.index_paths(edl_dirs, True)
            update_symbols(opi_path, depth, file_dict,
                        all_cfg, prod_root, mirror_root)
        except ValueError as e:
            log.warn('Error updating symbols in %s: %s', mod_name, e)