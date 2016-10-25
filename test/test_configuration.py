from pkg_resources import require
from convert import coordinates, configuration

require('mock')

import unittest


class ConfigurationTest(unittest.TestCase):

    def test_dependency_list_constructed_correctly_from_list_of_one_coord(self):
        coord = coordinates.create('root', 'area', 'module01', 'version01')
        result = configuration._dependency_list_to_string([coord])

        self.assertEqual("module01/version01", result)

    def test_dependency_list_constructed_correctly_from_list_of_three_coords(self):
        coords = [
            coordinates.create('root', 'area1', 'module01', 'version01'),
            coordinates.create('root', 'area2', 'module02', 'version02'),
            coordinates.create('root', 'area3', 'module03', 'version03')]
        result = configuration._dependency_list_to_string(coords)

        self.assertEqual(
            "module01/version01;module02/version02;module03/version03", result)

    def test_dependency_list_is_constructed_correctly_from_empty_list(self):
        result = configuration._dependency_list_to_string([])

        self.assertEqual("", result)

    def test_dependency_list_rebuilt_correctly_from_source_with_single_depend_with_version(self):
        source = "TMBF:1-4;"
        expected = "TMBF/1-4"

        depend_strings = configuration._split_value_list(source)
        depends = configuration._parse_dependency_list(depend_strings, None)

        output = configuration._dependency_list_to_string(depends)
        self.assertEqual(expected, output)

    def test_dependency_list_rebuilt_correctly_from_source_with_explicit_version(self):

        source = "motor:6-8-1dls4-3;vxStats:1-14-1;enzLoCuM4:2-31;" \
                 "pmacUtil:4-33;TimingTemplates:6-8;4chTimer:3-2;" \
                 "vacuumValve:4-22;TMBF:3-3;Libera:2.05.16;IsaPBPM:1-1"

        depend_strings = configuration._split_value_list(source)
        depends = configuration._parse_dependency_list(depend_strings, None)

        output = configuration._dependency_list_to_string(depends)
        self.assertEqual(source.replace(':', '/'), output)

    def test_dependency_list_parsed_correctly_from_source_with_versions(self):
            source = "motor:6-8-1dls4-3;vxStats:1-14-1;enzLoCuM4:2-31;" \
                     "pmacUtil:4-33;TimingTemplates:6-8;4chTimer:3-2;" \
                     "vacuum/vacuumValve:4-22"

            expected = [coordinates.create(root=None, area='support', module='motor', version='6-8-1dls4-3'),
                        coordinates.create(root=None, area='support', module='vxStats', version='1-14-1'),
                        coordinates.create(root=None, area='support', module='enzLoCuM4', version='2-31'),
                        coordinates.create(root=None, area='support', module='pmacUtil', version='4-33'),
                        coordinates.create(root=None, area='support', module='TimingTemplates', version='6-8'),
                        coordinates.create(root=None, area='support', module='4chTimer', version='3-2'),
                        coordinates.create(root=None, area='support', module='vacuum/vacuumValve', version='4-22')]

            depend_strings = configuration._split_value_list(source)
            depends = configuration._parse_dependency_list(depend_strings, None)

            self.assertListEqual(expected, depends)

    def test_dependency_parsed_correctly_from_source_with_single_depend_no_version(self):
        source = "TMBF"
        expected = coordinates.create(root=None, area='support', module='TMBF', version=None)

        depend_strings = configuration._split_value_list(source)
        depends = configuration._parse_dependency_list(depend_strings, None)
        self.assertListEqual([expected], depends)

    def test_dependency_parsed_correctly_from_source_with_single_depend_with_version(self):
        source = "TMBF:1-1"
        expected = coordinates.create(root=None, area='support', module='TMBF', version='1-1')

        depend_strings = configuration._split_value_list(source)
        depends = configuration._parse_dependency_list(depend_strings, None)
        self.assertListEqual([expected], depends)
