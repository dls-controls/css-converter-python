from convert.spoof import _from_configure_ioc, _is_edm_script
import unittest


class TestSpoof(unittest.TestCase):
    """
    A lot of these tests are fragile because they depend on the filesystem
    setup.
    """

    def test_configure_ioc(self):
        """
        This might fail if certain locations change.
        """
        out = _from_configure_ioc('CSS-gui')
        print(out)
        self.assertTrue('dls_sw' in out)
        self.assertTrue('css' in out)

    def test_configure_ioc_with_relative_path(self):
        """
        This might fail if certain locations change.
        """
        out = _from_configure_ioc('CS-DI-IOC-09', 'sofb-gui')
        self.assertTrue('dls_sw' in out)
        self.assertTrue(out.endswith('sofb-gui'))

    def test_is_edm_script_fofb(self):
        """
        This might fail if certain locations change.
        """
        out = _is_edm_script('/dls_sw/prod/R3.14.12.3/support/fastfeedback/11-21/fofbApp/opi/fofb-gui')
        self.assertTrue(out)


if __name__ == '__main__':
    unittest.main()
