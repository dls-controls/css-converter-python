#!/bin/env dls-python

import sys
import argparse

import dls_packages
import lxml.etree as et


class ArchiveViewerParser(object):
    """Parses an archive viewer XML file and presents itself as a model"""

    def __init__(self, filepath):
        # Avoid et.parse to workaround wrong file encoding
        self.root = et.XML(open(filepath).read().encode('utf16'))

    def get_start_time(self):
        return self.root.find('time_axis').find('start').text

    def get_end_time(self):
        return self.root.find('time_axis').find('end').text

    def get_pv_list(self):
        return [pv.get('name') for pv in self.root.findall('pv')]


class StripToolParser(object):
    """Parses a StripTool file and presents itself as a model"""

    END_TIME_KEY = 'Strip.Time.Timespan'

    def __init__(self, filepath):
        self.data = {}
        for line in open(filepath):
            k, v = line.split(None, 1)
            self.data[k] = v.strip()

    def get_start_time(self):
        return '-' + self.data[self.END_TIME_KEY] + 's'

    def get_end_time(self):
        return 'now'

    def get_pv_list(self):
        return [self.data[s] for s in self.data.keys() if '.Name' in s]


class DatabrowserWriter(object):
    """Create a databrowser file using a model"""

    ARCHIVE_NAME = 'All-(Primary Archiver)'
    ARCHIVE_URL = ('xnds://archiver.pri.diamond.ac.uk' +
        '/archive/cgi/ArchiveDataServer.cgi')
    ARCHIVE_KEY = '1000'

    def __init__(self, parser):
        self.parser = parser

    def write_output(self, filepath):
        document = et.ElementTree(element=self._generate_tree())
        document.write(filepath, pretty_print=True,
                encoding='utf-8', xml_declaration=True)

    def _generate_tree(self):
        root = et.Element('databrowser')
        et.SubElement(root, 'start').text = self.parser.get_start_time()
        et.SubElement(root, 'end').text = self.parser.get_end_time()
        self._generate_axes(root)
        self._generate_pv_list(root)
        return root

    def _generate_axes(self, root):
        axes = et.SubElement(root, 'axes')
        axis = et.SubElement(axes, 'axis')
        et.SubElement(axis, 'use_trace_names').text = 'false'

    def _generate_pv_list(self, root):
        pvs = et.SubElement(root, 'pvlist')
        for pv_name in self.parser.get_pv_list():
            pv = et.SubElement(pvs, 'pv')
            et.SubElement(pv, 'name').text = pv_name
            self._generate_pv_archive_data(pv)

    def _generate_pv_archive_data(self, pv):
        archive = et.SubElement(pv, 'archive')
        et.SubElement(archive, 'name').text = self.ARCHIVE_NAME
        et.SubElement(archive, 'url').text = self.ARCHIVE_URL
        et.SubElement(archive, 'key').text = self.ARCHIVE_KEY

def parse_args():
    parser = argparse.ArgumentParser(description=
            'Convert Striptool and Archive Viewer input files for CS-Studio')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--archive', help='Archive Viewer file to be converted')
    group.add_argument('--striptool', help='StripTool file to be converted')
    parser.add_argument('output', help='Output file path')
    return parser.parse_args()


args = parse_args()
if args.archive:
    model = ArchiveViewerParser(args.archive)
elif args.striptool:
    model = StripToolParser(args.striptool)
dbw = DatabrowserWriter(model)
dbw.write_output(args.output)
