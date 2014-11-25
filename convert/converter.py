#!/usr/bin/env dls-python
"""
Simple python script to find and convert EDM .edl files into CSS
.opi files. It uses conv.jar, built from the latest version
of the OPIBuilder converter (as of March 2014).

    java -jar conv.jar <filename> <destination>

It also uses edm to convert old-style files into new style files
if necessary:

    edm -convert <filename>

Since this function automatically puts the file in the same directory,
it copies the EDM files to a tmp directory first.

Steps:
 - if file is .edl file, try and convert
  - if conversion fails, it may be an old-style .edl file
  - try converting using edm, then converting again
 - if file is a different type, copy across directly
"""

import utils
import paths
import files

import os
import glob
import shutil
import string

import logging as log

OPI_EXT = 'opi'
EDL_EXT = 'edl'


class ConfigurationError(Exception):
    """ Customer exception to be raised in there is a config-file parse
        error
    """
    pass


class Converter(object):
    """
    Given a script used to start EDM, deduce the directories needed
    for conversion and convert them in the appropriate format.
    Output goes in the directory provided.

    Since we can't easily determine symbol files, these may be specified
    on creation.
    """

    def __init__(self, dirs, symbol_files, root_outdir):
        """
        Given the EDM entry script, deduce the paths to convert.
        A list of symbol files is stored to help when converting.
        """
        self.dirs = dirs
        self.file_index = paths.index_paths(dirs, True)

        self.symbol_files = symbol_files
        self.symbol_dict = {}

        self.root_outdir = root_outdir

        if not os.path.exists(self.root_outdir):
            log.info('Making new output directory %s', self.root_outdir)
            os.makedirs(self.root_outdir)

    def _process_one_directory(self, datadir, entry, force, working_path):
        """ Process a single directory
        """
        # ignore hidden directories
        if not entry.startswith('.'):
            full_path = os.path.join(datadir, entry)
            log.debug("New full path is %s", full_path)

            if os.path.isdir(full_path):
                outpath = os.path.join(working_path, entry)
                log.debug("New outdir is %s", outpath)
                self._convert_dir(full_path, outpath, force)

    def get_symbol_paths(self):
        return self.symbol_dict

    def convert(self, force):
        """
        Given the EDM datafiles and PATH lists, parse the directory and
        any subdirectories for edm/script files.  Create output in a similar
        directory structure.
        """
        for datadir in self.dirs:
            # Currently can't handle relative directories.
            if datadir.startswith('.'):
                continue
            log.debug('EDM data file %s', datadir)
            try:
                module_path, module_name, version, rel_path = utils.parse_module_name(datadir)
            except ValueError:
                log.warn("Can't parse path %s", datadir)
                continue

            log.debug("%s %s %s", module_name, version, rel_path)
            if rel_path is None:
                rel_path = ''
            module_name = module_name.split('/')[-1]
            log.debug('The module name path is %s', module_name)
            entries = os.listdir(datadir)
            working_path = os.path.join(self.root_outdir, module_name, rel_path)
            for entry in entries:
                self._process_one_directory(datadir, entry, force, working_path)

            self._convert_dir(datadir, working_path, force)

    def _is_symbol(self, filename):
        """
        Return True if:
         - the opi file name ends with 'symbol.edl'
         - the opi file name is included in self.symbol_files
        """
        return filename.endswith('symbol.edl') or \
            os.path.basename(filename) in self.symbol_files

    def _already_converted(self, outdir, file):
        """
        Return True if:
         - there is already a converted file in the destination
         - there is a png of the right name in place of a symbol file
        """
        basename = os.path.basename(file)
        base = '.'.join(basename.split('.')[:-1])
        if self._is_symbol(file):
            # look for the converted png
            return len(glob.glob(os.path.join(outdir, base) + '*.png'))
        else:
            opifile = basename[:-len(EDL_EXT)] + OPI_EXT
            destination = os.path.join(outdir, opifile)
            return os.path.exists(destination)

    def _convert_one_file(self, full_path, outdir, force):
        """
        Apppropriately convert one edl file, including updating
        any relative paths using the file_index dict.
        """
        # Figure out the 'depth' of the file.  This is how many 
        # nested directories any relative path must descend before
        # adding the relative path back on.
        relative_dir = os.path.relpath(outdir, self.root_outdir)
        depth = len(relative_dir.strip('/').split('/'))
        # change extension
        name = os.path.basename(full_path)
        opifile = name[:-len(EDL_EXT)] + OPI_EXT
        destination = os.path.join(outdir, opifile)
        try:
            if not force and self._already_converted(outdir, full_path):
                log.info('Skipping existing file %s', destination)
            elif self._is_symbol(full_path):
                # symbols are not converted here; conversion is postponed
                # until the end of the script to reduce focus-grabbing
                # machine distruption
                store_symbol(full_path, destination, self.symbol_dict)
                log.info('Successfully stored symbol file %s', destination)
            else:
                returncode = files.convert_edl(full_path, destination)
                if returncode == 0:
                    log.info('Successfully converted %s', destination)
                    self.update_paths(destination, depth)
                else:
                    log.warn('Conversion of %s failed with code %d.',
                             full_path, returncode)
        except Exception as e:
            log.warn('Conversion of %s unsuccessful.', full_path)
            log.warn(str(e))

    def _copy_one_file(self, full_path, outdir, force):
        executable = os.access(full_path, os.X_OK)
        name = os.path.basename(full_path)
        destination = os.path.join(outdir, name)
        if not force and os.path.isfile(destination):
            log.info('Skipping existing file %s', destination)
        else:
            # make sure we have write permissions on the destination
            try:
                utils.make_writeable(destination)
                shutil.copyfile(full_path, destination)
                utils.make_read_only(destination, executable)
                log.info('Successfully copied %s', destination)
            except Exception as e:
                log.error("Failed copying file %s: %s", full_path, str(e))

    def _convert_dir(self, indir, outdir, force):
        """
        Convert or copy files in one directory to the corresponding output
        directory:
         - if the file ends with 'edl', convert
         - otherwise, copy the file
        """
        log.info('Starting directory %s', indir)
        if not os.path.isdir(outdir):
            os.makedirs(outdir)

        for local in os.listdir(indir):
            full_path = os.path.join(indir, local)
            if local.endswith(EDL_EXT):
                # edl files
                self._convert_one_file(full_path, outdir, force)
            elif not os.path.isdir(full_path) and not local.endswith('~'):
                # files not ending in ~
                self._copy_one_file(full_path, outdir, force)
            elif os.path.isdir(full_path) and not local.startswith('.'):
                # directories, excluing 'hidden' ones (e.g. .svn) recurse
                self._convert_dir(full_path, os.path.join(outdir, local), force)
            else:
                log.info('Ignoring %s', full_path)

    def update_paths(self, filepath, depth):
        module = filepath.split('/')[1]
        log.debug('Module for path %s is %s', filepath, module)
        paths.update_opi_file(filepath, depth, self.file_index, module)


# helper functions
def store_symbol(source, destination, symbol_dictionary):
    """ Build a global dictionary of {fullname:<destinations>}
        for symbol files needing conversion.

        If the passed source file is not in the dictionary it is added.
        If the passed source file is already in the dictionary the destination
        is added to the list, provided it is not already there.

        Arguments:
            source -> full path to file to be converted
            destination -> full path to output file
    """
    log.debug("Adding %s: %s to symbol dictionary", source, destination)
    if source in symbol_dictionary:
        symbol_dictionary[source].add(destination)
    else:
        symbol_dictionary[source] = set([destination])

