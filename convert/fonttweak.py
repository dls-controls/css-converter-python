#!/bin/env dls-python
"""
Simply change the fonts in OPI files according to FONT_MAP.
"""
import xml.etree.ElementTree as ET
import os
import logging as log

import utils


FONT_MAP = {"arial": "liberation sans",
            "helvetica": "liberation sans",
            "courier": "monospace"}


def change_font(font_element):
    name = font_element.get("fontName")
    if name is None:
        return
    if name in FONT_MAP:
        font_element.set("fontName", FONT_MAP[name])


def parse(filepath):
    try:
        if os.path.exists(filepath) or os.access(filepath, os.R_OK):
            tree = ET.parse(filepath)
            root = tree.getroot()

            for font_element in root.findall(".//fontdata"):
                change_font(font_element)

            # write the new tree out to the same file
            utils.make_writeable(filepath)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        else:
            log.warn("Skipping %s, file not found", filepath)
    except ET.ParseError:
        log.warn("Skipping %s, XML invalid", filepath)


def build_filelist(basepath):
    """ Just find all OPI files.

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.info("Building fonttweak list.")
    files = []
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                files.append(os.path.join(dirpath, filename))

    return files
