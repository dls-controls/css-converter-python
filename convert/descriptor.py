from collections import namedtuple
import os
from convert.utils import find_module_from_path

__author__ = 'xzl80115'

ModCoord = namedtuple('ModCoord', 'root, area, module, version')

def generate_coord(filepath):
    """ Separate a filepath into:
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
        filepath = find_module_from_path(filepath)

    base, version = os.path.split(filepath)
    base, module = os.path.split(base)
    root, area = os.path.split(base)

    return create_coordinate(root, area, module, version)

def create_coordinate(root, area, module, version=None):
    """ Generate a coordinate tuple for a module or file
    :param root: File location (e.g. /dls_sw/prod/R3.14.12.3)
    :param area: "ioc" or "support"
    :param module: path between <area> and <version>
    :param version:
    :return:
    """
    return ModCoord(root, area, module, version)
