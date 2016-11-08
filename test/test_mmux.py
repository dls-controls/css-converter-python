import pkg_resources
pkg_resources.require('dls_css_utils')
from convert.mmux import find_mm_symbols, try_replace

__author__ = 'xzl80115'
import unittest
import xml.etree.ElementTree as ET

NO_MMUX = r'<display typeId="org.csstudio.opibuilder.Display" version="1.0">' \
          r' </display>'

ONE_MMUX_ONE_SET = r'<display typeId="org.csstudio.opibuilder.Display" version="1.0">' \
                   r'<widget typeId="org.csstudio.opibuilder.widgets.edm.menumux" version="1.0">' \
                   r'<border_alarm_sensitive>false</border_alarm_sensitive> ' \
                   r'<x>416</x> <y>648</y> <width>97</width> <height>25</height> ' \
                   r'<foreground_color> <color blue="0" green="0" name="Black" red="0" /> </foreground_color> ' \
                   r'<background_color> <color blue="200" green="200" name="Canvas" red="200" /> </background_color> ' \
                   r'<font> <fontdata fontName="helvetica" height="9" style="0" /> </font> ' \
                   r'<name>EDM MenuMux</name> ' \
                   r'<items> <s>Sensor1</s> <s>Sensor2</s> </items> ' \
                   r'<target0>num</target0> ' \
                   r'<values0> <s>val01</s> <s>val02</s> </values0> ' \
                   r'<num_sets>1</num_sets> ' \
                   r'</widget>' \
                   r' </display>'

ONE_MMUX_TWO_SET = r'<display typeId="org.csstudio.opibuilder.Display" version="1.0"> ' \
                   r'<widget typeId="org.csstudio.opibuilder.widgets.edm.menumux" version="1.0">' \
                   r'<border_alarm_sensitive>false</border_alarm_sensitive> ' \
                   r'<x>416</x> <y>648</y> <width>97</width> <height>25</height> ' \
                   r'<foreground_color> <color blue="0" green="0" name="Black" red="0" /> </foreground_color> ' \
                   r'<background_color> <color blue="200" green="200" name="Canvas" red="200" /> </background_color> ' \
                   r'<font> <fontdata fontName="helvetica" height="9" style="0" /> </font> ' \
                   r'<name>EDM MenuMux</name> ' \
                   r'<items> <s>Sensor1</s> <s>Sensor2</s> </items> ' \
                   r'<target0>num</target0> ' \
                   r'<values0> <s>val01</s> <s>val02</s> </values0> ' \
                   r'<target1>count</target1> <values1> <s>1</s> <s>2</s> </values1> ' \
                   r'<num_sets>2</num_sets> ' \
                   r'</widget> ' \
                   r'</display>'

TWO_MMUX_ONE_SET = r'<display typeId="org.csstudio.opibuilder.Display" version="1.0"> ' \
                   r'<widget typeId="org.csstudio.opibuilder.widgets.edm.menumux" version="1.0">' \
                   r'<border_alarm_sensitive>false</border_alarm_sensitive> ' \
                   r'<x>416</x> <y>648</y> <width>97</width> <height>25</height> ' \
                   r'<foreground_color> <color blue="0" green="0" name="Black" red="0" /> </foreground_color> ' \
                   r'<background_color> <color blue="200" green="200" name="Canvas" red="200" /> </background_color> ' \
                   r'<font> <fontdata fontName="helvetica" height="9" style="0" /> </font> ' \
                   r'<name>EDM MenuMux</name> ' \
                   r'<items> <s>Sensor1</s> <s>Sensor2</s> </items> ' \
                   r'<target0>num</target0> ' \
                   r'<values0> <s>val01</s> <s>val02</s> </values0> ' \
                   r'<num_sets>1</num_sets> ' \
                   r'</widget> ' \
                   r'<widget typeId="org.csstudio.opibuilder.widgets.edm.menumux" version="1.0">' \
                   r'<border_alarm_sensitive>false</border_alarm_sensitive> ' \
                   r'<x>416</x> <y>648</y> <width>97</width> <height>25</height> ' \
                   r'<foreground_color> <color blue="0" green="0" name="Black" red="0" /> </foreground_color> ' \
                   r'<background_color> <color blue="200" green="200" name="Canvas" red="200" /> </background_color> ' \
                   r'<font> <fontdata fontName="helvetica" height="9" style="0" /> </font> ' \
                   r'<name>EDM MenuMux2</name> ' \
                   r'<items> <s>Current</s> <s>Lifetime</s> </items> ' \
                   r'<target0>pvname</target0> ' \
                   r'<values0> <s>SR-DI-DCCT-01:SIGNAL</s> <s>SR-DI-DCCT-01:LIFETIME</s> </values0> ' \
                   r'<num_sets>1</num_sets> ' \
                   r'</widget> ' \
                   r'</display>'


class FindSymbolTest(unittest.TestCase):

    def __init__(self, caller):
        unittest.TestCase.__init__(self, caller)

    def test_returns_empty_for_no_sets(self):
        root = ET.fromstring(NO_MMUX)

        symbols = find_mm_symbols(root)

        self.assertDictEqual(symbols, {})

    def test_returns_target_value_for_one_mm_one_set(self):
        root = ET.fromstring(ONE_MMUX_ONE_SET)

        target_nodes = root.findall('.//target0')

        symbols = find_mm_symbols(root)

        self.assertDictEqual(symbols, {"num": "val01"})

        self.assertEqual("loc://$(DID)num<VString>", target_nodes[0].text)

    def test_returns_target_value_for_one_mm_two_sets(self):
        root = ET.fromstring(ONE_MMUX_TWO_SET)

        symbols = find_mm_symbols(root)

        self.assertDictEqual(symbols, {"num": "val01", "count": "1"})

    def test_returns_target_value_for_two_mm_one_sets(self):
        root = ET.fromstring(TWO_MMUX_ONE_SET)

        symbols = find_mm_symbols(root)

        self.assertDictEqual(symbols, {"num": "val01", "pvname": "SR-DI-DCCT-01:SIGNAL"})


class TryReplaceTest(unittest.TestCase):

    def __init__(self, caller):
        unittest.TestCase.__init__(self, caller)

    def test_does_nothing_if_symbol_not_defined(self):

        symbols = {"num": "val01"}
        text = "$(d)"

        replaced = try_replace(text, symbols)

        self.assertEqual(text, replaced)

    def test_does_nothing_if_symbol_not_defined_and_loc_pv(self):

        symbols = {"num": "val01"}
        text = "loc://d(1)"

        replaced = try_replace(text, symbols)

        self.assertEqual(text, replaced)

    def test_try_replace_sets_loc_pv_if_straight_match(self):
        """ Map <attr>$(d)</attr> to <attr>loc://$(DID)d<VString>("initval")</attr>
        """

        symbols = {"d": "val01"}
        text = "$(d)"
        expected = "=pv('loc://$(DID)%s<VString>(\"%s\")')" % ("d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_prefixing_match(self):

        symbols = {"d": "val01"}
        text = "$(d)MYPVNAME"
        expected = "=pv(concat(toString('loc://$(DID)%s<VString>(\"%s\")\'), \"MYPVNAME\"))" % ("d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_appending_match(self):

        symbols = {"d": "val01"}
        text = "MYPVNAME$(d)"
        expected = "=pv(concat(\"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\')))" % ("d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_single_match(self):

        symbols = {"d": "val01"}
        text = "MYPVNAME$(d)SUFFIX"
        expected = "=pv(concat(\"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\'), \"SUFFIX\"))" % ("d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_two_matches(self):

        symbols = {"d": "val01", "e": "val2"}
        text = "$(d)$(e)"
        expected = "=pv(concat(toString('loc://$(DID)%s<VString>(\"%s\")\'), toString('loc://$(DID)%s<VString>(\"%s\")\')))"  % ("d", symbols["d"], "e", symbols["e"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_two_matches_at_end_in_order(self):
        symbols = {"d": "val01", "e": "val2"}
        text = "MYPVNAME$(d)$(e)"
        expected = "=pv(concat(\"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\'), toString('loc://$(DID)%s<VString>(\"%s\")\')))" % ("d", symbols["d"], "e", symbols["e"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_two_matches_at_end_out_of_order(self):

        symbols = {"d": "val01", "e": "val2"}
        text = "MYPVNAME$(e)$(d)"
        expected = "=pv(concat(\"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\'), toString('loc://$(DID)%s<VString>(\"%s\")\')))" % ("e", symbols["e"], "d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_two_matches_at_start_and_end_in_order(self):

        symbols = {"d": "val01", "e": "val2"}
        text = "$(d)MYPVNAME$(e)"
        expected = "=pv(concat(toString('loc://$(DID)%s<VString>(\"%s\")\'), \"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\')))" % ("d", symbols["d"], "e", symbols["e"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

    def test_try_replace_sets_concat_loc_pv_if_inserting_two_matches_at_start_and_end_out_of_order(self):

        symbols = {"d": "val01", "e": "val2"}
        text = "$(e)MYPVNAME$(d)"
        expected = "=pv(concat(toString('loc://$(DID)%s<VString>(\"%s\")\'), \"MYPVNAME\", toString('loc://$(DID)%s<VString>(\"%s\")\')))" % ("e", symbols["e"], "d", symbols["d"])

        replaced = try_replace(text, symbols)

        self.assertEqual(expected, replaced)

if __name__ == '__main__':
    unittest.main()
