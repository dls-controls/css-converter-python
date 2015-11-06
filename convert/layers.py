#!/usr/bin/env dls-python
"""
Ordering of elements in BOY screens are determined only by their
position in the xml file.

Create an invisible Rectangle on top of any clickable
area which has the same click action.  Keep track of x and y
position of any parent grouping containers, so that the
new Rectangle ends up in the correct place.

Run this script after transforming all the relevant areas.  Note
that since the widgets it makes are clickable, running this
script again will make yet more widgets!
"""

import xml.etree.ElementTree as et
import copy
import logging as log

import utils

# BOY type IDs
LINK = 'org.csstudio.opibuilder.widgets.linkingContainer'
GROUP = 'org.csstudio.opibuilder.widgets.groupingContainer'
RECTANGLE = 'org.csstudio.opibuilder.widgets.Rectangle'
BOOL_BUTTON = 'org.csstudio.opibuilder.widgets.BoolButton'
ACTION_BUTTON = 'org.csstudio.opibuilder.widgets.ActionButton'
MENU_BUTTON = 'org.csstudio.opibuilder.widgets.MenuButton'

REL_NAME = 'EDM related display'
SHELL_NAME = 'EDM shell command'


def clickable_widget(node):
    anode = node.find('actions')
    if anode is not None:
        if node.attrib['typeId'] in [ACTION_BUTTON, BOOL_BUTTON, MENU_BUTTON]:
            return True
        else:
            return anode.attrib['hook'] == 'true'
    return False


def find_clickables(node, x, y):
    """
    Recursively find all nodes which accept a mouse click
    """
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
    """
    If the node is a menu button, it is already invisible.  A copy
    can be put on top.

    Otherwise, create new transparent rectangle.  Fetch the appropriate
    children of the node and copy them to the new widget.

    Change position to that relative to any grouping containers.
    """

    if node.attrib['typeId'] == MENU_BUTTON:
        nnode = copy.deepcopy(node)
        xtag = nnode.find('x')
        xtag.text = str(int(xtag.text) + x)
        ytag = nnode.find('y')
        ytag.text = str(int(ytag.text) + y)
    else:
        nnode = et.Element('widget')
        nnode.attrib['typeId'] = RECTANGLE
        v = et.SubElement(nnode, 'transparent')
        v.text = 'true'
        n = et.SubElement(nnode, 'name')
        n.text = 'Duplicate EDM widget'

        atag = node.find('actions')
        new_atag = copy.deepcopy(atag)
        new_atag.attrib['hook'] = 'true'
        nnode.append(new_atag)

        pvtag = node.find('pv_name')
        if pvtag is not None:
            nnode.append(pvtag)

        new_xtag = et.SubElement(nnode, 'x')
        xtag = node.find('x')
        new_xtag.text = str(int(xtag.text) + x)
        nnode.append(new_xtag)

        new_ytag = et.SubElement(nnode, 'y')
        ytag = node.find('y')
        new_ytag.text = str(int(ytag.text) + y)
        nnode.append(new_ytag)

        widthtag = node.find('width')
        nnode.append(widthtag)
        heighttag = node.find('height')
        nnode.append(heighttag)

    return nnode


def parse(path):
    tree = et.parse(path)
    root = tree.getroot()

    clickables = find_clickables(root, 0, 0)
    log.info("There are %s clickables.", len(clickables))

    newcs = []
    for clicker in clickables:
        newcs.append(create_new_clicker(*clicker))

    root.extend(newcs)

    # write the new tree out to the same file
    utils.make_writeable(path)
    tree.write(path, encoding='utf-8', xml_declaration=True)

