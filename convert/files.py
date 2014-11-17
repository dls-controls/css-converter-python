
import utils
import compress

import subprocess
import shutil
import os
import logging as log

NULL_FILE = open(os.devnull, 'w')
TMP_DIR = './tmp'
# Commands in lists for subprocess
CONVERT_CMD = ['java', '-Dedm2xml.colorsFile=res/colors.list', '-jar', 'res/conv.jar']
UPDATE_CMD = ['edm', '-convert']
SYMBOLS_DIR = './tmp/symbols'
SYMB_SCRIPT = os.path.join(os.getcwd(), 'res/auto-symb.sh')
COMPRESS_CMD = [SYMB_SCRIPT]


def convert_symbol(symbol_file, destinations):
    """
    Convert an EDM symbol file into the png used by the CSS symbol widget.
    This uses an external shell script.
    """
    log.debug("Converting symbol %s", symbol_file)
    dest = os.path.join(SYMBOLS_DIR, os.path.basename(symbol_file))
    utils.make_writeable(dest)
    shutil.copyfile(symbol_file, dest)
    # Update EDM file if necessary.
    if is_old_edl(dest):
        dest = update_edl(dest)
    # Compress EDM symbol file to minimum rectangle.
    compress.parse(dest)
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
            log.error("Failed copying file: %s", str(e))


def is_old_edl(filename):
    """
    Check version of .edl file.  Versions < 3 need updating.
    """
    with open(filename) as edm_file:
        for line in edm_file.readlines():
            if line.isspace() or line.strip().startswith('#'):
                continue
            return int(line.split()[0]) < 4


def update_edl(filename):
    """
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    """
    print 'updating', filename
    try:
        tmp_edm = os.path.join(TMP_DIR, os.path.basename(filename))
        print 'dest is', tmp_edm
        # make sure we have write permissions on the destination
        utils.make_writeable(tmp_edm)
        shutil.copyfile(filename, tmp_edm)
        cmd = UPDATE_CMD + [tmp_edm]
        print 'updated %s with %s' % (tmp_edm, cmd)
        returncode = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
        if returncode == 0:
            utils.make_writeable(tmp_edm)
            return tmp_edm
        else:
            log.warn('EDM update failed with code %s', returncode)
    except Exception as e:
        log.error("Failed copying file" + str(e))

    return None  # else and Exception cases


def convert_edl(filename, destination):
    """
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.

    Return the conversion return code.
    """
    if is_old_edl(filename):
        filename = update_edl(filename)
    utils.make_writeable(destination)
    log.debug("Converting %s", filename)
    command = CONVERT_CMD + [filename, destination]
    returncode = subprocess.call(command)
    utils.make_read_only(destination)
    return returncode
