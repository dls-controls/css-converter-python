#!/bin/env dls-python
"""
If a widget has no control pv, but is using a rule which has only one pv,
substitute the pv name into the control PV field.  This allows tooltip and
middle-click-copy to work.
"""
import logging as log
import os
import xml.etree.ElementTree as ET

from utils import make_writeable


def simplify_rules(widget):
    """ If the pv_name field is empty and there is exactly one PV used in
        rules, substitute that PV into the pv_name field.
    """
    pvs = widget.findall('./rules/rule/pv')
    if len(pvs) == 1:
        pv = widget.find('./pv_name')
        if pv is None:
            pv = ET.Element('pv_name')
            pv.text = pvs[0].text
            pvs[0].text = '$(pv_name)'
            widget.append(pv)
        elif pv.text is None:
            pv.text = pvs[0].text
            pvs[0].text = '$(pv_name)'


def parse(filepath):
    try:
        if os.path.exists(filepath) or os.access(filepath, os.R_OK):
            tree = ET.parse(filepath)
            root = tree.getroot()

            for widget in root.findall(".//widget"):
                if widget.find('./rules'):
                    simplify_rules(widget)

            # write the new tree out to the same file
            make_writeable(filepath)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        else:
            log.warn("Skipping %s, file not found", filepath)
    except ET.ParseError:
        log.warn("Skipping %s, XML invalid", filepath)


def build_filelist(basepath):
    """ Find all OPI files.

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.info("Building rules list.")
    files = []
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                files.append(os.path.join(dirpath, filename))

    return files
