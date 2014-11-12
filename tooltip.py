#!/usr/bin/env dls-python
'''
The default tooltip for any widget which may have a PV attached 
is "$(pv_name)\n%(pv_value)". If no PV is attached, this creates
a very ugly tooltip.

This script iterates through widgets and removes the default tooltip
if necessary.
'''

import xml.etree.ElementTree as et
import sys

from utils import make_writeable, make_read_only


def correct_tooltips(node):
    '''
    Recursively check each widget to see if it has a pv_name property.
    If so, and it is empty, remove the default tooltip.
    '''
    # If this widget is a grouping container, any child
    # widgets need to specify coordinates plus coordinates
    # of the grouping container.
    if node.tag == 'widget':
        pv_node = node.find('pv_name')
        tooltip_node = node.find('tooltip')
        if pv_node is not None:
            if pv_node.text == '' or pv_node.text is None:
                if tooltip_node is not None:
                    tooltip_node.text = ''
                else:
                    new_tooltip_node = et.SubElement(node, 'tooltip')

    for child in node:
        correct_tooltips(child)

def parse(path):
    '''
    Parse, correct, and rewrite OPI file with new tooltips.
    '''
    tree = et.parse(path)
    root = tree.getroot()

    correct_tooltips(root)

    # write the new tree out to the same file
    make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    make_read_only(path)


if __name__ == '__main__':

    try:
        file_to_parse = sys.argv[1]
    except IndexError:
        print "Usage: ", sys.argv[0], "<file-to-parse>"
        sys.exit()

    parse(file_to_parse)
