#!/bin/env dls-python
"""
If a widget has no control pv, but is using a rule which has only one pv,
substitute the pv name into the control PV field.  This allows tooltip and
middle-click-copy to work.
"""
import logging as log
import os
import xml.etree.ElementTree as ET

import utils


GROUPINGCONTAINER = "org.csstudio.opibuilder.widgets.groupingContainer"
LINKINGCONTAINER = "org.csstudio.opibuilder.widgets.linkingContainer"
LABEL = "org.csstudio.opibuilder.widgets.Label"

WIDGETS_WITHOUT_CONTROL_PV = [GROUPINGCONTAINER, LINKINGCONTAINER, LABEL]


def simplify_rules(widget):
    """ If the pv_name field is empty and there is exactly one PV used in
        rules, substitute that PV into the pv_name field.  Reference that PV
        in the rule using $(pv_name).

        If there is more than one PV defined in a rule, don't do anything.
    """
    # Find all pv elements defined in a rule.
    rule_pvs = widget.findall('./rules/rule/pv')
    if len(rule_pvs) == 1:  # Exactly one PV defined in a rule.
        # Find the control PV for the widget.
        control_pv = widget.find('./pv_name')
        if control_pv is None:  # No control PV defined.
            new_control_pv = ET.Element('pv_name')
            new_control_pv.text = rule_pvs[0].text
            rule_pvs[0].text = '$(pv_name)'
            widget.append(new_control_pv)
        elif control_pv.text is None:  # Control PV name empty.
            control_pv.text = rule_pvs[0].text
            rule_pvs[0].text = '$(pv_name)'


def parse(filepath):
    try:
        if os.path.exists(filepath) or os.access(filepath, os.R_OK):
            tree = ET.parse(filepath)
            root = tree.getroot()

            for widget in root.findall(".//widget"):
                # Some widgets do not have a PV Name field.
                if widget.attrib['typeId'] not in WIDGETS_WITHOUT_CONTROL_PV:
                    if widget.find('./rules'):
                        simplify_rules(widget)

            # write the new tree out to the same file
            utils.make_writeable(filepath)
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
    return utils.find_opi_files(basepath)
