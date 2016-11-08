import pkg_resources
pkg_resources.require('dls_css_utils')
import unittest
from convert import files


class OldEdlTest(unittest.TestCase):

    def test_is_old_edl_recognises_old(self):
        old_edl_file = '/dls_sw/prod/R3.14.11/support/vxStats/1-14/data/FE-IOCs.edl'
        self.assertTrue(files.is_old_edl(old_edl_file))

    def test_is_old_edl_recognises_new(self):
        new_edl_file = '/dls_sw/prod/R3.14.11/support/vxStats/1-14/data/diamond.edl'
        self.assertFalse(files.is_old_edl(new_edl_file))

    def test_is_old_edl_handles_no_version(self):
        no_version_file = '/dls_sw/prod/R3.14.12.3/support/fastfeedback/11-21/fofbApp/opi/footer.edl'
        self.assertFalse(files.is_old_edl(no_version_file))

if __name__ == '__main__':
    unittest.main()
