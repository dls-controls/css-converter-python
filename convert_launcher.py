#!/usr/bin/env dls-python
'''
Simple script to walk through the Launcher's applications.xml file
and convert each EDM instance it finds.
'''

import xml.etree.ElementTree as et
import os

from convert import Converter

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'
APPS_XML = os.path.join(LAUNCHER_DIR, 'applications.xml')

tree = et.parse(APPS_XML)

root = tree.getroot()

def get_apps(node):
    apps = []
    if node.tag == 'button':
        name = node.get('text')
        cmd = node.get('command')
        args = node.get('args', default="").split()
        print name
        apps.append((name, cmd, args))
    else:
        for child in node:
            apps.extend(get_apps(child))
    return apps

launcher_apps = get_apps(root)


for app, cmd, args in launcher_apps:
    print "cmd is", cmd
    if not os.path.isabs(cmd):
        cmd = os.path.join(LAUNCHER_DIR, cmd)
    c = Converter(cmd, args, [], './project/opi2')
    c.convert_opis(False)
    c.copy_scripts(False)
