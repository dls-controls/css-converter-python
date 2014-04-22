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
        print "update finished with code", x


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
            print 'Updated to new-style edl', new_edl
            command = CONVERT_CMD + [new_edl, destination]
            x = subprocess.call(command, stdout=NULL_FILE, stderr=NULL_FILE)
    return x == 0


def start(datadirs, outdir, force):
    for dir in datadirs:
        print 'Starting directory', dir
        files = os.listdir(dir)
        files = [os.path.join(dir, file) for file in files]

        for file in files:
            print 'Trying %s...' % file
            if file.endswith(EDL_EXT):
                # change extension
                name = os.path.basename(file)
                opifile = name[:-len(EDL_EXT)] + OPI_EXT
                destination = os.path.join(outdir, opifile)
                if not force and os.path.isfile(destination):
                    print 'Skipping existing file %s' % destination
                else:
                    if convert(file, destination):
                        print 'Successfully converted %s' % destination
                    else:
                        print 'Conversion unsuccessful.'
            elif file.split('.')[-1] in COPY_EXTS:
                name = os.path.basename(file)
                destination = os.path.join(outdir, name)
                if not force and os.path.isfile(destination):
                    print 'Skipping existing file %s' % destination
                else:
                    if subprocess.call(['cp', file, destination]):
                        print 'Successfully copied %s' % destination
                    else:
                        print 'Copying unsuccessful.'
            else:
                print 'Not doing anything with %s' % file

def get_datadirs(root, edmdatafiles):
    # Assemble the directories to convert.
    datadirs = []
    if root is not None:
        datadirs.append(root)
    if edmdatafiles is not None:
        datadirs.extend(edmdatafiles.split(':'))

    return datadirs

if __name__ == "__main__":
    # Parse configuration
    if len(sys.argv) == 1 or not os.path.isfile(sys.argv[1]):
        print 'Please specify a configuration file.'
        sys.exit()
    force = '-f' in sys.argv
    cp = ConfigParser.ConfigParser()
    cp.read(sys.argv[1])

    try:
        root = cp.get('edm', 'root')
    except ConfigParser.NoOptionError:
        print "No root option found."
        root = None

    try:
        datafiles = cp.get('edm', 'edmdatafiles')
    except ConfigParser.NoOptionError:
        print "No data files option found."
        datafiles = None

    outdir = cp.get('opi', 'outdir')
    if not os.path.isdir(outdir):
        print 'Directory %s does not exist' % outdir
        sys.exit()

    datadirs = get_datadirs(root, datafiles)

    start(datadirs, outdir, force)

