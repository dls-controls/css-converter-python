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

import os
import glob
import subprocess
import shutil
import string
import ConfigParser
import argparse

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


NULL_FILE = open(os.devnull, 'w')
TMP_DIR = './tmp'
SYMBOLS_DIR = './tmp/symbols'

OPI_EXT = 'opi'
EDL_EXT = 'edl'

# Commands in lists for subprocess
CONVERT_CMD = ['java', '-jar', 'conv.jar']
UPDATE_CMD = ['edm', '-convert']
SYMB_SCRIPT = os.path.join(os.getcwd(), 'auto-symb.sh')
COMPRESS_CMD = [SYMB_SCRIPT]

PROJECT_TEMPLATE = 'project.template'
PROJECT_FILENAME = '.project'


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

    def __init__(self, script_file, script_args, symbol_files, outdir, symbol_dict):
        """
        Given the EDM entry script, deduce the paths to convert.
        A list of symbol files is stored to help when converting.
        """
        # Spoof EDM to find EDMDATAFILES and PATH
        # Index these directories to find which modules
        # relative paths may be in.
        edmdatafiles, path_dirs, working_dir, args = utils.spoof_edm(
            script_file, script_args)

        self.edmdatafiles = [f for f in edmdatafiles if f not in ('', '.')]
        self.edmdatafiles.append(working_dir)

        self.path_dirs = path_dirs
        self.path_dirs.append(working_dir)

        self.file_index = paths.index_paths(self.edmdatafiles + self.path_dirs, True)

        self.symbol_files = symbol_files
        self.symbol_files = symbol_dict

        try:
            self.module_name, self.version, _ = utils.parse_module_name(working_dir)
        except ValueError:
            log.warn("Didn't understand script's working directory!")
            self.module_name = os.path.basename(script_file)
            self.version = None

        self.module_name = self.module_name.replace('/', '_')

        if self.version is None:
            self.version = 'no-version'

        self.root_outdir = os.path.join(outdir, "%s_%s" % (self.module_name, self.version))
        if not os.path.exists(self.root_outdir):
            log.info('Making new output directory %s', self.root_outdir)
            os.makedirs(self.root_outdir)

        self._generate_project_file()

    def _generate_project_file(self):
        """
        Create an Eclipse project file for this set of OPIs.
        """
        with open(os.path.join(self.root_outdir, PROJECT_FILENAME), 'w') as f:
            with open(PROJECT_TEMPLATE) as template:
                content = template.read()
                s = string.Template(content)
                updated_content = s.substitute(module_name=self.module_name,
                                               version=self.version)
                f.write(updated_content)

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

    def convert(self, force):
        """
        Given the EDM datafiles and PATH lists, parse the directory and
        any subdirectories for edm/script files.  Create output in a similar
        directory structure.
        """
        for datadir in self.edmdatafiles + self.path_dirs:
            # Currently can't handle relative directories.
            if datadir.startswith('.'):
                continue
            log.debug('EDM data file %s', datadir)
            try:
                module_name, version, rel_path = utils.parse_module_name(datadir)
            except ValueError:
                log.warn("Can't parse path %s" % datadir)
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
                store_symbol(full_path, destination, self.symbol_files)
                log.info('Successfully stored symbol file %s' % destination)
            else:
                convert_edl(full_path, destination)
                log.info('Successfully converted %s', destination)
                self.update_paths(destination, depth)
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
                log.info('Successfully copied %s' % destination)
            except Exception as e:
                log.error("Failed copying file" + str(e))

    def _convert_dir(self, indir, outdir, force):
        """
        Convert or copy files in one directory to the corresponding output
        directory:
         - if the file ends with 'edl', convert
         - otherwise, copy the file
        """
        log.info('Starting directory %s' % indir)
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
        log.debug('Module for path %s is %s' % (filepath, module))
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
        destinations = symbol_dictionary[source]
        if not destination in destinations:
            destinations.append(destination)
    else:
        symbol_dictionary[source] = [destination]


def set_up_options():
    parser = argparse.ArgumentParser(description='''
    Convert whole areas of EDM screens into CSS's OPI format.
    Configuration files for each area are found in the conf/
    directory.  The output location is not automatically
    created to avoid unwanted files...
    ''')
    parser.add_argument('-f', action='store_true', dest='force',
                        help='overwrite existing OPI files')
    parser.add_argument('config', metavar='<config-file>', nargs='*',
                        help='config file specifying EDM paths and output dir')
    args = parser.parse_args()
    return args


def parse_config(cfg):
    """ Parse a specified configuration file

        Raises ConfigurationError if critical section is missing

        Returns:
            script_file,
            script_args,
            symbols,
            outdir
    """

    log.info('\n\nStarting config file %s.\n', cfg)
    cp = ConfigParser.ConfigParser()
    cp.read(cfg)

    try:
        script_file = cp.get('edm', 'edm_script')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        raise ConfigurationError()

    try:
        script_args = cp.get('edm', 'script_args')
        script_args = script_args.split()
    except ConfigParser.NoOptionError:
        script_args = []

    try:
        outdir = cp.get('opi', 'outdir')
    except ConfigParser.NoSectionError:
        raise ConfigurationError()

    try:
        symbols = cp.get('edm', 'symbols')
        symbols = symbols.split(':')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        symbols = []

    return script_file, script_args, symbols, outdir


def run_conversion():
    """ Perform the module conversion.
        This is the entry point for the module
    """

    symbol_dict = {}

    # Parse configuration
    args = set_up_options()
    log.debug('Config files supplied: %s', args.config)

    try:
        if not os.path.isdir(TMP_DIR):
            os.makedirs(TMP_DIR)
        if not os.path.isdir(SYMBOLS_DIR):
            os.makedirs(SYMBOLS_DIR)
    except OSError:
        log.error('Could not create temporary directories %s and %s',
                  (TMP_DIR, SYMBOLS_DIR))

    for cfg in args.config:
        try:
            (script_file, script_args, symbols, outdir) = parse_config(cfg)

            for sym in symbols:
                print "Found symbol: " + sym

            c = Converter(script_file, script_args, symbols, outdir, symbol_dict)
            c.convert(args.force)
        except ConfigurationError:
            log.error('Please ensure %s is a valid config file' % args.config)

    log.info("Post-processing symbol files")
    for path, destinations in symbol_dict.iteritems():
        convert_symbol(path, destinations)


def convert_symbol(symbol_file, destinations):
    """
    Convert an EDM symbol file into the png used by the CSS symbol widget.
    This uses an external shell script.
    """
    log.debug("Converting symbol %s", symbol_file)
    # compress.py returns an edited .edl file
    command = COMPRESS_CMD + [symbol_file]
    out = subprocess.check_output(" ".join(command), shell=True)
    # copy png to right location
    relfilename = out.strip()
    filename = os.path.basename(relfilename)
    source = os.path.join(os.getcwd(), relfilename)

    # Copy the converted png to all specified destinations
    for destination in destinations:
        log.debug("... copy to %s", destination)
        try:
            utils.make_writeable(destination)
            destdir = os.path.dirname(destination)
            absfilename = os.path.join(destdir, filename)

            utils.make_writeable(absfilename)
            shutil.copyfile(source, absfilename)
            utils.make_read_only(absfilename)
        except Exception as e:
            log.error("Failed copying file" + str(e))


def update_edl(filename):
    """
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    """
    try:
        tmp_edm = os.path.join(TMP_DIR, os.path.basename(filename))
        # make sure we have write permissions on the destination
        utils.make_writeable(tmp_edm)
        shutil.copyfile(filename, tmp_edm)
        cmd = UPDATE_CMD + [tmp_edm]
        returncode = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
        if returncode != 0:
            utils.make_writeable(tmp_edm)
            return tmp_edm
        else:
            log.warn('EDM update failed with code %s' % returncode)
    except Exception as e:
        log.error("Failed copying file" + str(e))

    return None  # else and Exception cases

def convert_edl(filename, destination):
    """
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.
    """
    utils.make_writeable(destination)
    # preprocess symbol files - Matt's symbol widget requires pngs
    # instead of the OPIs from the converter.
    # first try converting opi
    log.debug("Converting %s" % filename)
    command = CONVERT_CMD + [filename, destination]
    returncode = subprocess.call(command)
    utils.make_read_only(destination)
    if returncode != 0:  # conversion failed
        log.warn('Conversion failed with code %d; will try updating' % returncode)
        new_edl = update_edl(filename)
        if new_edl is not None:
            log.warn('Updated to new-style edl %s' % new_edl)
            command = CONVERT_CMD + [new_edl, destination]
            returncode = subprocess.call(command)
            log.info("Conversion return code: %s" % returncode)
            utils.make_read_only(destination)

if __name__ == '__main__':
    run_conversion()
