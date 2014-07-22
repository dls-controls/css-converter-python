#!/usr/bin/env dls-python
'''
Ordering of elements in BOY screens are determined only by their 
position in the xml file.

Use elementtree to move:
 - invisible related displays
 - grouping container containing only invisible related displays
to the bottom of an opi file, meaning that they are rendered
at the top.

Run this script after transforming all the relevant areas.
'''

import xml.etree.ElementTree as et
import sys

try:
    path_file = sys.argv[1]
except IndexError:
    print "Usage: ", sys.argv[0], "<path-file>"
    sys.exit()

with open(path_file) as f:
    lines = f.readlines()
    lines = [line.strip() for line in lines if not line.startswith('#')]
    lines = [line.strip() for line in lines if not line == '']


# BOY type IDs
LINK = 'org.csstudio.opibuilder.widgets.linkingContainer'
GROUP = 'org.csstudio.opibuilder.widgets.groupingContainer'
RECTANGLE = 'org.csstudio.opibuilder.widgets.Rectangle'
BOOL_BUTTON = 'org.csstudio.opibuilder.widgets.BoolButton'
ACTION_BUTTON = 'org.csstudio.opibuilder.widgets.ActionButton'

REL_NAME = 'EDM related display'
SHELL_NAME = 'EDM shell command'


# invisible components are all rectangles, since buttons
# cannot be transparent
def invisible_related(node):
    if not node.tag == 'widget':
        return False
    if not node.attrib['typeId'] == RECTANGLE:
        return False
    trans = True
    rel = False
    for child in node:
        if child.tag == 'transparent':
            trans = child.text == 'true'
        if child.tag == 'name':
            rel = (child.text == REL_NAME or child.text == SHELL_NAME)
    return rel and trans


def for_raising(node):
    '''
    Determine if any element is to be raised to the top.
    '''
    assert node.tag == 'widget'

    type = node.attrib['typeId']
    if type == GROUP:
        print "fr for group"
        for child in node:
            if child.tag == 'widget':
                if not invisible_related(child):
                    return False
        return True
    elif type == RECTANGLE:
        return invisible_related(node)
    else:
        return False

def find_groups(node):
    '''
    remove any rule from linking containers which are any children of the node
    '''
    removed = []
    if len(node) == 0:
        return []
    else:
        for child in node:
            if child.tag == 'widget':
                if for_raising(child):
                    print "removing", child.attrib['typeId']
                    node.remove(child)
                    removed.append(child)
                else:
                    removed.extend(find_groups(child))
            else:
                removed.extend(find_groups(child))

    return removed


def fix_file(path):
    tree = et.parse(path)
    root = tree.getroot()

    clickables = find_groups(root)
    print "There are %s clickables." % len(clickables)
    # simply put all the invisible clickable elements at the bottom
    # of the XML, where they are rendered last
    root.extend(clickables)

    print "\n\nthe clickables are:"

    for clicker in clickables:
        for child in clicker:
            if child.tag == 'name':
                print child.text


    # write the new tree out to the same file
    tree.write(path, encoding='utf-8', xml_declaration=True)


for file in lines:
    print "starting file ", file
    fix_file(file)


