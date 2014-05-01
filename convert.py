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

import os
import sys
import subprocess
import shutil
import stat
import ConfigParser
import argparse

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


NULL_FILE = open(os.devnull, 'w')
TMPDIR = './tmp'

OPI_EXT = 'opi'
EDL_EXT = 'edl'

# Filetypes to copy across unchanged
COPY_EXTS = ['png', 'sh']

# Commands in lists for subprocess
CONVERT_CMD = ['java', '-jar', 'conv.jar']
UPDATE_CMD = ['edm', '-convert']


def update_edm(filename):
    '''
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    '''
    tmp_edm = os.path.join(TMPDIR, os.path.basename(filename))
    if os.path.exists(tmp_edm):
        # make sure we have write permissions on the destination
        os.chmod(tmp_edm, stat.S_IWUSR)
    shutil.copyfile(filename, tmp_edm)
    cmd = UPDATE_CMD + [tmp_edm]
    x = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
    if not x:
        os.chmod(tmp_edm, 0o777)
        return tmp_edm
    else:
        log.warn('EDM update failed with code %s' % x)


def convert(filename, destination):
    '''
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.
    '''
    # first try
    command = CONVERT_CMD + [filename, destination]
    x = subprocess.call(command, stdout=NULL_FILE, stderr=NULL_FILE)
    if x != 0: # conversion failed
        log.warn('Conversion failed with code %d' % x)
        new_edl = update_edm(filename)
        if new_edl is not None:
            log.warn('Updated to new-style edl %s' % new_edl)
            command = CONVERT_CMD + [new_edl, destination]
            x = subprocess.call(command, stdout=NULL_FILE, stderr=NULL_FILE)
    return x == 0


def parse_dir(directory, outdir, force):
    log.info('Starting directory %s' % directory)
    files = os.listdir(directory)
    files = [os.path.join(directory, file) for file in files]
    edm_dir = any(file.endswith(EDL_EXT) for file in files)
    if edm_dir and not os.path.exists(outdir):
        log.info('Making new output directory %s' % outdir)
        os.mkdir(outdir)

    for file in files:
        log.debug('Trying %s...' % file)
        if file.endswith(EDL_EXT):
            # change extension
            name = os.path.basename(file)
            opifile = name[:-len(EDL_EXT)] + OPI_EXT
            destination = os.path.join(outdir, opifile)
            if not force and os.path.isfile(destination):
                log.info('Skipping existing file %s' % destination)
            else:
                if convert(file, destination):
                    log.info('Successfully converted %s' % destination)
                else:
                    log.warn('Conversion of %s unsuccessful.' % file)
        elif file.split('.')[-1] in COPY_EXTS:
            name = os.path.basename(file)
            destination = os.path.join(outdir, name)
            if not force and os.path.isfile(destination):
                log.info('Skipping existing file %s' % destination)
            else:
                if subprocess.call(['cp', file, destination]):
                    log.info('Successfully copied %s' % destination)
                else:
                    log.warn('Copying file %s unsuccessful.' % file)
        else:
            log.info('Not doing anything with %s' % file)

def start(datadirs, outdir, force):
    '''
    Given the EDM datafiles list, parse the directory and any subdirectories
    for edm files.  Create output in a similar directory structure.
    '''
    for directory in datadirs:
        entries = os.listdir(directory)
        for entry in entries:
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                parse_dir(full_path, os.path.join(outdir, entry), force)

        parse_dir(directory, outdir, force)


def datadirs_from_string(root, edmdatafiles):
    # Assemble the directories to convert.
    return edmdatafiles.split(':')

def datadirs_from_file(filename):
    paths = []
    for line in open(filename):
        if not (line.startswith('#') or line.isspace()):
            paths.append(line.strip())
    return paths

def set_up_options():
    parser = argparse.ArgumentParser(description='''
    Convert whole areas of EDM screens into CSS's OPI format.
    Configuration files for each area are found in the conf/
    directory.  The output location is not automatically 
    created to avoid unwanted files...
    ''')
    parser.add_argument('-f', dest='force',
        help='overwrite existing OPI files')
    parser.add_argument('config', metavar='<config-file>',
        help='config file specifying EDM paths and output dir')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    # Parse configuration
    args = set_up_options()

    cp = ConfigParser.ConfigParser()
    cp.read(args.config)

    try:
        outdir = cp.get('opi', 'outdir')
        if not os.path.isdir(outdir):
            log.error('Please create directory %s for output files.' % outdir)
            sys.exit()
    except ConfigParser.NoSectionError:
        log.error('Please ensure %s is a valid config file' % args.config)
        sys.exit()

    try:
        datafiles = cp.get('edm', 'edmdatafiles')
        datadirs = datadirs_from_string(datafiles)
    except ConfigParser.NoOptionError:
        try:
            datafilepath = cp.get('edm', 'edmpathfile')
            datadirs = datadirs_from_file(datafilepath)
        except ConfigParser.NoOptionError:
            log.error('No data files option found in %s.' % args.config)
            log.error('Use either edmdatafiles or edmpathfile options.')
            sys.exit()

    start(datadirs, outdir, args.force)

