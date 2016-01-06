import colourtweak
import files
import groups
import layers
import mmux
import utils

import os
import shutil
import dependency
import coordinates
import paths
import logging as log


EDL_EXTENSION = 'edl'
OPI_EXTENSION = 'opi'


class Module(object):
    """Object representing one IOC or support module."""

    def __init__(self, coords, cfg_dict, mirror_root, increment_version=True):
        """

        Args:
            coords: source module coordinates
            cfg_dict: general config info -- extra deps, edl and opi dirs
            mirror_root: root of target filesystem
        """
        self.coords = coords
        self.edl_dir = cfg_dict['edl_dir']
        self.opi_dir = cfg_dict['opi_dir']
        # Relative paths within self.opi_dir
        self.path_dirs = cfg_dict['path_dirs']
        self.extra_deps = coordinates.update_version_from_files(cfg_dict['extra_deps'], self.coords.root)
        print('module.py: extra_deps {}'.format(self.extra_deps))
        self.layers = cfg_dict['layers']
        self.groups = cfg_dict['groups']
        self.mirror_root = mirror_root
        # Used for locating a file in module and dependencies given
        # only its name.
        self.file_dict = {}
        # Used for locating an executable given only its name.
        self.path_dict = {}

        if increment_version:
            self.new_version = utils.increment_version(coords.version)
        else:
            self.new_version = coords.version

        prod_path = coordinates.as_path(coords, False)
        # prod_path[1:] strips leading / to allow creation of shadow
        # file system INSIDE a containing dir /.../dls_sw/prod/R3...
        self.conversion_root = os.path.join(mirror_root, prod_path[1:],
                                            self.new_version)

        if not os.path.exists(self.conversion_root) and cfg_dict['has_opi']:
            err_msg = 'Module to be converted does not exist: {}'
            raise ValueError(err_msg.format(self.conversion_root))

        self.layer_files = self._build_files(self.layers)
        self.group_files = self._build_files(self.groups)

    def get_dependencies(self):
        """
        Returns:
            dict {name: coords} for all module dependencies
        """
        dp = dependency.DependencyParser(self.coords, self.extra_deps)
        return dp.find_dependencies()

    def get_path_dirs(self):
        """
        Returns:
            List of paths relative to self.opi_dir
        """
        return self.path_dirs

    def get_opi_path(self):
        """
        Returns:
            Full path to converted OPI files directory
        """
        opi_path = os.path.join(self.conversion_root, self.opi_dir)
        return os.path.normpath(opi_path)

    def get_edl_path(self):
        """
        Returns:
            Full path to edl file directory
        """
        edl_path = os.path.join(self.conversion_root, self.edl_dir)
        return os.path.normpath(edl_path)

    def _build_files(self, part_paths):
        """ Build a list of all files referenced by the partial paths relative
            to an EDL path root

        Args:
            part_paths: Relative paths to generate

        Returns:
            List of file paths based on configuration EDL path
        """
        root = self.get_edl_path()
        file_list = []
        for part in part_paths:
            f = os.path.join(root, part)
            if os.path.exists(f):
                file_list.append(f)

        return file_list

    def convert(self, force):
        """Convert entire module.

        Args:
            force: Reconvert if destination exists
        """
        origin = self.get_edl_path()
        destination = self.get_opi_path()
        try:
            os.makedirs(destination)
        except OSError:
            # directory already exists
            pass

        self._convert_all(origin, destination, force)

    def __str__(self):
        return 'Module at coordinates {}'.format(self.coords)

    def _convert_one(self, source, target, depth, force):
        """ Convert a single file.

            If this is not an EDL file it is copied to the target path,
            otherwise:
                - OPI created
                - paths updated
                - [layer post process]
                - [group post process]

            Layer and group post process performed only on files listed in the
            layers and groups sections of the modules configuration file

            File metadata is preserved for non-EDL files

        Args:
            source: source file (relative path)
            target: target file (relative path)
            depth: file 'depth' relative to eclipse link base
            force: if True, force reconversion and copy
        """
        log.debug('Handling file: %s to %s', source, target)
        edl_file = source.endswith(EDL_EXTENSION)
        if edl_file:
            target = target[:-len(EDL_EXTENSION)] + OPI_EXTENSION

        target_exists = os.path.exists(target)
        if not force and target_exists:
            log.info('Skipping existing file {}'.format(target))
        else:
            if edl_file:
                if files.convert_edl(source, target):
                    paths.update_opi_file(target, depth, self.file_dict,
                                          self.coords.module, use_rel=False)
                    paths.update_opi_file(target, depth, self.path_dict,
                                          self.coords.module, use_rel=True)
                    if self.is_layer_file(source):
                        layers.parse(target)
                    if self.is_group_file(source):
                        groups.parse(target)
                    colourtweak.parse(target)
                    if utils.grep(target, mmux.MENU_MUX_ID):
                        mmux.parse(target)
            else:
                try:
                    # don't attempt to copy a file onto itself
                    if source != target:
                        # if not writable before copy an error will be raised
                        # and file will not update
                        if target_exists:
                            utils.make_writeable(target)

                        shutil.copy2(source, target)
                except shutil.Error as e:
                    log.warn('Error trying to copy {}: {}'.format(source, e))

    def is_layer_file(self, f):
        """Determine if file requires post-process 'layer' manipulation.

        Args:
            f: File path to check

        Returns:
            True if file appears in list of Layer files
        """
        return f in self.layer_files

    def is_group_file(self, f):
        """ Determine if file requires post-process 'group' manipulation.

        Args:
            f: File path to check

        Returns:
            True if file appears in list of Group files
        """
        return f in self.group_files

    def _convert_all(self, origin, destination, force):
        """Copy each file in origin to destination:
            * if .edl, convert it to .opi
            * ignore .svn directories
        """
        old_edl_files = []
        log.info('Converting %s to %s', origin, destination)
        if not os.path.exists(destination):
            raise ValueError('Destination directory {} does not exist'.format(destination))
        if not os.path.exists(origin):
            raise ValueError('Origin directory {} does not exist'.format(origin))

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

            for f in filenames:
                source = os.path.join(dirpath, f)  # full path for source
                rel = os.path.relpath(source, origin)  # relative path for target
                target = os.path.join(destination, rel)  # full path for target
                eclipse_path = os.path.join(self.coords.module, rel)
                depth = len(eclipse_path.split(os.sep)) - 1
                log.debug('The depth for %s in %s is %s', rel, self.coords.module, depth)

                try:
                    self._convert_one(source, target, depth, force)
                except files.OldEdlError:
                    log.warn('Skipping old edl file %s', source)
                    old_edl_files.append(source)

        return old_edl_files
