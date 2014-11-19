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

from convert import converter
from convert import files
from convert.files import SYMBOLS_DIR, TMP_DIR

import os
import ConfigParser
import argparse

import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)


class ConfigurationError(Exception):
    """ Customer exception to be raised in there is a config-file parse
        error
    """
    pass


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

            c = converter.Converter(script_file, script_args, symbols, outdir, symbol_dict)
            c.convert(args.force)
        except ConfigurationError:
            log.error('Please ensure %s is a valid config file' % args.config)

    if symbol_dict:
        log.info("Post-processing symbol files")
        for path, destinations in symbol_dict.iteritems():
            files.convert_symbol(path, destinations)


if __name__ == '__main__':
    run_conversion()
