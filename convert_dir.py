#!/usr/bin/env dls-python
'''
Convert only one directory, rather than using the launcher.
'''
import os
import sys
import logging as log
LOG_FORMAT = '%(levelname)s:  %(message)s'
LOG_LEVEL = log.INFO
log.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

from convert import converter
from convert import utils
from convert_launcher import process_symbol_files, SYMBOLS_CONF, OUTDIR


if __name__ == '__main__':

    try:
        directory = sys.argv[1]
        assert os.path.isdir(directory)
    except (IndexError, AssertionError):
        print('Usage: {} <directory>'.format(sys.argv[0]))
        sys.exit()

    symbols = utils.read_symbols_file(SYMBOLS_CONF)
    c = converter.Converter([sys.argv[1]], symbols, OUTDIR, {})
    c.convert(False)
    symbols = c.get_symbol_paths()
    print("Symbols: " + str(symbols))

    if symbols:
        process_symbol_files(symbols, True)
