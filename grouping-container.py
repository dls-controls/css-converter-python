#!/usr/bin/env dls-python
'''
In both EDM and CSS grouping contained hold mutiple objects.
The general principle is the same, however: in EDM widgets which
have dimensions exceeding the grouping container are drawn, in
CSS these widgets are clipped to the grouping container area.

This script searches for grouping containers and modifies thier
dimensions so that they match the contents.
'''


import sys
import xml.etree.ElementTree as et
from utils import make_writeable, make_read_only



GROUPING_CONTAINER = 'org.csstudio.opibuilder.widgets.groupingContainer'


def get_container_size(widget):
    '''
    Returns the minimum dimensions of a container that is large enough to
    hold the widget.
    '''
    w = int(widget.find('width').text) + int(widget.find('x').text)
    h = int(widget.find('height').text) + int(widget.find('y').text)
    return w, h


def set_grouping_container_size(container_widget):
    '''
    Searches through the child widgets of the grouping container to determine
    the minium size required to contain those widgets, then sets the container
    to that size.
    '''
    w = 0
    h = 0
    children = container_widget.getchildren()
    for child in children:
        if child.tag == 'widget':
            if child.attrib['typeId'] == GROUPING_CONTAINER:
                cw, ch = set_grouping_container_size(child)
            else:
                cw, ch = get_container_size(child)
            w = max(cw, w)
            h = max(ch, h)
    container_widget.find('width').text = '%d' % w
    container_widget.find('height').text = '%d' % h
    return get_container_size(container_widget)


def parse(filepath):
    tree = et.parse(filepath)
    root = tree.getroot()

    # Set dimensions for all grouping containers
    for child in root:
        if child.tag == 'widget':
            if child.attrib['typeId'] == GROUPING_CONTAINER:
                set_grouping_container_size(child)

    # Overwrite the old file with the new tree
    make_writeable(filepath)
    tree.write(filepath, encoding='utf-8', xml_declaration=True)
    make_read_only(filepath)


if __name__ == '__main__':
    try:
        path_file = sys.argv[1]
    except IndexError:
        print "Usage: ", sys.argv[0], "<path-file>"
        sys.exit(-1)

    with open(path_file) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == ''] 

    for file in lines:
        print "Parsing file ", file
        parse(file)
