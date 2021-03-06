#!/usr/bin/env dls-python
'''
Menu mux widgets in EDM can't be automatically translated by the
converter, because they rely on dynamic macros which do not exist
in CSS.

What can be done is to achieve the same effect with a local PV.
However, the problem with this is that the converter doesn't know
which macros in an OPI file need to be changed to local PVs.

Process:

1. Find all the symbols used by a menu mux button.
2. Find any references to these symbols.
3. Replace the reference with the appropriate expression.
'''
import os
import subprocess
import xml.etree.ElementTree as ET
import logging as log

import mmux
import utils

MENU_MUX_ID = 'org.csstudio.opibuilder.widgets.edm.menumux'
MISSING = 'missing'
LOC_PREFIX = 'loc://$(DID)'
VSTRING_TYPE = '<VString>'

# OPI XML tags to subsitute a plain 'concat( )' not 'pv(concat( ))'
NON_PV_TAGS = ['text']

# OPI XML tags to make *no* replacements in: any replacements won't work as
# PVs must be passed into the script as arguments; a manual post-process step
EXCLUDED_TAGS = ['scriptText']


def is_menumux(element):
    """ Return true if the tree element is a widget with typeId menumux
    """

    return element.tag == 'widget' and \
        element.get('typeId', default=MISSING) == MENU_MUX_ID


def find_mm_symbols(node):
    """
    Recursively find all MenuMux symbols from root node.
    Return a list of (name, first_value).
    """
    symbols = {}
    if len(node) == 0:
        return symbols
    else:
        for child in node:
            if is_menumux(child):
                try:
                    # grab the number of sets of target-values defined
                    num_sets = child.find('num_sets')
                    for set_idx in range(0, int(num_sets.text)):

                        target = child.find("target%d" % set_idx)
                        values = child.find("values%d" % set_idx)

                        if LOC_PREFIX in target.text:
                            log.info("Skipping already updated target %s", target.text)
                        else:
                            first_value = values.find('s')
                            symbols[target.text] = first_value.text

                            # Update the target text to be a (private) locPV
                            target.text = create_loc_pv(target.text)
                except AttributeError as e:
                    log.warn("Error parsing MenuMux: %s", e)
            else:
                symbols.update(find_mm_symbols(child))

    return symbols


def create_loc_pv(pv_name, initial_value=None):
    """Create a local PV for use in a menu mux.

    Args:
    - pv_name: name of edl macro, e.g. iot
    - initial_value: optional initial value
    Returns:
        loc://$(DID)pv_name<VString> if initial value is None
        loc://$(DID)pv_name<VString>(\"initial_value\") otherwise
    """
    pv = '{}{}{}'.format(LOC_PREFIX, pv_name, VSTRING_TYPE)

    if initial_value is not None:
        pv += '(\"{}\")'.format(initial_value)

    return pv


def try_replace(text, symbols):
    """
    Find instances of symbols as macros.  Replace with a local
    PV with a value selected as initial state.

        Returns:
            - name mangled string to use
    """

    updated = text
    matched = False

    for sym, value in symbols.iteritems():
        sym_rep = '$(%s)' % sym
        sym_loc = create_loc_pv(sym, value)
        sym_loc_ts = "toString('%s')" % sym_loc

        if sym_rep == text:
            matched = True
            updated = sym_loc
            # can abort here as we've finished
            break

        elif sym_rep in updated:

            matched = True
            # Three cases:
            # i) the pattern is at the start of the string
            # ii) the pattern is at the end of the string
            # iii) the pattern is somewhere in the middle
            length = len(sym_rep)
            index = updated.index(sym_rep)

            if index == 0:  # match at the start
                body = '%s, "%s"' % (sym_loc_ts, updated[length:])
            elif index + length == len(updated):  # match at the end
                body = '"%s", %s' % (updated[:-length], sym_loc_ts)
            else:  # match in the middle
                body = '"%s", %s, "%s"' % (updated[:index], sym_loc_ts, updated[index+length:])

            if updated.startswith('concat('):
                updated = body[1:-1]  # strip start/end quotes
            else:
                updated = 'concat(%s)' % body

            ## remove any empty strings
            updated = updated.replace(', ""', '')
            updated = updated.replace('"", ', '')

    if matched:
        # A concat() function does not need to be in quotes
        # in the pv() function; a local PV does.
        if updated.startswith("loc"):
            updated = "'%s'" % updated
        updated = '=pv(%s)' % updated
        log.info("Converted %s to %s", text, updated)
    return updated


def replace_symbols(node, symbols):
    """
    Recursively replace any instance of a symbol with a local PV.
    """
    warning = False

    if len(node) == 0:
        if node.text is not None and not node.text.isspace():
            if '$' in node.text and not (node.tag in EXCLUDED_TAGS):
                node.text = try_replace(node.text, symbols)

                if node.tag in NON_PV_TAGS:
                    warning = True
    else:
        for child in node:
            if replace_symbols(child, symbols):
                warning = True

    return warning


def parse(filepath):
    if os.path.exists(filepath) or os.access(filepath, os.R_OK):
        tree = ET.parse(filepath)
        root = tree.getroot()

        mm_symbols = find_mm_symbols(root)
        if mm_symbols:
            log.info('There are %s mm_symbols:', len(mm_symbols))
            log.info('%s', mm_symbols)

            warning = replace_symbols(root, mm_symbols)
            if warning:
                log.warn(">>> Manual post-processing required: '%s' contains Label with PV-value text <<<", filepath)

            # write the new tree out to the same file
            utils.make_writeable(filepath)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
    else:
        log.warn("Skipping %s, file not found", filepath)


def build_filelist(basepath):
    """ Execute a grep on the basepath to find all files that contain a menumux
        control

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.debug("Building menu mux list.")
    proc = subprocess.Popen("find " + basepath + " -name \"*.opi\" | xargs grep -sl " + mmux.MENU_MUX_ID,
                            stdout=subprocess.PIPE,
                            shell=True)

    for line in iter(proc.stdout.readline, ''):
        filepath = line.rstrip()
        yield filepath
