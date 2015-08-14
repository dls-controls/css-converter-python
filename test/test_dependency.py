import unittest
from convert import coordinates
from convert.dependency import DependencyParser


class TestDependencies(unittest.TestCase):

    def test_returns_empty_list_if_no_depends(self):
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3',  'support', 'topup', '5-3')
        d = DependencyParser(coord)
        depends = d.find_dependencies()
        self.assertDictEqual({}, depends)

    def test_returns_empty_list_if_invalid_module(self):

        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'dummy', 'LI/TI', '5-3')
        d = DependencyParser(coord)
        depends = d.find_dependencies()
        self.assertDictEqual({}, depends)

    def test_get_version_returns_correct_depends_for_ioc(self):
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'ioc', 'LI/TI', '5-3')
        d = DependencyParser(coord)
        depends = d.find_dependencies()

        print "Searching: %s" % d._module_path
        for k, v in depends.iteritems():
            self.assertIn(v.area, ('ioc', 'support'))
            self.assertEqual('/dls_sw/prod/R3.14.12.3', v.root)
            print k, v

    def test_get_version_returns_correct_depends_for_support_module(self):
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'dlsPLC', '1-30')
        d = DependencyParser(coord)
        depends = d.find_dependencies()

        print "Searching: %s" % d._module_path
        for k, v in depends.iteritems():
            self.assertIn(v.area, ('ioc', 'support'))
            self.assertEqual('/dls_sw/prod/R3.14.12.3', v.root)
            print k, v

    def test_depends_parser_asserts_if_coordinate_does_not_contain_version(self):
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'ioc', 'LI/TI', None)
        self.assertRaises(AssertionError, DependencyParser, coord)

    def test_depends_parser_includes_additional_dependency_if_one_passed_none_discovered(self):

        additional = [('calc', '3-1')]
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'dummy', 'LI/TI', '5-3')
        d = DependencyParser(coord, additional)

        depends = d.find_dependencies()
        expected = {'calc':coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'calc', '3-1')}
        self.assertDictEqual(expected, depends)

    def test_depends_parser_includes_additional_dependency_if_one_passed_some_discovered(self):

        additional = [('test', '3-1dls4')]
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'dlsPLC', '1-30')
        d = DependencyParser(coord, additional)

        depends = d.find_dependencies()
        expected = {'test':coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'test', '3-1dls4')}
        self.assertDictContainsSubset(expected, depends)
        self.assertTrue(len(depends) > 1)

    def test_depends_parser_includes_additional_dependencies_if_many_passed_none_discovered(self):

        additional = [('test', '3-1dls4'), ('test2', '5-2')]
        coord = coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'dummy', '1-30')
        d = DependencyParser(coord, additional)

        depends = d.find_dependencies()
        expected = {'test':coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'test', '3-1dls4'),
                    'test2':coordinates.create('/dls_sw/prod/R3.14.12.3', 'support', 'test2', '5-2')}
        self.assertDictEqual(expected, depends)
