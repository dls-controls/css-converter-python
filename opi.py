
import xml.etree.ElementTree as et
from collections import defaultdict

OPI_FILE = '/home/hgs15624/code/converter/vacuum/diamondVacuumOverview.opi'
OUT_FILE = '/tmp/new2.opi'

LINK = 'org.csstudio.opibuilder.widgets.linkingContainer'

new_symbol = '/home/hgs15624/.css-workspaces/w1/CSS/symbol.opi'

tree = et.parse(OPI_FILE)

root = tree.getroot()

types = defaultdict(int)
removed = 0
changed = 0
lcs = 0
nodes = 0

def remove_lcs(node):
    '''
    remove any linking container children of the node
    '''
    global removed, nodes
    nodes += 1
    if len(node) == 0:
        return
    else:
        for child in node:
            if child.tag == 'widget':
                type = child.attrib['typeId']
                if  type == LINK:
                    rules = child.findall('rules')
                    print len(rules)
                    for rule in rules:
                        rs = rule.findall('rule')
                        for r in rs:
                            rule.remove(r)
                    removed += 1
                else:
                    remove_lcs(child)
            else:
                remove_lcs(child)

def change_sym(node):
    '''
    remove any linking container children of the node
    '''
    global changed
    if len(node) == 0:
        return
    else:
        for child in node:
            if child.tag == 'widget':
                type = child.attrib['typeId']
                if  type == LINK:
                    opis = child.findall('opi_file')
                    for opi in opis:
                        opi.text = new_symbol
                        changed += 1
                else:
                    change_sym(child)
            else:
                change_sym(child)


def change_symbol(node):
    '''
    remove any linking container children of the node
    '''
    print node
    global changed, lcs
    for child in node.findall('widget'):
        lcs += 1
#        print "%dth lc" % lcs
        if child.attrib['typeId'] == LINK:
            for c in child.findall('opi_file'):
                changed += 1
#                print c.text, changed
                c.text = new_symbol

'''
for child in root.findall('widget'):
    change_symbol(root)
    for child1 in child:
        change_symbol(child1)
        try:
            types[child.attrib['typeId']] += 1
        except KeyError:
            print "no type tag"
        for child2 in child1:
            change_symbol(child2)
            for child3 in child2:
                change_symbol(child3)
'''
remove_lcs(root)
#change_sym(root)

tree.write(OUT_FILE)

print "removed %d linking containers" % removed
print "total nodes %d" % nodes
print types
