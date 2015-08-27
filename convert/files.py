import utils
import symbols
import glob

import subprocess
import shutil
import os
import logging as log


# Configuration
NULL_FILE = open(os.devnull, 'w')
TMP_DIR = './tmp'
SYMBOLS_DIR = os.path.join(TMP_DIR, 'symbols')
# Commands in lists for subprocess
JAVA = '/usr/bin/java'
JAR_FILE = 'res/conv.jar'
MAIN_CLASS = 'org.csstudio.opibuilder.converter.EdmConverter'
COLORS_VARIABLE = '-Dedm2xml.colorsFile=res/colors.list'
SYMBOLS_VARIABLE = '-Dedm2xml.symbolsFile=res/symbols.conf'
CONVERT_CMD = [JAVA, COLORS_VARIABLE, SYMBOLS_VARIABLE, '-cp', JAR_FILE, MAIN_CLASS]
UPDATE_CMD = ['edm', '-convert']
SYMBOL_SCRIPT = os.path.join(os.getcwd(), 'res/auto-symb.sh')
SYMBOL_TO_PNG_CMD = [SYMBOL_SCRIPT]



class OldEdlError(Exception):
    pass


def convert_symbol(symbol_file, destinations):
    """
    Convert an EDM symbol file into the png used by the CSS symbol widget.
    This uses an external shell script.
    """
    log.debug("Converting symbol %s", symbol_file)
    if not os.path.exists(SYMBOLS_DIR):
        os.makedirs(SYMBOLS_DIR)

    temp_file = os.path.join(SYMBOLS_DIR, os.path.basename(symbol_file))
    utils.make_writeable(temp_file)
    shutil.copyfile(symbol_file, temp_file)
    png_files = glob.glob(os.path.join(os.path.dirname(symbol_file), '*.png'))
    for png_file in png_files:
        shutil.copyfile(png_file, os.path.join(SYMBOLS_DIR, os.path.basename(png_file)))
    # Update EDM file if necessary.
    if is_old_edl(temp_file):
         update_edl(temp_file, in_place=True)
    # Compress EDM symbol file to minimum rectangle.
    try:
        symbols.compress(temp_file)
    except symbols.SymbolError as e:
        log.error(e)
        return

    command = SYMBOL_TO_PNG_CMD + [temp_file]
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
        except Exception as e:
            log.error("Failed copying file: %s", str(e))

    return filename


def is_old_edl(filename):
    """
    Check version of .edl file.  Versions < 3 need updating.
    """
    with open(filename) as edm_file:
        for line in edm_file.readlines():
            if line.isspace() or line.strip().startswith('#'):
                continue
            return int(line.split()[0]) < 4


def update_edl(filename, in_place=False):
    """
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    """
    try:
        if not in_place:
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
            temp_file = os.path.join(TMP_DIR, os.path.basename(filename))
            shutil.copyfile(filename, temp_file)
            filename = temp_file
        # make sure we have write permissions on the destination
        utils.make_writeable(filename)
        cmd = UPDATE_CMD + [filename]
        returncode = subprocess.call(cmd, stdout=NULL_FILE, stderr=NULL_FILE)
        if returncode == 0:
            utils.make_writeable(filename)
            return filename
        else:
            log.warn('EDM update failed with code %s', returncode)
    except Exception as e:
        log.error("Failed copying file" + str(e))

    return None  # else and Exception cases


def convert_edl(filename, destination):
    """
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.

    Return True if conversion successful, False if a non-zero return code produced.
    """
    if is_old_edl(filename):
        raise OldEdlError('EDL file in old format')
    if not os.path.exists(JAVA):
        raise utils.ConfigError('Cannot find java executable {}'.format(JAVA))
    if not os.path.exists(JAR_FILE):
        raise utils.ConfigError('Cannot find jar file {}'.format(JAR_FILE))

    utils.make_writeable(destination)
    log.debug('Converting %s to %s', filename, destination)
    command = CONVERT_CMD + [filename, destination]
    log.debug('Conversion command {}'.format(' '.join(command)))

    returncode = subprocess.call(command)
    if returncode != 0:
        log.warn('Conversion of {0} failed with code {1}.'.format(filename, returncode))
        success = False
    else:
        success = True

    return success
