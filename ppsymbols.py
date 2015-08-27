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
    print('Filename {}; size {}'.format(filename, size))
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
    log.warn('Updating symbols in %s', filename)
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
        log.info('Module for %s is %s', symbol_file, smodule)
        new_path = paths._update_opi_path(symbol_file, 1,
                                          file_dict, module, False)
        if png_file is not None:
            print('New path: {}'.format(new_path))
            new_path = os.sep.join(os.path.split(new_path)[:-1] + (png_file,))
            print('New path: {}'.format(new_path))
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
    print('name is {}'.format(name))
    mod_cfg = configuration.get_config_section(cfg, mod)
    area = mod_cfg['area']
    version = mod_cfg['version']
    if version is None:
        version = utils.get_latest_version(os.path.join(prod_root, area, mod))
    version = utils.increment_version(version)
    edl_path = mod_cfg['edl_dir']
    opi_path = mod_cfg['opi_dir']
    coords = coordinates.create(prod_root, area, mod, version)
    print(edl_path, name)
    print(coords)
    print(coordinates.as_path(coords))
    mirror_path = os.path.join(mirror_root, coordinates.as_path(coords)[1:])
    full_path = os.path.join(mirror_path, edl_path, name[:-3] + 'edl')
    destination = os.path.join(mirror_path, opi_path, name)
    print('Destination is {}'.format(destination))
    try:
        for f in os.listdir(os.path.dirname(destination)):
            n = os.path.split(name)[1]
            n = '.'.join(n.split('.')[:-1])
            if f.startswith(n) and f.endswith('png'):
                print('Destination already exists: {}'.format(f))
                return f
    except OSError as e:
        print('Failed: {}'.format(e))
    if os.path.exists(full_path):
        return files.convert_symbol(full_path, [destination])
    else:
        log.warn('Symbol %s does not exist', full_path)


if __name__ == '__main__':
    filename = '/tmp/symbols/old_sym.opi'
    all_cfg = configuration.parse_configuration('conf/modules.ini')
    gen_cfg = configuration.parse_configuration('conf/converter.ini')
    mirror_root = gen_cfg.get('general', 'mirror_root')
    prod_root = gen_cfg.get('general', 'prod_root')
    symbol_opis = build_filelist(mirror_root)
    for opi_path in symbol_opis:
        r, m, v, rp = utils.parse_module_name(opi_path)
        cfg = configuration.get_config_section(all_cfg, m)
        version = cfg.get('version')
        if version is None:
            version = utils.get_latest_version(os.path.join(prod_root,
                                                            cfg['area'], m))
        coords = coordinates.create(prod_root, cfg['area'], m, version)
        mod = module.Module(coords, cfg, mirror_root)
        edl_dirs = get_edl_dirs(mod)

        file_dict = paths.index_paths(edl_dirs, True)
        update_symbols(opi_path, file_dict, coords.module,
                       all_cfg, prod_root, mirror_root)
