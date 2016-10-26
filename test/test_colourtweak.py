#!/bin/env dls-python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from convert import colourtweak

import unittest
import xml.etree.ElementTree as ET
import difflib

DISPLAY = """<display typeId="org.csstudio.opibuilder.Display" version="1.0">
  <x>97</x>
  <y>277</y>
  <width>1305</width>
  <height>500</height>
  <font>
    <fontdata fontName="arial" height="12" style="0" />
  </font>
  <foreground_color>
    <color blue="0" green="0" name="Black" red="0" />
  </foreground_color>
  <background_color>
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="1" green="200" name="LINAC Canvas" red="200" />
    <color blue="2" green="200" name="FE Canvas" red="200" />
    <color blue="3" green="200" name="RING Canvas" red="200" />
    <color blue="4" green="200" name="TARGET Canvas" red="200" />
    <color blue="5" green="200" name="CF Canvas" red="200" />
    <color blue="6" green="200" name="UNMS Canvas" red="200" />
  </background_color>
  <name>Six Circle Diffractometer Control - $(device)</name>
  <show_grid>true</show_grid>
  <grid_space>5</grid_space>
</display>"""

DISPLAY_TWK = """<display typeId="org.csstudio.opibuilder.Display" version="1.0">
  <x>97</x>
  <y>277</y>
  <width>1305</width>
  <height>500</height>
  <font>
    <fontdata fontName="arial" height="12" style="0" />
  </font>
  <foreground_color>
    <color blue="0" green="0" name="Black" red="0" />
  </foreground_color>
  <background_color>
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
  </background_color>
  <name>Six Circle Diffractometer Control - $(device)</name>
  <show_grid>true</show_grid>
  <grid_space>5</grid_space>
</display>"""

DISPLAY_ANON_COLOUR = """<display typeId="org.csstudio.opibuilder.Display" version="1.0">
  <x>97</x>
  <y>277</y>
  <width>1305</width>
  <height>500</height>
  <font>
    <fontdata fontName="arial" height="12" style="0" />
  </font>
  <foreground_color>
    <color blue="0" green="0" name="Black" red="0" />
  </foreground_color>
  <background_color>
    <color blue="200" green="200" red="200" />
    <color blue="1" green="200" name="LINAC Canvas" red="200" />
    <color blue="2" green="200" name="FE Canvas" red="200" />
    <color blue="3" green="200" name="RING Canvas" red="200" />
    <color blue="4" green="200" name="TARGET Canvas" red="200" />
    <color blue="5" green="200" name="CF Canvas" red="200" />
    <color blue="6" green="200" name="UNMS Canvas" red="200" />
  </background_color>
  <name>Six Circle Diffractometer Control - $(device)</name>
  <show_grid>true</show_grid>
  <grid_space>5</grid_space>
</display>"""

DISPLAY_ANON_COLOUR_TWK = """<display typeId="org.csstudio.opibuilder.Display" version="1.0">
  <x>97</x>
  <y>277</y>
  <width>1305</width>
  <height>500</height>
  <font>
    <fontdata fontName="arial" height="12" style="0" />
  </font>
  <foreground_color>
    <color blue="0" green="0" name="Black" red="0" />
  </foreground_color>
  <background_color>
    <color blue="200" green="200" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
    <color blue="200" green="200" name="Canvas" red="200" />
  </background_color>
  <name>Six Circle Diffractometer Control - $(device)</name>
  <show_grid>true</show_grid>
  <grid_space>5</grid_space>
</display>"""

LABEL = """<widget typeId="org.csstudio.opibuilder.widgets.Label" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>35</x>
    <y>5</y>
    <width>403</width>
    <height>28</height>
    <foreground_color>
      <color blue="0" green="0" name="Black" red="0" />
    </foreground_color>
    <background_color>
      <color blue="255" green="255" name="Disconn/Invalid" red="255" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="18" style="1" />
    </font>
    <name>EDM Label</name>
    <text>BtS TIMING DIAG.    BS-DI-EVR-01</text>
    <auto_size>true</auto_size>
    <border_style>0</border_style>
    <border_color>
      <color blue="0" green="0" name="Black" red="0" />
    </border_color>
    <background_color>
      <color blue="255" green="255" name="Disconn/Invalid" red="255" />
    </background_color>
    <foreground_color>
      <color blue="0" green="0" name="Black" red="0" />
    </foreground_color>
    <transparent>true</transparent>
    <horizontal_alignment>1</horizontal_alignment>
</widget>"""

LABEL_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.Label" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>35</x>
    <y>5</y>
    <width>403</width>
    <height>28</height>
    <foreground_color>
      <color blue="0" green="0" name="Text: FG" red="0" />
    </foreground_color>
    <background_color>
      <color blue="255" green="255" name="White" red="255" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="18" style="1" />
    </font>
    <name>EDM Label</name>
    <text>BtS TIMING DIAG.    BS-DI-EVR-01</text>
    <auto_size>true</auto_size>
    <border_style>0</border_style>
    <border_color>
      <color blue="0" green="0" name="Black" red="0" />
    </border_color>
    <background_color>
      <color blue="255" green="255" name="White" red="255" />
    </background_color>
    <foreground_color>
      <color blue="0" green="0" name="Text: FG" red="0" />
    </foreground_color>
    <transparent>true</transparent>
    <horizontal_alignment>1</horizontal_alignment>
</widget>"""

CHOICE = """<widget typeId="org.csstudio.opibuilder.widgets.choiceButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>96</x>
    <y>88</y>
    <width>105</width>
    <height>23</height>
    <foreground_color>
      <color blue="255" green="0" name="Controller" red="0" />
    </foreground_color>
    <background_color>
      <color blue="200" green="200" name="Canvas" red="200" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <name>EDM choice  Button</name>
    <pv_name>LI-DI-YAG-01:SET</pv_name>
    <items_from_pv>true</items_from_pv>
    <horizontal>true</horizontal>
    <selected_color>
      <color blue="187" green="187" name="Button: On" red="187" />
    </selected_color>
  </widget>"""

CHOICE_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.choiceButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>96</x>
    <y>88</y>
    <width>105</width>
    <height>23</height>
    <foreground_color>
      <color blue="192" green="0" name="Controller: FG" red="0" />
    </foreground_color>
    <background_color>
      <color blue="205" green="205" name="Controller: BG" red="205" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <name>EDM choice  Button</name>
    <pv_name>LI-DI-YAG-01:SET</pv_name>
    <items_from_pv>true</items_from_pv>
    <horizontal>true</horizontal>
    <selected_color>
      <color blue="190" green="190" name="Button: On" red="190" />
    </selected_color>
  </widget>"""

ACTIONBUTTON = """<widget typeId="org.csstudio.opibuilder.widgets.ActionButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>1170</x>
    <y>440</y>
    <width>116</width>
    <height>36</height>
    <foreground_color>
      <color blue="192" green="0" name="Exit/Quit/Kill" red="192" />
      <color blue="192" green="0" name="Shell/reldsp-alt" red="192" />
      <color blue="192" green="0" name="Related display" red="192" />
    </foreground_color>
    <background_color>
      <color blue="200" green="200" name="Canvas" red="200" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="12" style="0" />
    </font>
    <name>EDM Exit Button</name>
    <actions hook="false" hook_all="false">
      <action type="EXECUTE_JAVASCRIPT">
        <embedded>true</embedded>
        <scriptText>importPackage(Packages.org.csstudio.opibuilder.scriptUtil);ScriptUtil.closeAssociatedOPI(widget);</scriptText>
      </action>
    </actions>
    <text>Exit</text>
</widget>"""

ACTIONBUTTON_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.ActionButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>1170</x>
    <y>440</y>
    <width>116</width>
    <height>36</height>
    <foreground_color>
      <color blue="192" green="0" name="Exit: FG" red="192" />
      <color blue="0" green="0" name="Text: FG" red="0" />
      <color blue="32" green="64" name="Related Display: FG" red="128" />
    </foreground_color>
    <background_color>
      <color blue="205" green="205" name="Controller: BG" red="205" />
    </background_color>
    <font>
      <fontdata fontName="arial" height="12" style="0" />
    </font>
    <name>EDM Exit Button</name>
    <actions hook="false" hook_all="false">
      <action type="EXECUTE_JAVASCRIPT">
        <embedded>true</embedded>
        <scriptText>importPackage(Packages.org.csstudio.opibuilder.scriptUtil);ScriptUtil.closeAssociatedOPI(widget);</scriptText>
      </action>
    </actions>
    <text>Exit</text>
</widget>"""

BOOLBUTTON = """<widget typeId="org.csstudio.opibuilder.widgets.BoolButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>400</x>
    <y>1016</y>
    <width>105</width>
    <height>25</height>
    <foreground_color>
      <color blue="255" green="0" name="Controller" red="0" />
    </foreground_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <show_led>false</show_led>
    <show_boolean_label>true</show_boolean_label>
    <square_button>true</square_button>
    <rules>
      <rule name="OnOffBackgroundRule" out_exp="false" prop_id="background_color">
        <exp bool_exp="widget.getValue().booleanValue()">
          <value>
            <color blue="187" green="187" name="Button: On" red="187" />
          </value>
        </exp>
        <exp bool_exp="true">
          <value>
            <color blue="200" green="200" name="Canvas" red="200" />
          </value>
        </exp>
        <pv trig="true">$(pv_name)</pv>
      </rule>
      <rule name="OnOffBackgroundRule" out_exp="false" prop_id="background_color">
        <exp bool_exp="widget.getValue().booleanValue()">
          <value>
            <color blue="187" green="187" name="Button: On" red="187" />
          </value>
        </exp>
        <exp bool_exp="true">
          <value>
            <color blue="200" green="200" name="Canvas" red="200" />
          </value>
        </exp>
        <pv trig="true">$(pv_name)</pv>
      </rule>
    </rules>
    <name>EDM Message Button</name>
    <pv_name>$(prefix)STAT-$(suff1)1:RESDSTP</pv_name>
    <actions hook="true" hook_all="true">
      <action type="WRITE_PV">
        <pv_name>$(pv_name)</pv_name>
        <value>0</value>
      </action>
    </actions>
    <push_action_index>0</push_action_index>
    <released_action_index>1</released_action_index>
    <on_color>
      <color blue="187" green="187" name="Button: On" red="187" />
    </on_color>
    <off_color>
      <color blue="200" green="200" name="Canvas" red="200" />
    </off_color>
    <on_label>Enabling...</on_label>
    <off_label>Enable U/S</off_label>
    <toggle_button>false</toggle_button>
    <show_confirm_dialog>0</show_confirm_dialog>
  </widget>"""

BOOLBUTTON_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.BoolButton" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>400</x>
    <y>1016</y>
    <width>105</width>
    <height>25</height>
    <foreground_color>
      <color blue="192" green="0" name="Controller: FG" red="0" />
    </foreground_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <show_led>false</show_led>
    <show_boolean_label>true</show_boolean_label>
    <square_button>true</square_button>
    <rules>
      <rule name="OnOffBackgroundRule" out_exp="false" prop_id="background_color">
        <exp bool_exp="widget.getValue().booleanValue()">
          <value>
            <color blue="190" green="190" name="Button: On" red="190" />
          </value>
        </exp>
        <exp bool_exp="true">
          <value>
            <color blue="205" green="205" name="Controller: BG" red="205" />
          </value>
        </exp>
        <pv trig="true">$(pv_name)</pv>
      </rule>
      <rule name="OnOffBackgroundRule" out_exp="false" prop_id="background_color">
        <exp bool_exp="widget.getValue().booleanValue()">
          <value>
            <color blue="190" green="190" name="Button: On" red="190" />
          </value>
        </exp>
        <exp bool_exp="true">
          <value>
            <color blue="205" green="205" name="Controller: BG" red="205" />
          </value>
        </exp>
        <pv trig="true">$(pv_name)</pv>
      </rule>
    </rules>
    <name>EDM Message Button</name>
    <pv_name>$(prefix)STAT-$(suff1)1:RESDSTP</pv_name>
    <actions hook="true" hook_all="true">
      <action type="WRITE_PV">
        <pv_name>$(pv_name)</pv_name>
        <value>0</value>
      </action>
    </actions>
    <push_action_index>0</push_action_index>
    <released_action_index>1</released_action_index>
    <on_color>
      <color blue="190" green="190" name="Button: On" red="190" />
    </on_color>
    <off_color>
      <color blue="205" green="205" name="Controller: BG" red="205" />
    </off_color>
    <on_label>Enabling...</on_label>
    <off_label>Enable U/S</off_label>
    <toggle_button>false</toggle_button>
    <show_confirm_dialog>0</show_confirm_dialog>
  </widget>"""

TEXTUPDATE = """<widget typeId="org.csstudio.opibuilder.widgets.TextUpdate" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>464</x>
    <y>792</y>
    <width>97</width>
    <height>33</height>
    <foreground_color>
      <color blue="0" green="224" name="Monitor: NORMAL" red="0" />
    </foreground_color>
    <background_color>
      <color blue="105" green="105" name="Monitor BG" red="105" />
    </background_color>
    <forecolor_alarm_sensitive>true</forecolor_alarm_sensitive>
    <foreground_color>
      <color blue="0" green="224" name="Monitor: NORMAL" red="0" />
    </foreground_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <name>EDM Text Update</name>
    <pv_name>BR01C-PC-EVR-01:GCALC-OT1D</pv_name>
    <transparent>false</transparent>
    <horizontal_alignment>1</horizontal_alignment>
    <border_width>0</border_width>
    <border_style>1</border_style>
    <border_color>
      <color blue="0" green="224" name="Monitor: NORMAL" red="0" />
    </border_color>
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <precision_from_pv>true</precision_from_pv>
    <show_units>true</show_units>
    <format_type>0</format_type>
    <precision>0</precision>
    <foreground_color>
      <color blue="0" green="224" name="Monitor: NORMAL" red="0" />
    </foreground_color>
  </widget>"""

TEXTUPDATE_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.TextUpdate" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>464</x>
    <y>792</y>
    <width>97</width>
    <height>33</height>
    <foreground_color>
      <color blue="96" green="255" name="Monitor: FG" red="96" />
    </foreground_color>
    <background_color>
      <color blue="64" green="64" name="Monitor: BG" red="64" />
    </background_color>
    <forecolor_alarm_sensitive>true</forecolor_alarm_sensitive>
    <foreground_color>
      <color blue="96" green="255" name="Monitor: FG" red="96" />
    </foreground_color>
    <font>
      <fontdata fontName="arial" height="9" style="0" />
    </font>
    <name>EDM Text Update</name>
    <pv_name>BR01C-PC-EVR-01:GCALC-OT1D</pv_name>
    <transparent>false</transparent>
    <horizontal_alignment>1</horizontal_alignment>
    <border_width>0</border_width>
    <border_style>1</border_style>
    <border_color>
      <color blue="0" green="192" name="Mid Green" red="0" />
    </border_color>
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <precision_from_pv>true</precision_from_pv>
    <show_units>true</show_units>
    <format_type>0</format_type>
    <precision>0</precision>
    <foreground_color>
      <color blue="96" green="255" name="Monitor: FG" red="96" />
    </foreground_color>
  </widget>"""

BYTE = """<widget typeId="org.csstudio.opibuilder.widgets.bytemonitor" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>280</x>
    <y>180</y>
    <width>21</width>
    <height>21</height>
    <name>EDM Byte</name>
    <horizontal>false</horizontal>
    <effect_3d>false</effect_3d>
    <square_led>true</square_led>
    <on_color>
      <color blue="0" green="255" name="Green LED: On" red="0" />
      <color blue="0" green="255" name="Yellow LED: On" red="255" />
      <color blue="0" green="0" name="Red LED: On" red="255" />
      <color blue="255" green="0" name="Controller/alt" red="0" />
    </on_color>
    <off_color>
      <color blue="0" green="128" name="Green LED: Off" red="0" />
      <color blue="0" green="128" name="Yellow LED: Off" red="128" />
      <color blue="0" green="0" name="Red LED: Off" red="128" />
      <color blue="0" green="0" name="cyan-34" red="128" />
    </off_color>
    <foreground_color>
      <color blue="0" green="0" name="unknown" red="0" />
    </foreground_color>
    <pv_name>BL21B-DI-PHDGN-04:CAM:CAM:Acquire</pv_name>
    <rules>
      <rule name="onColorAlarm" out_exp="false" prop_id="on_color">
        <exp bool_exp="pvSev0==-1">
          <value>
            <color name="Invalid" />
          </value>
        </exp>
        <exp bool_exp="pvSev0==1">
          <value>
            <color name="Major" />
          </value>
        </exp>
        <exp bool_exp="pvSev0==2">
          <value>
            <color name="Minor" />
          </value>
        </exp>
        <pv trig="true">BL21B-DI-PHDGN-04:CAM:CAM:Acquire</pv>
      </rule>
    </rules>
    <bitReverse>false</bitReverse>
    <numBits>1</numBits>
    <startBit>0</startBit>
  </widget>"""

BYTE_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.bytemonitor" version="1.0">
    <border_alarm_sensitive>false</border_alarm_sensitive>
    <x>280</x>
    <y>180</y>
    <width>21</width>
    <height>21</height>
    <name>EDM Byte</name>
    <horizontal>false</horizontal>
    <effect_3d>false</effect_3d>
    <square_led>true</square_led>
    <on_color>
      <color blue="0" green="255" name="Green LED: On" red="0" />
      <color blue="0" green="255" name="Yellow LED: On" red="255" />
      <color blue="0" green="0" name="Red LED: On" red="255" />
      <color blue="255" green="240" name="Blue LED: On" red="96" />
    </on_color>
    <off_color>
      <color blue="0" green="96" name="Green LED: Off" red="0" />
      <color blue="0" green="96" name="Yellow LED: Off" red="96" />
      <color blue="0" green="0" name="Red LED: Off" red="96" />
      <color blue="96" green="64" name="Blue LED: Off" red="32" />
    </off_color>
    <foreground_color>
      <color blue="0" green="0" name="Black" red="0" />
    </foreground_color>
    <pv_name>BL21B-DI-PHDGN-04:CAM:CAM:Acquire</pv_name>
    <rules>
      <rule name="onColorAlarm" out_exp="false" prop_id="on_color">
        <exp bool_exp="pvSev0==-1">
          <value>
            <color blue="255" green="255" name="Invalid" red="255" />
          </value>
        </exp>
        <exp bool_exp="pvSev0==1">
          <value>
            <color blue="0" green="0" name="Major" red="255" />
          </value>
        </exp>
        <exp bool_exp="pvSev0==2">
          <value>
            <color blue="0" green="241" name="Minor" red="255" />
          </value>
        </exp>
        <pv trig="true">BL21B-DI-PHDGN-04:CAM:CAM:Acquire</pv>
      </rule>
    </rules>
    <bitReverse>false</bitReverse>
    <numBits>1</numBits>
    <startBit>0</startBit>
  </widget>"""

MISC_COLOURS = """<widget typeId="org.csstudio.opibuilder.widgets.Unknown" version="1.0">
    <foreground_color>
      <color blue="0" green="0" name="Disconn/Invalid" red="0" />
      <color blue="0" green="0" name="Top Shadow" red="0" />
      <color blue="0" green="0" name="grey-2" red="0" />
      <color blue="0" green="0" name="Canvas" red="0" />
      <color blue="0" green="0" name="Button: On" red="0" />
      <color blue="0" green="0" name="Wid-alt/Anno-sec" red="0" />
      <color blue="0" green="0" name="Title" red="0" />
      <color blue="0" green="0" name="grey-7" red="0" />
      <color blue="0" green="0" name="grey-8" red="0" />
      <color blue="0" green="0" name="Help" red="0" />
      <color blue="0" green="0" name="Monitor BG" red="0" />
      <color blue="0" green="0" name="Bottom Shadow" red="0" />
      <color blue="0" green="0" name="grey-12" red="0" />
      <color blue="0" green="0" name="grey-13" red="0" />
      <color blue="0" green="0" name="Black" red="0" />
      <color blue="0" green="0" name="Green LED: On" red="0" />
      <color blue="0" green="0" name="Monitor: NORMAL" red="0" />
      <color blue="0" green="0" name="Open/On" red="0" />
      <color blue="0" green="0" name="Monitor: alt" red="0" />
      <color blue="0" green="0" name="Green LED: Off" red="0" />
      <color blue="0" green="0" name="Red LED: On" red="0" />
      <color blue="0" green="0" name="Monitor: MAJOR" red="0" />
      <color blue="0" green="0" name="Shut/Off" red="0" />
      <color blue="0" green="0" name="Mon: MAJOR/unack" red="0" />
      <color blue="0" green="0" name="Red LED: Off" red="0" />
      <color blue="0" green="0" name="Controller" red="0" />
      <color blue="0" green="0" name="blue-26" red="0" />
      <color blue="0" green="0" name="blue-27" red="0" />
      <color blue="0" green="0" name="blue-28" red="0" />
      <color blue="0" green="0" name="blue-29" red="0" />
      <color blue="0" green="0" name="Controller/alt" red="0" />
      <color blue="0" green="0" name="cyan-31" red="0" />
      <color blue="0" green="0" name="cyan-32" red="0" />
      <color blue="0" green="0" name="cyan-33" red="0" />
      <color blue="0" green="0" name="cyan-34" red="0" />
      <color blue="0" green="0" name="Yellow LED: On" red="0" />
      <color blue="0" green="0" name="Monitor: MINOR" red="0" />
      <color blue="0" green="0" name="Mon: MINOR/unack" red="0" />
      <color blue="0" green="0" name="amber-38" red="0" />
      <color blue="0" green="0" name="Yellow LED: Off" red="0" />
      <color blue="0" green="0" name="Shell/reldsp-alt" red="0" />
      <color blue="0" green="0" name="orange-41" red="0" />
      <color blue="0" green="0" name="orange-42" red="0" />
      <color blue="0" green="0" name="Related display" />
      <color blue="0" green="0" name="brown-44" red="0" />
      <color blue="0" green="0" name="purple-45" red="0" />
      <color blue="0" green="0" name="Exit/Quit/Kill" red="0" />
      <color blue="0" green="0" name="purple-47" red="0" />
      <color blue="0" green="0" name="CO title" red="0" />
      <color blue="0" green="0" name="CO help" red="0" />
      <color blue="0" green="0" name="LINAC canvas" red="0" />
      <color blue="0" green="0" name="EA title" red="0" />
      <color blue="0" green="0" name="EA help" red="0" />
      <color blue="0" green="0" name="VA title" red="0" />
      <color blue="0" green="0" name="VA help" red="0" />
      <color blue="0" green="0" name="FE canvas" red="0" />
      <color blue="0" green="0" name="MA title" red="0" />
      <color blue="0" green="0" name="MA help" red="0" />
      <color blue="0" green="0" name="TI title" red="0" />
      <color blue="0" green="0" name="TI help" red="0" />
      <color blue="0" green="0" name="RING canvas" red="0" />
      <color blue="0" green="0" name="MO title" red="0" />
      <color blue="0" green="0" name="MO help" red="0" />
      <color blue="0" green="0" name="CG title" red="0" />
      <color blue="0" green="0" name="CG help" red="0" />
      <color blue="0" green="0" name="TARGET canvas" red="100" />
      <color blue="0" green="0" name="RS title" red="0" />
      <color blue="0" green="0" name="RS help" red="0" />
      <color blue="0" green="0" name="RF title" red="0" />
      <color blue="0" green="0" name="RF help" red="0" />
      <color blue="0" green="0" name="CF canvas" red="0" />
      <color blue="0" green="0" name="MP title" red="0" />
      <color blue="0" green="0" name="MP help" red="0" />
      <color blue="0" green="0" name="DI title" red="0" />
      <color blue="0" green="0" name="DI help" red="0" />
      <color blue="0" green="0" name="UNMS canvas" red="0" />
      <color blue="0" green="0" name="PS title" red="0" />
      <color blue="0" green="0" name="PS help" red="0" />
      <color blue="0" green="0" name="78" red="0" />
      <color blue="0" green="0" name="79" red="0" />
      <color blue="0" green="0" name="invisible" red="0" />
    </foreground_color>
</widget>"""

MISC_COLOURS_TWK = """<widget typeId="org.csstudio.opibuilder.widgets.Unknown" version="1.0">
    <foreground_color>
      <color blue="255" green="255" name="White" red="255" />
      <color blue="230" green="230" name="Grey 90%" red="230" />
      <color blue="230" green="230" name="Grey 90%" red="230" />
      <color blue="192" green="192" name="Grey 75%" red="192" />
      <color blue="192" green="192" name="Grey 75%" red="192" />
      <color blue="166" green="166" name="Grey 65%" red="166" />
      <color blue="166" green="166" name="Grey 65%" red="166" />
      <color blue="128" green="128" name="Grey 50%" red="128" />
      <color blue="128" green="128" name="Grey 50%" red="128" />
      <color blue="128" green="128" name="Grey 50%" red="128" />
      <color blue="102" green="102" name="Grey 40%" red="102" />
      <color blue="102" green="102" name="Grey 40%" red="102" />
      <color blue="64" green="64" name="Grey 25%" red="64" />
      <color blue="64" green="64" name="Grey 25%" red="64" />
      <color blue="0" green="0" name="Black" red="0" />
      <color blue="0" green="255" name="Green" red="0" />
      <color blue="0" green="192" name="Mid Green" red="0" />
      <color blue="0" green="192" name="Mid Green" red="0" />
      <color blue="0" green="192" name="Mid Green" red="0" />
      <color blue="0" green="128" name="Dark Green" red="0" />
      <color blue="0" green="0" name="Red" red="255" />
      <color blue="0" green="0" name="Red" red="255" />
      <color blue="0" green="0" name="Mid Red" red="192" />
      <color blue="0" green="0" name="Mid Red" red="192" />
      <color blue="0" green="0" name="Dark Red" red="128" />
      <color blue="255" green="0" name="Blue" red="0" />
      <color blue="255" green="0" name="Blue" red="0" />
      <color blue="192" green="0" name="Mid Blue" red="0" />
      <color blue="192" green="0" name="Mid Blue" red="0" />
      <color blue="128" green="0" name="Dark Blue" red="0" />
      <color blue="255" green="255" name="Cyan" red="0" />
      <color blue="255" green="255" name="Cyan" red="0" />
      <color blue="192" green="192" name="Mid Cyan" red="0" />
      <color blue="192" green="192" name="Mid Cyan" red="0" />
      <color blue="128" green="128" name="Dark Cyan" red="0" />
      <color blue="0" green="255" name="Yellow" red="255" />
      <color blue="0" green="255" name="Yellow" red="255" />
      <color blue="0" green="192" name="Mid Yellow" red="192" />
      <color blue="0" green="192" name="Amber" red="255" />
      <color blue="0" green="128" name="Dark Yellow" red="128" />
      <color blue="96" green="192" name="Orange" red="255" />
      <color blue="96" green="192" name="Orange" red="255" />
      <color blue="64" green="128" name="Light Brown" red="192" />
      <color blue="64" green="128" name="Light Brown" red="192" />
      <color blue="32" green="96" name="Dark Brown" red="128" />
      <color blue="255" green="0" name="Purple" red="255" />
      <color blue="192" green="0" name="Mid Purple" red="192" />
      <color blue="128" green="0" name="Dark Purple" red="128" />
      <color blue="240" green="210" name="CO title" red="169" />
      <color blue="240" green="210" name="CO title" red="169" />
      <color blue="0" green="0" red="0" />
      <color blue="135" green="216" name="EA title" red="135" />
      <color blue="135" green="216" name="EA title" red="135" />
      <color blue="159" green="223" name="VA title" red="202" />
      <color blue="159" green="223" name="VA title" red="202" />
      <color blue="0" green="0" red="0" />
      <color blue="184" green="198" name="MA title" red="185" />
      <color blue="184" green="198" name="MA title" red="185" />
      <color blue="172" green="201" name="TI title" red="210" />
      <color blue="172" green="201" name="TI title" red="210" />
      <color blue="0" green="0" red="0" />
      <color blue="216" green="212" name="MO title" red="115" />
      <color blue="216" green="212" name="MO title" red="115" />
      <color blue="207" green="207" name="CG title" red="158" />
      <color blue="207" green="207" name="CG title" red="158" />
      <color blue="0" green="0" red="100" />
      <color blue="144" green="193" name="RS title" red="225" />
      <color blue="144" green="193" name="RS title" red="225" />
      <color blue="198" green="181" name="RF title" red="184" />
      <color blue="198" green="181" name="RF title" red="184" />
      <color blue="0" green="0" red="0" />
      <color blue="224" green="205" name="MP title" red="238" />
      <color blue="224" green="205" name="MP title" red="238" />
      <color blue="198" green="181" name="DI title" red="198" />
      <color blue="198" green="181" name="DI title" red="198" />
      <color blue="0" green="0" red="0" />
      <color blue="168" green="150" name="PS title" red="255" />
      <color blue="168" green="150" name="PS title" red="255" />
      <color blue="0" green="0" name="Black" red="0" />
      <color blue="0" green="0" name="Black" red="0" />
      <color blue="0" green="0" name="Black" red="0" />
    </foreground_color>
</widget>"""


class ColourChangeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        colourtweak.init(filepath=os.path.join('..', colourtweak.COLOR_DEF_FILE))

    def assertStringsEqual(self, first, second, msg=None):
        """Assert that two multi-line strings are equal.
        If they aren't, show a nice diff.
        """
        self.assertTrue(isinstance(first, str), 'First arg is not a string')
        self.assertTrue(isinstance(second, str), 'Second arg is not a string')

        if first != second:
            message = ''.join(difflib.unified_diff(
                    first.splitlines(True), second.splitlines(True)))
            if msg:
                message += " : " + msg
            self.fail("Multi-line strings are unequal: %s\n" % message)

    def do_colourtweak(self, text):
        root = ET.fromstring(text)
        colourtweak.change_colours(root)
        return ET.tostring(root)

    def test_change_colours_label(self):
        self.assertStringsEqual(self.do_colourtweak(LABEL), LABEL_TWK)

    def test_anon_colour(self):
        self.assertStringsEqual(self.do_colourtweak(DISPLAY_ANON_COLOUR),
                                DISPLAY_ANON_COLOUR_TWK)

    def test_change_colours_action_button(self):
        self.assertStringsEqual(self.do_colourtweak(ACTIONBUTTON), ACTIONBUTTON_TWK)

    def test_change_colours_byte(self):
        self.assertStringsEqual(self.do_colourtweak(BYTE), BYTE_TWK)

    def test_change_colours_text_update(self):
        self.assertStringsEqual(self.do_colourtweak(TEXTUPDATE), TEXTUPDATE_TWK)

    def test_change_colours_bool_button(self):
        self.assertStringsEqual(self.do_colourtweak(BOOLBUTTON), BOOLBUTTON_TWK)

    def test_change_colours_choice_button(self):
        self.assertStringsEqual(self.do_colourtweak(CHOICE), CHOICE_TWK)

    def test_change_colours_no_widget_specific_logic(self):
        self.assertStringsEqual(self.do_colourtweak(MISC_COLOURS), MISC_COLOURS_TWK)

    def test_change_colours_canvas(self):
        self.assertStringsEqual(self.do_colourtweak(DISPLAY), DISPLAY_TWK)

if __name__ == '__main__':
    unittest.main()
