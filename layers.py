#!/usr/bin/env dls-python
'''
Ordering of elements in BOY screens are determined only by their 
position in the xml file.

Create an invisible Rectangle on top of any clickable 
area which has the same click action.  Keep track of x and y
position of any parent grouping containers, so that the 
new Rectangle ends up in the correct place.

Run this script after transforming all the relevant areas.  Note 
that since the widgets it makes are clickable, running this 
script again will make yet more widgets!
'''

import xml.etree.ElementTree as et
import sys
import copy

from utils import make_writeable, make_read_only

# BOY type IDs
LINK = 'org.csstudio.opibuilder.widgets.linkingContainer'
GROUP = 'org.csstudio.opibuilder.widgets.groupingContainer'
RECTANGLE = 'org.csstudio.opibuilder.widgets.Rectangle'
BOOL_BUTTON = 'org.csstudio.opibuilder.widgets.BoolButton'
ACTION_BUTTON = 'org.csstudio.opibuilder.widgets.ActionButton'

REL_NAME = 'EDM related display'
SHELL_NAME = 'EDM shell command'


def clickable_widget(node):
    anode = node.find('actions')
    if anode is not None:
        if node.attrib['typeId'] in [ACTION_BUTTON, BOOL_BUTTON]:
            return True
        else:
            return anode.attrib['hook'] == 'true'
    return False


def find_clickables(node, x, y):
    '''
    Recursively find all nodes which accept a mouse click
    '''
    # If this widget is a grouping container, any child
    # widgets need to specify coordinates plus coordinates
    # of the grouping container.
    if node.tag == 'widget' and node.attrib['typeId'] == GROUP:
        x += int(node.find('x').text)
        y += int(node.find('y').text)
    clickables = []
    if len(node) == 0:
        return []
    else:
        for child in node:
            if child.tag == 'widget':
                if clickable_widget(child):
                    clickables.append((child, x, y))
                else:
                    clickables.extend(find_clickables(child, x, y))
            else:
                clickables.extend(find_clickables(child, x, y))

    return clickables


def create_new_clicker(node, x, y):
    '''
    Create new transparent rectangle.  Fetch the appropriate children of 
    the node and copy them to the new widget.
    Change position to that relative to any grouping containers.
    '''
    rect = et.Element('widget')
    rect.attrib['typeId'] = RECTANGLE
    v = et.SubElement(rect, 'transparent')
    v.text = 'true'
    n = et.SubElement(rect, 'name')
    n.text = 'Duplicate EDM widget'

    atag = node.find('actions')
    new_atag = copy.deepcopy(atag)
    new_atag.attrib['hook'] = 'true'
    rect.append(new_atag)

    new_xtag = et.SubElement(rect, 'x')
    xtag = node.find('x')
    new_xtag.text = str(int(xtag.text) + x)
    rect.append(new_xtag)

    new_ytag = et.SubElement(rect, 'y')
    ytag = node.find('y')
    new_ytag.text = str(int(ytag.text) + y)
    rect.append(new_ytag)

    widthtag = node.find('width')
    rect.append(widthtag)
    heighttag = node.find('height')
    rect.append(heighttag)

    return rect


def parse(path):
    tree = et.parse(path)
    root = tree.getroot()

    clickables = find_clickables(root, 0, 0)
    print "There are %s clickables." % len(clickables)

    newcs = []
    for clicker in clickables:
        newcs.append(create_new_clicker(*clicker))

    root.extend(newcs)

    # write the new tree out to the same file
    make_writeable(file)
    tree.write(file, encoding='utf-8', xml_declaration=True)
    make_read_only(file)


if __name__ == '__main__':

    try:
        path_file = sys.argv[1]
    except IndexError:
        print "Usage: ", sys.argv[0], "<path-file>"
        sys.exit()

    with open(path_file) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == '']


    for file in lines:
        print "Parsing file ", file
        parse(file)


