import utils
import files
import os
import shutil
import dependency
import coordinates
import paths
import logging as log


EDL_EXTENSION = 'edl'
OPI_EXTENSION = 'opi'


def handle_one_file(origin, destination, depth, module, file_index, force):
    log.debug('Handling file: %s to %s', origin, destination)
    edl_file = origin.endswith(EDL_EXTENSION)
    if edl_file:
        destination = destination[:-len(EDL_EXTENSION)] + OPI_EXTENSION
    if not force and os.path.exists(destination):
        log.info('Skipping existing file {}'.format(destination))
    else:
        if edl_file:
            files.convert_edl(origin, destination)
            paths.update_opi_file(destination, depth, file_index,
                                  module, use_rel=False)
        else:
            try:
                shutil.copy2(origin, destination)
            except IOError as e:
                log.warn('Error trying to copy {}: {}'.format(origin, e))


def convert_all(origin, destination, module, file_index, force):
    """
    Copy each file in origin to destination:
        * if .edl, convert it to .opi
        * ignore .svn directories
    """
    old_edl_files = []
    log.debug('Converting %s to %s', origin, destination)
    if not os.path.exists(destination):
        raise ValueError('Destination directory {} does not exist'.format(destination))
    # Flatten list, otherwise creating directories while iterating
    # causes an infinite loop.
    walklist = list(os.walk(origin))
    for dirpath, dirnames, filenames in walklist:
        log.debug('Reached directory %s %s %s', dirpath, dirnames, filenames)
        if '.svn' in dirpath:
            continue
        # Create mirror directory
        relpath = os.path.relpath(dirpath, origin)
        log.debug('relpath is %s', relpath)
        if relpath != '.':
            try:
                os.mkdir(os.path.join(destination, relpath))
            except OSError:
                pass
        # Full paths for each file
        originpaths = [os.path.join(dirpath, f) for f in filenames]
        log.debug('The origin paths are %s', originpaths)
        # Paths relative to origin for each file
        relpaths = [os.path.relpath(os.path.join(dirpath, f), origin) for f in filenames]
        # Destination paths for each file
        destpaths = [os.path.join(destination, rp) for rp in relpaths]
        log.debug('The destination paths are %s', destpaths)
        for o, d, r in zip(originpaths, destpaths, relpaths):
            eclipse_path = os.path.join(module, r)
            depth = len(eclipse_path.split(os.sep)) - 1
            log.debug('The depth for %s in %s is %s', r, module, depth)
            try:
                handle_one_file(o, d, depth, module, file_index, force)
            except files.OldEdlError:
                log.warn('Skipping old edl file %s', o)
                old_edl_files.append(o)

    return old_edl_files


class Module(object):

    def __init__(self, coords, edl_dir, opi_dir, mirror_root, extra_deps):
        """

        :param coords: source module co-ord
        :param edl_dir: directory in module to convert edl files from
        :param opidir: directory in module to store converted opi files
        :param mirror_root: root of target filesystem
        """
        self.coords = coords
        self.edl_dir = edl_dir
        self.opi_dir = opi_dir
        self.mirror_root = mirror_root
        self.extra_deps = extra_deps

        self.new_version = utils.increment_version(coords.version)
        self.new_module_dir = os.path.join(coordinates.as_path(coords, False),
                                           self.new_version)

    def get_dependencies(self):
        """
        :return: List of coords of all module dependencies
        """
        dp = dependency.DependencyParser(self.coords, self.extra_deps)
        return dp.find_dependencies()

    def get_edl_path(self):
        """
        :return: Full path to edl file directory
        """
        return os.path.join(self.mirror_root, self.new_module_dir[1:], self.edl_dir)

    def convert(self, file_dict, force):
        """

        :param file_dict: filename -> (module,path-in-module)
        :param force: Reconvert if destination exists
        :return:
        """
        # self.new_module_dir[1:] strips leading / to allow creation of shadow
        # file system INSIDE a containing dir /../dls_sw/prod/R3...
        new_root = os.path.join(self.mirror_root, self.new_module_dir[1:])

        if self.edl_dir == '.':
            origin = new_root
        else:
            origin = os.path.join(new_root, self.edl_dir)

        destination = os.path.join(new_root, self.opi_dir)
        try:
            os.makedirs(destination)
        except OSError:
            # directory already exists
            pass
        convert_all(origin, destination, self.coords.module, file_dict, force)
