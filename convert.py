#!/usr/bin/env dls-python
'''
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
'''

import utils
import update_paths

import os
import sys
import glob
import subprocess
import shutil
import string
import ConfigParser
import argparse

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.DEBUG
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


def convert_symbol(symbol_file, destination):
    '''
    Convert an EDM symbol file into the png used by the CSS symbol widget.
    This uses an external shell script.
    '''
    utils.make_writeable(destination)
    # compress.py returns an edited .edl file
    command = COMPRESS_CMD + [symbol_file]
    out = subprocess.check_output(" ".join(command), shell=True)
    # copy png to right location
    relfilename = out.strip()
    filename = os.path.basename(relfilename)
    source = os.path.join(os.getcwd(), relfilename)
    destdir = os.path.dirname(destination)
    absfilename = os.path.join(destdir, filename)

    try:
        utils.make_writeable(absfilename)
        shutil.copyfile(source, absfilename)
        utils.make_read_only(absfilename)
    except Exception as e:
        log.warn("Failed copying file" + str(e))
        raise e


def update_edl(filename):
    '''
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    '''
    tmp_edm = os.path.join(TMP_DIR, os.path.basename(filename))
    if os.path.exists(tmp_edm):
        # make sure we have write permissions on the destination
        utils.make_writeable(tmp_edm)
    shutil.copyfile(filename, tmp_edm)
    cmd = UPDATE_CMD + [tmp_edm]
    x = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
    if not x:
        utils.make_writeable(tmp_edm)
        return tmp_edm
    else:
        log.warn('EDM update failed with code %s' % x)


def convert_edl(filename, destination):
    '''
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.
    '''
    utils.make_writeable(destination)
    # preprocess symbol files - Matt's symbol widget requires pngs
    # instead of the OPIs from the converter.
    # first try converting opi
    log.debug("Converting %s" % filename)
    command = CONVERT_CMD + [filename, destination]
    x = subprocess.call(command)
    utils.make_read_only(destination)
    if x != 0: # conversion failed
        log.warn('Conversion failed with code %d; will try updating' % x)
        new_edl = update_edl(filename)
        if new_edl is not None:
            log.warn('Updated to new-style edl %s' % new_edl)
            command = CONVERT_CMD + [new_edl, destination]
            x = subprocess.call(command)
            log.info("Conversion return code: %s" % x)
            utils.make_read_only(destination)
    return x == 0


class Converter(object):
    '''
    Given a script used to start EDM, deduce the directories needed
    for conversion and convert them in the appropriate format.
    Output goes in the directory provided.

    Since we can't easily determine symbol files, these may be specified
    on creation.
    '''

    def __init__(self, script_file, script_args, symbol_files, outdir):
        '''
        Given the EDM entry script, deduce the paths to convert.
        A list of symbol files is stored to help when converting.
        '''
        # Spoof EDM to find EDMDATAFILES and PATH
        # Index these directories to find which modules
        # relative paths may be in.
        edmdatafiles, paths, working_dir = utils.spoof_edm(script_file, script_args)
        self.edmdatafiles = [f for f in edmdatafiles if f not in  ('', '.')]
        self.edmdatafiles.append(working_dir)
        self.paths = paths
        self.paths.append(working_dir)
        self.file_dict = update_paths.index_opi_paths(self.edmdatafiles)
        self.path_dict = update_paths.index_paths(self.paths)
        self.symbol_files = symbol_files
        self.tmpdir = TMP_DIR
        self.symbolsdir = SYMBOLS_DIR
        try:
            self.module_name, self.version, _dummy = utils.parse_module_name(working_dir)
        except ValueError:
            log.warn("Didn't understand script's working directory!")
            self.module_name = os.path.basename(script_file)
            self.version = "0-0"
        self.module_name = self.module_name.replace('/', '_')
        self.outdir = os.path.join(outdir, "%s_%s" % (self.module_name, self.version))
        if not os.path.exists(self.outdir):
            log.info('Making new output directory %s' % self.outdir)
            os.makedirs(self.outdir)
        self.generate_project_file()

    def generate_project_file(self):
        '''
        Create an Eclipse project file for this set of OPIs.
        '''
        with open(PROJECT_TEMPLATE) as f:
            content = f.read()
        s = string.Template(content)
        updated_content = s.substitute(module_name=self.module_name,
                version=self.version)
        with open(os.path.join(self.outdir, PROJECT_FILENAME), 'w') as f:
            f.write(updated_content)

    def convert_opis(self, force):
        '''
        Given the EDM datafiles list, parse the directory and (recursively)
        any subdirectories for edm files.  Create output in a similar
        directory structure.
        '''
        for datadir in self.edmdatafiles:
            log.debug('EDM data file %s' % datadir)
            try:
                module_name, version, rel_path = utils.parse_module_name(datadir)
            except ValueError:
                module_name = ""
                rel_path = ""
                version = None
            log.debug("%s %s %s", module_name, version, rel_path)
            if rel_path is None:
                rel_path = ""
            module_name = module_name.split('/')[-1]
            log.debug("The module name path is %s", module_name)
            entries = os.listdir(datadir)
            for entry in entries:
                # ignore hidden directories
                if not entry.startswith('.'):
                    full_path = os.path.join(datadir, entry)
                    log.debug("New full path is %s", full_path)
                    if os.path.isdir(full_path):
                        outpath = os.path.join(self.outdir, module_name, rel_path, entry)
                        log.debug("New outdir is %s", outpath)
                        self.convert_dir(full_path, outpath, force)

            self.convert_dir(datadir, os.path.join(self.outdir, module_name, rel_path), force)

    def copy_scripts(self, force):
        '''
        Given the EDM PATH list, copy all files in the directory and any
        subdirectories across. Create output in a similar directory structure.
        '''
        log.debug("The path files are: %s", self.paths)
        for datadir in self.paths:
            log.debug('EDM path directory %s' % datadir)
            try:
                module_name, version, rel_path = utils.parse_module_name(datadir)
                if rel_path is None:
                    rel_path = ""
            except ValueError:
                log.warn("Can't parse path %s" % datadir)
                continue
            module_name = module_name.split('/')[-1]

            entries = os.listdir(datadir)
            for entry in entries:
                # ignore hidden directories
                if not entry.startswith('.'):
                    full_path = os.path.join(datadir, entry)
                    log.debug("New full path is %s", full_path)
                    if os.path.isdir(full_path):
                        outpath = os.path.join(self.outdir, module_name, rel_path, entry)
                        log.debug("New outdir is %s", outpath)
                        if not os.path.isdir(outpath):
                            os.makedirs(outpath)
                        self.convert_dir(full_path, os.path.join(self.outdir, module_name, entry), force)

            self.convert_dir(datadir, os.path.join(self.outdir, module_name, rel_path), force)


    def is_symbol(self, filename):
        '''
        Return True if:
         - the opi file name ends with 'symbol.edl'
         - the opi file name is included in self.symbol_files
        '''
        if filename.endswith('symbol.edl'):
            return True
        if os.path.basename(filename) in self.symbol_files:
            return True
        return False

    def already_converted(self, outdir, file):
        '''
        Return True if:
         - there is already a converted file in the destination
         - there is a png of the right name in place of a symbol file
        '''
        basename = os.path.basename(file)
        base = '.'.join(basename.split('.')[:-1])
        if self.is_symbol(file):
            # look for the converted png
            return len(glob.glob(os.path.join(outdir, base) + '*.png'))
        else:
            opifile = basename[:-len(EDL_EXT)] + OPI_EXT
            destination = os.path.join(outdir, opifile)
            return os.path.exists(destination)

    def convert_one_file(self, full_path, outdir, force):
        # change extension
        name = os.path.basename(full_path)
        opifile = name[:-len(EDL_EXT)] + OPI_EXT
        destination = os.path.join(outdir, opifile)
        try:
            if not force and self.already_converted(outdir, full_path):
                log.info('Skipping existing file %s' % destination)
            elif self.is_symbol(full_path):
                convert_symbol(full_path, destination)
                log.info('Successfully converted symbol file %s' % destination)
            else:
                convert_edl(full_path, destination)
                log.info('Successfully converted %s' % destination)
                self.update_paths(destination)
        except Exception as e:
            log.warn('Conversion of %s unsuccessful.' % full_path)
            log.warn(str(e))

    def copy_one_file(self, full_path, outdir, force):
        executable = os.access(full_path, os.X_OK)
        name = os.path.basename(full_path)
        destination = os.path.join(outdir, name)
        if not force and os.path.isfile(destination):
            log.info('Skipping existing file %s' % destination)
        else:
            # make sure we have write permissions on the destination
            if os.path.isfile(destination):
                utils.make_writeable(destination)
            if not subprocess.call(['cp', full_path, destination]):
                utils.make_read_only(destination, executable)
                log.info('Successfully copied %s' % destination)
            else:
                log.warn('Copying file %s unsuccessful.' % full_path)

    def convert_dir(self, indir, outdir, force):
        '''
        Convert or copy files in one directory to the corresponding output
        directory:
         - if the file ends with 'edl', convert
         - otherwise, copy the file
        '''
        log.info('Starting directory %s' % indir)
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        full_paths = [os.path.join(indir, f) for f in os.listdir(indir)]

        for full_path in full_paths:
            log.debug('Trying %s...' % full_path)
            if full_path.endswith(EDL_EXT):
                self.convert_one_file(full_path, outdir, force)
            elif not os.path.isdir(full_path) and not full_path.endswith('~'):
                self.copy_one_file(full_path, outdir, force)
            else:
                log.info('Ignoring %s' % full_path)

    def update_paths(self, filepath):
        module = filepath.split('/')[1]
        log.debug('Module for path %s is %s' % (filepath, module))
        update_paths.parse(filepath, self.file_dict, self.path_dict, module)


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


if __name__ == '__main__':

    # Parse configuration
    args = set_up_options()
    log.debug("Config files supplied: %s", args.config)

    for cfg in args.config:
        log.info('\n\nStarting config file %s.\n', cfg)
        cp = ConfigParser.ConfigParser()
        cp.read(cfg)

        try:
            if not os.path.isdir(TMP_DIR):
                os.makedirs(TMP_DIR)
            if not os.path.isdir(SYMBOLS_DIR):
                os.makedirs(SYMBOLS_DIR)
        except OSError:
            log.error('Could not create temporary directories %s and %s',
                    (TMP_DIR, SYMBOLS_DIR))
            sys.exit()

    try:
        script_file = cp.get('edm', 'edm_script')
    except ConfigParser.NoSectionError:
        log.error('Please ensure %s is a valid config file' % args.config)
        sys.exit()

    try:
        script_args = cp.get('edm', 'script_args')
    except ConfigParser.NoOptionError:
        script_args = None

    try:
        outdir = cp.get('opi', 'outdir')
    except ConfigParser.NoSectionError:
        log.error('Please ensure %s is a valid config file' % args.config)
        sys.exit()

    try:
        symbols = cp.get('edm', 'symbols')
        symbols = symbols.split(':')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        symbols = []

    c = Converter(script_file, script_args, symbols, outdir)
    c.convert_opis(args.force)
    c.copy_scripts(args.force)


