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

import xml.etree.ElementTree as et
import sys

from convert import make_writeable, make_read_only

MENU_MUX_ID = 'org.csstudio.opibuilder.widgets.edm.muxmenu'


def find_mm_symbols(node):
    '''
    Recursively find all MenuMux symbols from root node.
    '''
    # If this widget is a grouping container, any child
    # widgets need to specify coordinates plus coordinates
    # of the grouping container.
    symbols = []
    if len(node) == 0:
        return []
    else:
        for child in node:
            if child.tag == 'widget':
                if child.attrib['typeId'] == MENU_MUX_ID:
                    t = child.find('targets')
                    syms = t.findall('s')
                    symbols.extend(set(sym.text for sym in syms))
                else:
                    symbols.extend(find_mm_symbols(child))
            else:
                symbols.extend(find_mm_symbols(child))

    return symbols


def try_replace(text, symbols):
    for sym in symbols:
        sym_rep = '$(%s)' % sym
        sym_loc = "'loc://%s'" % sym
        sym_loc_ts = "toString('loc://%s')" % sym
        if sym_rep == text:
            text = sym_loc
        elif sym_rep in text:
            # Assume that the macro is only to be susbstituted once.
            index = text.index(sym_rep)
            length = len(sym_rep)
            if index == 0: # match at the start
                text = '=pv(concat(%s, "%s"))' % (sym_loc_ts, text[length:])
            elif index + length == len(text): # match at the end
                text = '=pv(concat("%s", %s))' % (text[:-length], sym_loc_ts)
            else:  # match in the middle
                text = '=pv(concat("%s", %s, "%s"))' %\
                         (text[:index], sym_loc_ts, text[index+length:])
        return text


def replace_symbols(node, symbols):
    '''
    Recursively replace any instance of a symbol with a local PV.
    '''
    if len(node) == 0:
        if node.text is not None and not node.text.isspace():
            if '$' in node.text:
                node.text = try_replace(node.text, symbols)
    else:
        for child in node:
            replace_symbols(child, symbols)

def parse(filepath):
    tree = et.parse(filepath)
    root = tree.getroot()

    mm_symbols = find_mm_symbols(root)
    print 'There are %s mm_symbols:' % len(mm_symbols)
    print mm_symbols

    replace_symbols(root, mm_symbols)

    # write the new tree out to the same file
    make_writeable(filepath)
    tree.write(filepath, encoding='utf-8', xml_declaration=True)
    make_read_only(filepath)


if __name__ == '__main__':

    try:
        path_file = sys.argv[1]
    except IndexError:
        print 'Usage: ', sys.argv[0], '<path-file>'
        sys.exit()

    with open(path_file) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == '']


    for filepath in lines:
        print 'Parsing file', filepath
        parse(filepath)


