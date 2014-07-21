'''
Ordering of elements in BOY screens are determined only by their 
position in the xml file.

Use elementtree to move:
 - invisible related displays
 - grouping container containing only invisible related displays
to the bottom of an opi file, meaning that they are rendered
at the top.
'''

import xml.etree.ElementTree as et
import sys

try:
    OPI_FILE = sys.argv[1]
except IndexError:
    print "Usage: ", sys.argv[0], "<opi-file>"
    sys.exit()



def new_name(old_name):
    '''
    Append a 2 to the name of the file.
    '''
    parts = old_name.split('.')
    return '%s2.%s' % (''.join(parts[:-1]), parts[-1])


OUT_FILE = new_name(OPI_FILE)
print OPI_FILE
print OUT_FILE

# BOY type IDs
LINK = 'org.csstudio.opibuilder.widgets.linkingContainer'
GROUP = 'org.csstudio.opibuilder.widgets.groupingContainer'
RECTANGLE = 'org.csstudio.opibuilder.widgets.Rectangle'


# invisible components are all rectangles, since buttons
# cannot be transparent
def invisible_related(node):
    if not node.tag == 'widget':
        return False
    if not node.attrib['typeId'] == RECTANGLE:
        return False
    print "inv rel", node.attrib['typeId']
    trans = False
    rel = False
    for child in node:
        if child.tag == 'transparent':
            trans = child.text == 'true'
        if child.tag == 'name':
            print child.text
            rel = child.text == 'EDM related display'
    if rel:
        print "returning true for", node
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
                    print "returning false from fr"
                    return False
        print "returning true from fr"
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

    print "returning ", removed
    return removed

# parse the files
tree = et.parse(OPI_FILE)
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
tree.write(OPI_FILE, encoding='utf-8', xml_declaration=True)
