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
 - if file is an image, copy across directly
'''
import utils
import update_paths

import os
import sys
import glob
import subprocess
import shutil
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


def make_read_only(filename):
    if os.path.exists(filename):
        os.chmod(filename, 0o444)

def make_writeable(filename):
    if os.path.exists(filename):
        os.chmod(filename, 0o777)

def update_edm(filename):
    '''
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    '''
    tmp_edm = os.path.join(TMP_DIR, os.path.basename(filename))
    if os.path.exists(tmp_edm):
        # make sure we have write permissions on the destination
        make_writeable(tmp_edm)
    shutil.copyfile(filename, tmp_edm)
    cmd = UPDATE_CMD + [tmp_edm]
    x = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
    if not x:
        make_writeable(tmp_edm)
        return tmp_edm
    else:
        log.warn('EDM update failed with code %s', x)

def is_symbol(filename, symbols):
    if filename.endswith('symbol.edl'):
        return True
    if os.path.basename(filename) in symbols:
        return True
    return False

def convert_symbol(symbol_file, destdir):
    # compress.py returns an edited .edl file
    command = COMPRESS_CMD + [symbol_file]
    png_file = subprocess.check_output(" ".join(command), shell=True, stderr=NULL_FILE)
    # copy png to right location
    relfilename = png_file.strip()
    filename = os.path.basename(relfilename)
    source = os.path.join(os.getcwd(), relfilename)
    absfilename = os.path.join(destdir, filename)

    try:
        make_writeable(absfilename)
        shutil.copyfile(source, absfilename)
        make_read_only(absfilename)
    except Exception as e:
        log.warn("Failed copying file" + str(e))
        raise e


def convert(filename, destination):
    '''
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.
    '''
    make_writeable(destination)
    # preprocess symbol files - Matt's symbol widget requires pngs
    # instead of the OPIs from the converter.
    # first try converting opi
    command = CONVERT_CMD + [filename, destination]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    x = p.returncode
    if err != "":
        log.info(err)
    if out != "":
        log.debug(out)
    make_read_only(destination)
    if x != 0: # conversion failed
        log.warn('Conversion failed with code %d; will try updating', x)
        new_edl = update_edm(filename)
        if new_edl is not None:
            log.warn('Updated to new-style edl %s', new_edl)
            command = CONVERT_CMD + [new_edl, destination]
            x = subprocess.call(command)
            log.info("Conversion return code: %s", x)
            make_read_only(destination)
    return x == 0

def already_converted(outdir, file, symbols):
    basename = os.path.basename(file)
    base = '.'.join(basename.split('.')[:-1])
    if is_symbol(file, symbols):
        # look for the converted png
        return len(glob.glob(os.path.join(outdir, base) + '*.png'))
    else:
        opifile = basename[:-len(EDL_EXT)] + OPI_EXT
        destination = os.path.join(outdir, opifile)
        return os.path.exists(destination)


def parse_dir(directory, symbols, outdir, force):
    log.info('Starting directory %s', directory)
    files = os.listdir(directory)
    files = [os.path.join(directory, file) for file in files]
    if not os.path.exists(outdir):
        log.info('Making new output directory %s', outdir)
        os.mkdir(outdir)

    for file in files:
        log.debug('Trying %s...', file)
        if file.endswith(EDL_EXT):
            # change extension
            name = os.path.basename(file)
            opifile = name[:-len(EDL_EXT)] + OPI_EXT
            destination = os.path.join(outdir, opifile)
            try:
                if not force and already_converted(outdir, file, symbols):
                    log.info('Skipping existing file %s', destination)

                elif is_symbol(file, symbols):
                    convert_symbol(file, outdir)
                    log.info('Successfully converted symbol file %s', destination)
                else:
                    if convert(file, destination):
                        log.info('Successfully converted %s', destination)
                    else:
                        log.error('Failed to convert %s', file)
            except Exception as e:
                log.warn('Conversion of %s unsuccessful.', file)
                log.warn(str(e))
        elif not os.path.isdir(file) and not file.endswith('~'):
            # copy all other files
            name = os.path.basename(file)
            destination = os.path.join(outdir, name)
            if not force and os.path.isfile(destination):
                log.info('Skipping existing file %s', destination)
            else:
                # make sure we have write permissions on the destination
                if os.path.isfile(destination):
                    make_writeable(destination)
                if not subprocess.call(['cp', file, destination]):
                    make_read_only(destination)
                    log.info('Successfully copied %s', destination)
                else:
                    log.warn('Copying file %s unsuccessful.', file)
        else:
            log.info('Ignoring %s', file)

def start(datadirs, symbols, outdir, force):
    '''
    Given the EDM datafiles list, parse the directory and any subdirectories
    for edm files.  Create output in a similar directory structure.
    '''
    for directory in datadirs:
        entries = os.listdir(directory)
        for entry in entries:
            # ignore hidden directories
            if not entry.startswith('.'):
                full_path = os.path.join(directory, entry)
                if os.path.isdir(full_path):
                    parse_dir(full_path, symbols, os.path.join(outdir, entry), force)

        parse_dir(directory, symbols, outdir, force)


def datadirs_from_string(edmdatafiles):
    # Assemble the directories to convert.
    return edmdatafiles.split(':')

def datadirs_from_file(filename):
    paths = []
    for line in open(filename):
        if not (line.startswith('#') or line.isspace()):
            paths.append(line.strip())
    return paths

def update_version(filepath):
    '''
    If the filepath contains '/*/', assume it refers to a version number.
    Check the directory for the latest version and use that.
    '''
    try:
        if '/*/' in filepath:
            parts = filepath.split('/*/')
            versions = os.listdir(parts[0])
            m1 = 0
            m2 = 0
            for version in versions:
                [a, b] = [int(i) for i in version.split('-')]
                if a > m1:
                    m1 = a
                    m2 = b
                elif a == m1 and b > m2:
                    m2 = b
            return "%s/%d-%d/%s" % (parts[0], m1, m2, parts[1])
    except Exception, e:
        log.warn("Version update failed on %s: %s", (filepath, e))
        return filepath

    return filepath

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
    print args.config

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
            outdir = cp.get('opi', 'outdir')
            if not os.path.isdir(outdir):
                log.info('Creating directory %s for output files.', outdir)
                os.makedirs(outdir)
        except ConfigParser.NoSectionError:
            log.error('Please ensure %s is a valid config file', cfg)
            sys.exit()

        try:
            datafiles = cp.get('edm', 'edmdatafiles')
            datadirs = datadirs_from_string(datafiles)
        except ConfigParser.NoOptionError:
            try:
                datafilepath = cp.get('edm', 'edmpathfile')
                datadirs = datadirs_from_file(datafilepath)
            except ConfigParser.NoOptionError:
                log.error('No data files option found in %s.', cfg)
                log.error('Use either edmdatafiles or edmpathfile options.')
                sys.exit()

        try:
            symbols = cp.get('edm', 'symbols')
            symbols = symbols.split(':')
        except:
            symbols = []

        datadirs = [update_version(dd) for dd in datadirs]

        start(datadirs, symbols, outdir, args.force)

