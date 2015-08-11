import unittest
from convert.dependency import DependencyParser


class TestIncrementVersion(unittest.TestCase):

    def test_returns_empty_list_if_no_depends(self):

        d = DependencyParser('/dls_sw/prod/R3.14.12.3', 'support', 'topup', '5-3')
        depends = d.find_dependencies()
        self.assertDictEqual({}, depends)

    def test_returns_empty_list_if_invalid_module(self):

        d = DependencyParser('/dls_sw/prod/R3.14.12.3', 'dummy', 'LI/TI', '5-3')
        depends = d.find_dependencies()
        self.assertDictEqual({}, depends)

    def test_get_version_returns_correct_depends_for_ioc(self):

        d = DependencyParser('/dls_sw/prod/R3.14.12.3', 'ioc', 'LI/TI', '5-3')
        depends = d.find_dependencies()

        for k, v in depends.iteritems():
            print k, v

    def test_get_version_returns_correct_depends_for_support_module(self):

        d = DependencyParser('/dls_sw/prod/R3.14.12.3', 'support', 'dlsPLC', '1-30')
        depends = d.find_dependencies()

        for k, v in depends.iteritems():
            print k, v
