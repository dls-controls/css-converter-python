from collections import namedtuple
import os

from convert import utils

__author__ = 'xzl80115'

ModCoord = namedtuple('ModCoord', 'root, area, module, version')


def from_path(filepath):
    """ Separate a file path into:
            root = File location (e.g. /dls_sw/prod/R3.14.12.3)
            area = [ioc / support]
            module = path between <area> and <version>
            version = may be None

    :param filepath: Filepath to split
    :return: ModCoord
    """
    # try to get module path
    ## WIP: attempt to stip the 'it's a file' case
    if not os.path.isdir(filepath):
        filepath = utils.find_module_from_path(filepath)

    base, version = os.path.split(filepath)
    base, module = os.path.split(base)
    root, area = os.path.split(base)

    return create(root, area, module, version)


def from_path2(filepath):
    mp, m, v, rp = utils.parse_module_name(filepath)
    root, area = os.path.split(mp)
    return create(root, area, m, v)


def create(root, area, module, version=None):
    """ Generate a coordinate tuple for a module or file
    :param root: File location (e.g. /dls_sw/prod/R3.14.12.3)
    :param area: "ioc" or "support"
    :param module: path between <area> and <version>
    :param version:
    :return:
    """
    return ModCoord(root, area, module, version)


def as_path(coord, include_version=True):
    """ Convert a module coordinate object to a file path

    :param coord: Coordinate to interpret
    :return: Full path to module
    """
    if coord.version is None or not include_version:
        path = os.path.join(coord.root, coord.area, coord.module)
    else:
        path = os.path.join(coord.root, coord.area, coord.module, coord.version)

    return path
