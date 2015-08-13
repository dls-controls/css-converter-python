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


def handle_one_file(origin, destination, module, depth, file_index, force):
    log.debug('Handling file: %s to %s', origin, destination)
    edl_file = origin.endswith(EDL_EXTENSION)
    if edl_file:
        destination = destination[:-len(EDL_EXTENSION)] + OPI_EXTENSION
    if not force and os.path.exists(destination):
        log.info('Skipping existing file {}'.format(destination))
    else:
        if edl_file:
            files.convert_edl(origin, destination)
            paths.update_opi_file(destination, depth, file_index, module)
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
            depth = len(r.split(os.sep))
            try:
                handle_one_file(o, d, module, depth, file_index, force)
            except files.OldEdlError:
                log.warn('Skipping old edl file %s', o)
                old_edl_files.append(o)

    return old_edl_files


class Module(object):

    def __init__(self, coords, datadir, opidir, mirror_root):
        self.coords = coords
        self.datadir = datadir
        self.opidir = opidir
        self.old_version = coords.version
        self.module_dir = coordinates.as_path(coords, False)
        if not os.path.exists(self.module_dir):
            raise ValueError('Cannot locate module {} at {}'.format(coords.name,
                                                                    self.module_dir))

        self.mirror_root = mirror_root
        self.new_version = utils.increment_version(self.old_version)

    def get_dependencies(self):
        dp = dependency.DependencyParser(self.coords)
        return dp.find_dependencies()

    def get_datadir(self):
        return os.path.join(self.module_dir, self.old_version, self.datadir)

    def get_file_dict(self, datadir):
        # For all files return a dictionary
        # {filename: (module, path-within-module)}
        # This allows us to find any edl file by name
        datapath = os.path.join(self.module_dir, self.old_version, datadir)
        file_dict = {}
        for dirname, dirs, filenames in os.walk(datapath):
            for f in filenames:
                relpath = os.path.relpath(os.path.join(dirname, f), datapath)
                file_dict[f] = self.coords.module, relpath

        return file_dict

    def convert(self, file_index, force):
        new_root = os.path.join(self.mirror_root, self.module_dir[1:], self.new_version)
        origin = new_root if self.datadir == '.' else os.path.join(new_root, self.datadir)
        destination = os.path.join(new_root, self.opidir)
        try:
            os.makedirs(destination)
        except OSError:
            # directory already exists
            pass
        convert_all(origin, destination, self.coords.module, file_index, force)

