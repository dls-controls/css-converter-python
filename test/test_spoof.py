
from convert.spoof import _from_configure_ioc, _is_edm_script

import unittest

class TestSpoof(unittest.TestCase):

    def test_configure_ioc(self):
        """
        This might fail when the actual output changes!
        """
        out = _from_configure_ioc('CSS-gui')
        self.assertEqual(out, '/dls_sw/work/common/CSS/css')

    def test_configure_ioc_with_relative_path(self):
        """
        This might fail when the actual output changes!
        """
        out = _from_configure_ioc('CS-DI-IOC-09', 'sofb-gui')
        self.assertEqual(out, '/dls_sw/prod/R3.14.12.3/ioc/CS/CS-DI-IOC-09/1-46/sofb-gui')

    def test_is_edm_script_fofb(self):
        out = _is_edm_script('/dls_sw/prod/R3.14.12.3/support/fastfeedback/11-11/fofbApp/opi/fofb-gui')
        self.assertTrue(out)

    def test_is_edm_script_fofb(self):
        out = _is_edm_script('/dls_sw/prod/R3.14.12.3/support/fastfeedback/11-11/fofbApp/opi/fofb-gui')
        self.assertTrue(out)
