import os
import stat
import logging as log
import dls_css_utils.utils as css_utils

EXPECTED_DIR_IN_MODULE = ('bin', 'configure', 'data', 'db', 'etc')


def find_modules(filepath):
    """ Find all modules in the given filepath.

        If path does not contain any IOCs or support modules returns [].
        If path does not exist returns [].

        "module" is determined as the path section between ioc/support and a
        version number, e.g.
            /dls_sw/prod/R3.14.12.3/support/zebra/2-0-1 => zebra
            /dls_sw/prod/R3.14.12.3/ioc/LI/TI/5-3 => LI/TI

    Args:
        filepath
    Returns:
        list of module_names
    """
    log.info('Finding all modules in: %s', filepath)
    all_paths = css_utils.get_all_dirs(filepath)
    modules = set()

    for path in all_paths:
        try:
            _, module_name, _, relpath = css_utils.parse_module_name(path)
            if relpath in EXPECTED_DIR_IN_MODULE:
                modules.add(module_name)
        except ValueError as ex:
            log.warn(ex.message)

    log.debug('Found modules %s', modules)

    return list(modules)


def get_module_version(root, area, module_name, config_version):
    """ Use "latest version" as determined from PROD file system, unless set
        explicitly in config file.

    :param config_version: explicit version number from ConfigFile (may be None)
    :param root: PROD root
    :param area: module area
    :param module_name: module name
    :return: Version number
    """
    version = config_version
    if version is None:
        log.debug("Finding module version from filesystem: %s", os.path.join(root, area, module_name))
        version = css_utils.get_latest_version(os.path.join(root, area, module_name))
    else:
        log.debug("Using module version from config: %s", config_version)

    return version


def newer_version(v1, v2):
    """ Determine if v1 is newer than v2.

    If the versions are equal, return False.
    If v1 is None, return False.
    If v1 is not None and v2 is None, return True.

    Args:
        v1: first version string to compare
        v2: second version string to compare

    Returns:
        True if v1 is newer than v2
    """
    if v1 is None:
        return False
    elif v2 is None:
        return True
    # Like zip() but substitute None if lengths don't match.
    for i, j in map(None, css_utils.parse_version(v1), css_utils.parse_version(v2)):
        if i > j:
            return True
    return False


def make_writeable(filename):
    """
    Make the file writeable by the owner.
    """
    try:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IWUSR)
    except OSError:
        log.debug('Failed to make file %s writeable.', filename)


def grep(filename, string):
    with open(filename) as f:
        for line in f:
            if string in line:
                return True

    return False


def find_opi_files(basepath):
    files = []
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                files.append(os.path.join(dirpath, filename))

    return files
