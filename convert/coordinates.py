from collections import namedtuple
import os

from convert import utils

__author__ = 'xzl80115'

ModCoord = namedtuple('ModCoord', 'root, area, module, version')


def from_path(filepath):
    """ Separate a file path into:
            root = File location (e.g. /dls_sw/prod/R3.14.12.3)
            area = [ioc / support]
            module = path between <area> and <version> may include multiple chunks
            version =

        Note: If filepath is not correctly structured, i.e.
            <root>/<area>/<module>/<version>
        this method WILL NOT correctly determine it's composition!

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
    if area not in ("ioc", "support"):
        module = os.path.join(area, module)
        root, area = os.path.split(root)

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
    :param version: version string (e.g. 4-2dls2) [optional]
    :return:
    """
    return ModCoord(root, area, module, version)


def create_rootless(area, module, version):
    """ Generate a coordinate tuple for a module or file with NO ROOT DEFINED

        Coordinates generated with this constructor will raise a ValueError if
        to_path is called

    :param area: "ioc" or "support"
    :param module: path between <area> and <version>
    :param version: version string (e.g. 4-2dls2)
    :return:
    """
    return ModCoord(None, area, module, version)


def update_version(coord, version):
    """ Generate a new coordinate with updated version
    :param coord: Base coordinate
    :param version: New version to set
    :return: New coord
    """
    return create(coord.root, coord.area, coord.module, version)


def update_root(coord, root):
    """ Generate a new coordinate with a modified root
    :param coord: Base coordinate
    :param root: New root to set
    :return: New coord
    """
    return create(root, coord.area, coord.module, coord.version)


def as_path(coord, include_version=True):
    """ Convert a module coordinate object to a file path

    Args:
        coord: Coordinate to interpret

    Returns:
        Full path to module
    """
    if coord.root is None:
        raise ValueError("Cannot find path of coord with no root", coord)

    if coord.version is None or not include_version:
        path = os.path.join(coord.root, coord.area, coord.module)
    else:
        path = os.path.join(coord.root, coord.area, coord.module, coord.version)

    return path


def update_version_from_files(coords, root):
    """ If any of the coordinates in the list do not have a specific version
        get the latest version and update the coord with that version.

    Args:
        deps: list of rootless coordinates, some of which may have None
              as a version
        root: filesystem root in which to look for versions
    """
    updated_coords = []
    for coord in coords:
        if coord.version is None:
            latest_version = utils.get_latest_version(os.path.join(root, coord.area, coord.module))
            updated_dep = update_version(coord, latest_version)
            updated_coords.append(updated_dep)
        else:
            updated_coords.append(coord)

    return updated_coords
