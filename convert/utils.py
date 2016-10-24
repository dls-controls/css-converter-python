import os
import re
import stat
import logging as log
import string

EPICS_ROOT = '/dls_sw/prod/R3.14.12.3'
AREA_IOC = 'ioc'
AREA_SUPPORT = 'support'

VERSION_FILE = 'configure/VERSION'

PROJECT_TEMPLATE = 'res/project.template'
PROJECT_FILENAME = '.project'

IGNORE_DIR_IN_SEARCH = ('.svn', 'Db', 'bin', 'configure', 'data', 'db', 'dbd', 'etc', 'iocBoot', 'opi', 'src')
EXPECTED_DIR_IN_MODULE = ('bin', 'configure', 'data', 'db', 'etc')


class ConfigError(Exception):
    pass

VERSION_NUMBER_PATTERNS = [
        re.compile(r"(dls)[0-9]+[_\-\.][0-9]+.*"),# dls4-21beta
        re.compile(r"[0-9]+[_\-\.][0-9]+.*"),    # 4-21beta
        re.compile(r"[0-9]+[_\-\.](Run)[0-9]+.*") # 2015-Run2-4 (support/pgmNextGen_EPICS)
    ]


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
    all_paths = get_all_dirs(filepath)
    modules = set()

    for path in all_paths:
        try:
            _, module_name, _, relpath = parse_module_name(path)
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
        version = get_latest_version(os.path.join(root, area, module_name))
    else:
        log.debug("Using module version from config: %s", config_version)

    return version


def get_version(configuration_path):
    """ Read the current version number from the VERSION file in a fully
        qualified modulepath (e.g. /dls_sw/..../modulename/version)

        :return Version string (e.g. '4-2dls2')
    """
    version = ""
    path = os.path.join(configuration_path, VERSION_FILE)
    if os.path.exists(path):
        with open(path, 'r') as content_file:
            version = content_file.read()

    return version.rstrip()


def get_latest_version(filepath):
    """ Find the 'latest' version from a release directory containing version
        numbered folders.

        It simply finds the 'largest' tuple of numbered components so
            4-2 > 4-1
            5-4-2 > 5-4-1
            5-4-2 > 5-2-8
            5-4dls2 > 5-4dls1

    Args:
        filepath: Module path to search
    Returns:
        Largest version number
    Raises:
        ValueError if no versions are found in filepath
    """
    all_parts = []
    for root, dirs, _ in os.walk(filepath):
        for version in dirs:
            all_parts.append((parse_version(version), version))
        # only process the first level of the tree; this should contain the
        # release version folders
        break

    if all_parts:
        version_string = max(all_parts)[1]
    else:
        raise ValueError('No version found in %s' % filepath)

    return version_string


def parse_version(version_string):
    """ Convert version number string, containing test and numbers into a
        list of the integer parts

        Note: this is different to the parsing done in increment version as that
        keeps the non-numeric parts and is only interested in final number

    :param version_string: Version string to parse (e.g. dls1-2, 1-2, 1-4-2dls4)
    :return: numeric elements as list of values ordered as in the string (e.g. [1,4,2,4])
    """

    matches = re.findall('\d+\d*', version_string)
    return [int(m) for m in matches]


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
    for i, j in zip(parse_version(v1), parse_version(v2)):
        if i > j:
            return True
    return False


def get_all_dirs(filepath):
    """ Walk the file system from specified start point terminating at the iocBoot level

    :param filepath: Path to search
    :return: list of all child folders
    """
    all_paths = []
    for root, dirs, _ in os.walk(filepath):
        all_paths.extend([os.path.join(root, d) for d in dirs])
        # do not parse .svn, bin, etc directories
        for d in IGNORE_DIR_IN_SEARCH:
            try:
                dirs.remove(d)
            except ValueError:
                # raised if d not in dirs
                pass

    return all_paths


def find_module_from_path(filepath, top_dir=EPICS_ROOT):
    """ Crawl UP the file system to find the <module>/<version> folder containing
        the specified path.

        This is the same level as produced by get_all_dirs()
            e.g. /dls_sw/prod/R3.14.12.3/ioc/LI/TI/5-3

        If initial path is *above* this level no version will be included.

    :param filepath: path to search
    :param top_dir: top directory level: abort search here
    :return: filepath of module/version
    """

    test_path = filepath
    log.debug('Trying %s', test_path)

    while not get_all_dirs(test_path) and \
            os.path.abspath(test_path) != os.path.abspath(top_dir):
        test_path, _ = os.path.split(test_path)
        log.debug('Trying %s', test_path)

    return test_path


def is_version_number(candidate):
    """ Relatively crude pattern match of version numbers

    :param candidate: string to test as a possible version number
    :return: True if candidate is a version number
    """
    has_match = False
    # These are patterns that return a name from a filename
    for pattern in VERSION_NUMBER_PATTERNS:
        match = pattern.match(candidate)
        if match:
            has_match = True
            break

    return has_match


def parse_module_name(filepath):
    """
    Return (module_path, module_name, version, relative_path)

    If the path is not an ioc or a support module, raise ValueError.

    version may be None
    """
    log.debug('Parsing %s.', filepath)
    filepath = os.path.normpath(os.path.realpath(filepath))
    parts = filepath.split('/')
    version = None

    if AREA_SUPPORT in parts:
        root_index = parts.index(AREA_SUPPORT)
    elif AREA_IOC in parts:
        root_index = parts.index(AREA_IOC)
    else:
        raise ValueError('%s contains neither ioc nor support.' % filepath)

    v = None
    for i, p in enumerate(parts):
        if p == '':
            continue
        # Test for whether string represents a version.
        if is_version_number(p) or p == 'Rx-y':
            version = p
            v = i
    if v is None:
        module = '/'.join(parts[root_index+1:root_index+2])
        relative_path = '/'.join(parts[root_index+2:])
    else:
        module = '/'.join(parts[root_index+1:v])
        relative_path = '/'.join(parts[v+1:])

    module_path = '/'.join(parts[:root_index+1])
    if module == '':
        raise ValueError('No module found in %s' % filepath)

    return module_path, module, version, relative_path


def increment_version(version_string):
    """ Increment a version number, adding 1 to the final digit

        e.g. 1-4dls4 -> 1-4dls5, 4-2 -> 4-3

    :param version_string: current module version
    :return: incremented version
    """
    # Group parentheses required to include numbers in result.
    parts = re.split('([!0-9]*)', version_string)
    parts = [p for p in parts if p != '']
    last_number = parts.pop()
    try:
        new_version = str(int(last_number) + 1)
    except ValueError:
        # if last value is not a number will raise an error, so abort
        new_version = last_number

    parts.append(new_version)
    return ''.join(parts)


def make_read_only(filename, executable=False):
    """
    Remove write permissions from the file for everyone.
    """
    try:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
    except OSError:
        log.debug('Failed to make file %s read-only.', filename)


def make_writeable(filename):
    """
    Make the file writeable by the owner.
    """
    try:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IWUSR)
    except OSError:
        log.debug('Failed to make file %s writeable.', filename)


def read_conf_file(filename):
    """
    Read generic config file into list of lines.
    """
    with open(filename) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == '']
    return lines


def read_symbols_file(filename):
    """
    Read config file consisting of lines of the form:
    key: value
    Return a list of keys.  This is specifically useful for parsing
    our symbols configuration.
    """
    lines = read_conf_file(filename)
    symbols = [l.split(':')[0] for l in lines]
    return symbols


def generate_project_file(outdir, module_name, version):
    """
    Create an Eclipse project file for this set of OPIs.
    """
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    with open(os.path.join(outdir, PROJECT_FILENAME), 'w') as f:
        with open(PROJECT_TEMPLATE) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(module_name=module_name,
                                           version=version)
            f.write(updated_content)


def grep(filename, string):
    with open(filename) as f:
        for line in f:
            if string in line:
                return True

    return False
