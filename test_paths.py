
import paths

import unittest


class UpdatePathsTest(unittest.TestCase):

    def test_index_path_no_recurse_in_prod(self):
        '''
        Not a true unit test since it depends on the prod filesystem
        being available.
        '''
        root = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi'
        path = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi'
        index = paths._index_dir(root, path, False)
        contents = {'runtmbf': ('TMBF', 'opi'),
                    'tmbf': ('TMBF', 'opi'),
                    'tmbf_launcher.opi': ('TMBF', 'opi'),
                    'scripts': ('TMBF', 'opi')}

        self.assertEqual(index, contents)

    def test_index_path_recurse_in_prod(self):
        '''
        Not a true unit test since it depends on the prod filesystem
        being available.
        '''
        root = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi'
        path = '/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.8/opi'
        index = paths._index_dir(root, path, True)
        contents = {'tmbf/debug.opi': ('TMBF', 'opi'),
                    'scripts/set_adc_offset': ('TMBF', 'opi'),
                    'tmbf/window.opi': ('TMBF', 'opi'),
                    'tmbf/one_tune.opi': ('TMBF', 'opi'),
                    'tmbf/dac_minmax.opi': ('TMBF', 'opi'),
                    'tmbf/fast_buffer.opi': ('TMBF', 'opi'),
                    'tmbf/sensors.opi': ('TMBF', 'opi'),
                    'tmbf/peaks.opi': ('TMBF', 'opi'),
                    'tmbf/peak_graphs.opi': ('TMBF', 'opi'),
                    'tmbf/dac_setup.opi': ('TMBF', 'opi'),
                    'scripts/setup_tunemeasurement': ('TMBF', 'opi'),
                    'tmbf/tune_waveform_log.opi': ('TMBF', 'opi'), 
                    'runtmbf': ('TMBF', 'opi'), 
                    'scripts/set_one_bunch': ('TMBF', 'opi'),
                    'tmbf/fir_state.opi': ('TMBF', 'opi'),
                    'tmbf/tune.opi': ('TMBF', 'opi'),
                    'tmbf_launcher.opi': ('TMBF', 'opi'),
                    'tmbf/tmbf_simple.opi': ('TMBF', 'opi'),
                    'tmbf/triggers.opi': ('TMBF', 'opi'),
                    'tmbf/fir_waveforms.opi': ('TMBF', 'opi'),
                    'tmbf/tune_follow.opi': ('TMBF', 'opi'),
                    'tmbf/tune_waveform_linear.opi': ('TMBF', 'opi'),
                    'tmbf/seq_state.opi': ('TMBF', 'opi'),
                    'tmbf/control.opi': ('TMBF', 'opi'),
                    'tmbf/basic_tune.opi': ('TMBF', 'opi'),
                    'tmbf/ddr_ram.opi': ('TMBF', 'opi'),
                    'tmbf/sequencer.opi': ('TMBF', 'opi'),
                    'tmbf/adc_setup.opi': ('TMBF', 'opi'),
                    'tmbf/bunch_waveforms.opi': ('TMBF', 'opi'),
                    'tmbf/tune_follow_debug.opi': ('TMBF', 'opi'),
                    'tmbf/bunch_state.opi': ('TMBF', 'opi'),
                    'tmbf/detector.opi': ('TMBF', 'opi'),
                    'tmbf/super_seq.opi': ('TMBF', 'opi'),
                    'tmbf/restart.opi': ('TMBF', 'opi'),
                    'tmbf/iq_monitor.opi': ('TMBF', 'opi'),
                    'tmbf/adc_minmax.opi': ('TMBF', 'opi'),
                    'tmbf/tmbf_overview.opi': ('TMBF', 'opi'),
                    'scripts/TMBF_tune.config': ('TMBF', 'opi')}
        self.assertEqual(index, contents)

if __name__ == '__main__':
    unittest.main()
