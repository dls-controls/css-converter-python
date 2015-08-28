#!/usr/bin/env dls-python
"""
Post processing script to locate all the symbol widgets in converted
EDM panels and change them into DLS symbol widgets.
As part of the process, create the necessary PNG files.

Since this grabs screen attention, it can be run after all other conversion
steps are complete.
"""
import pkg_resources
pkg_resources.require('dls_epicsparser')
from convert import configuration
from convert import coordinates
from convert import files
from convert import module
from convert import paths
from convert import utils

import os
import re
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
import xml.etree.ElementTree as et


SYMBOL_ID = 'org.csstudio.opibuilder.widgets.edm.symbolwidget'


def get_edl_dirs(module):
    dependencies = mod.get_dependencies()
    edl_dirs = [mod.get_edl_path()]
    for dep, dep_coords in dependencies.items():
        new_version = utils.increment_version(dep_coords.version)
        dep_cfg = configuration.get_config_section(all_cfg, dep)
        dep_edl_path = os.path.join(mirror_root,
                                    coordinates.as_path(dep_coords, False)[1:],
                                    new_version,
                                    dep_cfg['edl_dir'])
        edl_dirs.append(dep_edl_path)
    return edl_dirs


def edit_symbol_node(node, filename):
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


def update_symbols(filename, file_dict, module, cfg, prod_root, mirror_root):

    symbol_files = {}
    log.info('Updating symbols in %s', filename)
    tree = et.parse(filename)
    root = tree.getroot()
    for widget in root.findall(".//widget[name='EDM Symbol']"):
        symbol_file = widget.find('opi_file').text
        try:
            smodule, spath = file_dict[symbol_file]
        except KeyError:
            continue
        if (symbol_file, smodule) in symbol_files:
            png_file = symbol_files[(symbol_file, smodule)]
        else:
            png_file = process_symbol(symbol_file, smodule, spath,
                                      cfg, prod_root, mirror_root)
            symbol_files[(symbol_file, smodule)] = png_file
            file_dict[png_file] = (smodule, '')
        log.debug('Module for %s is %s', symbol_file, smodule)
        new_path = paths.update_opi_path(symbol_file, 1, file_dict, module, False)
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
    log.info("Building list of files containing EDM symbols.")
    files = []
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                if utils.grep(os.path.join(dirpath, filename), "EDM Symbol"):
                    files.append(os.path.join(dirpath, filename))

    return files


def process_symbol(name, mod, path, cfg, prod_root, mirror_root):
    mod_cfg = configuration.get_config_section(cfg, mod)
    area = mod_cfg['area']
    version = mod_cfg['version']
    if version is None:
        version = utils.get_latest_version(os.path.join(prod_root, area, mod))
    version = utils.increment_version(version)
    edl_path = mod_cfg['edl_dir']
    opi_path = mod_cfg['opi_dir']
    coords = coordinates.create(prod_root, area, mod, version)
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
        _, mod_name, _, _ = utils.parse_module_name(opi_path)
        module_cfg = configuration.get_config_section(all_cfg, mod_name)
        area = module_cfg.get('area')
        version = utils.get_module_version(prod_root, area, mod_name, module_cfg.get('version'))
        coords = coordinates.create(prod_root, area, mod_name, version)

        mod = module.Module(coords, module_cfg, mirror_root)
        edl_dirs = get_edl_dirs(mod)

        file_dict = paths.index_paths(edl_dirs, True)
        update_symbols(opi_path, file_dict, coords.module,
                       all_cfg, prod_root, mirror_root)
