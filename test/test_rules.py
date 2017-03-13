from convert import rules
import xml.etree.ElementTree as et


NO_RULES = '<widget><a>b</a></widget>'
PV_DEFINED = '<widget><pv_name>pv1</pv_name><rules><rule><pv>pv2</pv></rule></rules></widget>'
NO_PV_DEFINED = '<widget><rules><rule><pv>pv2</pv></rule></rules></widget>'
NO_PV_NAME = '<widget><pv_name></pv_name><rules><rule><pv>pv2</pv></rule></rules></widget>'


def test_simplify_rules_does_not_change_widget_with_no_rules():
    widget = et.fromstring(NO_RULES)
    rules.simplify_rules(widget)
    assert et.tostring(widget) == NO_RULES


def test_simplify_rules_does_not_change_widget_with_pv_name():
    widget = et.fromstring(PV_DEFINED)
    rules.simplify_rules(widget)
    assert et.tostring(widget) == PV_DEFINED


def test_simplify_rules_adds_pv_element_if_not_defined():
    widget = et.fromstring(NO_PV_DEFINED)
    rules.simplify_rules(widget)
    assert widget.find('./pv_name').text == 'pv2'


def test_simplify_rules_amends_pv_element_if_empty():
    widget = et.fromstring(NO_PV_NAME)
    rules.simplify_rules(widget)
    assert widget.find('./pv_name').text == 'pv2'
