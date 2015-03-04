#!/bin/env dls-python
import xml.etree.ElementTree as ET
import os
import logging as log

from utils import make_writeable, make_read_only

DISPLAY = "org.csstudio.opibuilder.Display"
ACTIONBUTTON = "org.csstudio.opibuilder.widgets.ActionButton"
MULTISTATESYMBOLMONITOR = "org.csstudio.opibuilder.widgets.symbol.multistate.MultistateMonitorWidget"
LINKINGCONTAINER = "org.csstudio.opibuilder.widgets.linkingContainer"
RECTANGLE = "org.csstudio.opibuilder.widgets.Rectangle"
LABEL = "org.csstudio.opibuilder.widgets.Label"
DETAILPANEL = "org.csstudio.opibuilder.widgets.detailpanel"
GROUPINGCONTAINER = "org.csstudio.opibuilder.widgets.groupingContainer"
TEXTINPUT = "org.csstudio.opibuilder.widgets.TextInput"
TEXTUPDATE = "org.csstudio.opibuilder.widgets.TextUpdate"
MENUBUTTON = "org.csstudio.opibuilder.widgets.MenuButton"
CHOICEBUTTON = "org.csstudio.opibuilder.widgets.choiceButton"
BYTEMONITOR = "org.csstudio.opibuilder.widgets.bytemonitor"
BOOLBUTTON = "org.csstudio.opibuilder.widgets.BoolButton"

colours = """
# Alarm colours
Minor = 255, 241, 0
Major = 255, 0, 0
Invalid = 255, 255, 255
Disconnected = 255, 255, 255

# Widget colours
Canvas = 200, 200, 200
Monitor: BG = 64, 64, 64
Monitor: FG = 96, 255, 96
Controller: FG = 0, 0, 192
Controller: BG = 205, 205, 205
Button: On = 190, 190, 190
Related Display: FG = 128, 64, 32
Text: FG = 0, 0, 0
Exit: FG = 192, 0, 192

# LED colours
Red LED: On = 255, 0, 0
Red LED: Off = 96, 0, 0
Yellow LED: On = 255, 255, 0
Yellow LED: Off = 96, 96, 0
Green LED: On = 0, 255, 0
Green LED: Off = 0, 96, 0
Blue LED: On = 96, 240, 255
Blue LED: Off = 32, 64, 96

# Generic colours
White = 255, 255, 255
Grey 90% = 230, 230, 230
Grey 75% = 192, 192, 192
Grey 65% = 166, 166, 166
Grey 50% = 128, 128, 128
Grey 40% = 102, 102, 102
Grey 25% = 64, 64, 64
Black = 0, 0, 0
Red = 255, 0, 0
Mid Red = 192, 0, 0
Dark Red = 128, 0, 0
Yellow = 255, 255, 0
Mid Yellow = 192, 192, 0
Dark Yellow = 128, 128, 0
Green = 0, 255, 0
Mid Green = 0, 192, 0
Dark Green = 0, 128, 0
Cyan = 0, 255, 255
Mid Cyan = 0, 192, 192
Dark Cyan = 0, 128, 128
Blue = 0, 0, 255
Mid Blue = 0, 0, 192
Dark Blue = 0, 0, 128
Purple = 255, 0, 255
Mid Purple = 192, 0, 192
Dark Purple = 128, 0, 128
Amber = 255, 192, 0
Orange = 255, 192, 96
Light Brown = 192, 128, 64
Dark Brown = 128, 96, 32

# Title colours
CO title = 169, 210, 240
EA title = 135, 216, 135
VA title = 202, 223, 159
MA title = 185, 198, 184
TI title = 210, 201, 172
MO title = 115, 212, 216
CG title = 158, 207, 207
RS title = 225, 193, 144
RF title = 184, 181, 198
MP title = 238, 205, 224
DI title = 198, 181, 198
PS title = 255, 150, 168
"""
# colour_dict["Red"] = (255, 0, 0)
colour_dict = {}
for line in colours.splitlines():
    # get rid of comments
    split = line.split("#")
    if split[0]:
        # name = r, g, b
        name, rgb = split[0].split("=")
        r, g, b = rgb.split(",")                
        colour_dict[name.strip()] = (r.strip(), g.strip(), b.strip())

def set_colour(el, name):
    # set colour attributes to be according to the named colour
    r, g, b = colour_dict[name]
    el.set("red", r)
    el.set("green", g)            
    el.set("blue", b)
    el.set("name", name)

# Map of colours with no widget specific changes
colour_map = {
    "Disconn/Invalid": "White",
    "Top Shadow": "Grey 90%",
    "grey-2": "Grey 90%",
    "Canvas": "Grey 75%",
    "Button: On": "Grey 75%",
    "Wid-alt/Anno-sec": "Grey 65%",
    "Title": "Grey 65%",
    "grey-7": "Grey 50%",
    "grey-8": "Grey 50%",
    "Help": "Grey 50%",
    "Monitor BG": "Grey 40%",
    "Bottom Shadow": "Grey 40%",
    "grey-12": "Grey 25%",
    "grey-13": "Grey 25%",
    "Black": "Black",
    "Green LED: On": "Green",
    "Monitor: NORMAL": "Green",
    "Open/On": "Mid Green",
    "Monitor: alt": "Mid Green",
    "Green LED: Off": "Dark Green",
    "Red LED: On": "Red",
    "Monitor: MAJOR": "Red",
    "Shut/Off": "Mid Red",
    "Mon: MAJOR/unack": "Mid Red",
    "Red LED: Off": "Dark Red",
    "Controller": "Blue",
    "blue-26": "Blue",
    "blue-27": "Mid Blue",
    "blue-28": "Mid Blue",
    "blue-29": "Dark Blue",
    "Controller/alt": "Cyan",
    "cyan-31": "Cyan",
    "cyan-32": "Mid Cyan",
    "cyan-33": "Mid Cyan",
    "cyan-34": "Dark Cyan",
    "Yellow LED: On": "Yellow",
    "Monitor: MINOR": "Yellow",
    "Mon: MINOR/unack": "Mid Yellow",
    "amber-38": "Amber",
    "Yellow LED: Off": "Dark Yellow",
    "Shell/reldsp-alt": "Orange",
    "orange-41": "Orange",
    "orange-42": "Light Brown",
    "Related display": "Light Brown",
    "brown-44": "Dark Brown",
    "purple-45": "Purple",
    "Exit/Quit/Kill": "Mid Purple",
    "purple-47": "Dark Purple",
    "CO title": "CO title",
    "CO help": "CO title",
    "EA title": "EA title",
    "EA help": "EA title",
    "VA title": "VA title",
    "VA help": "VA title",
    "MA title": "MA title",
    "MA help": "MA title",
    "TI title": "TI title",
    "TI help": "TI title",
    "MO title": "MO title",
    "MO help": "MO title",
    "CG title": "CG title",
    "CG help": "CG title",
    "RS title": "RS title",
    "RS help": "RS title",
    "RF title": "RF title",
    "RF help": "RF title",
    "MP title": "MP title",
    "MP help": "MP title",
    "DI title": "DI title",
    "DI help": "DI title",
    "PS title": "PS title",
    "PS help": "PS title",
    "78": "Black",
    "79": "Black",
    "invisible": "Black",
    "unknown": "Black",    
    "Minor": "Minor",
    "Major": "Major",
    "Invalid": "Invalid",
    "Disconnected": "Disconnected",            
}
  
def change_colours(widget):
    textControls = [ACTIONBUTTON, TEXTINPUT, MENUBUTTON, CHOICEBUTTON, BOOLBUTTON]
    textMonitors = [TEXTUPDATE]
    textStatic = [LINKINGCONTAINER, LABEL, DETAILPANEL, GROUPINGCONTAINER]
    nonText = [MULTISTATESYMBOLMONITOR, RECTANGLE, BYTEMONITOR]
    # Get the widget type
    typeId = widget.get("typeId")
    # Parent lookup for colours
    colour_prop = {c:p.tag for p in widget.iter() for c in p}
    # Look for colour elements
    for colour in widget.findall(".//color"):
        # Map colours
        name = colour.get("name")
        prop = colour_prop[colour]
        # Role specific overrides
        if name.split()[-1].lower() == "canvas" and typeId in textStatic + [DISPLAY] and prop == "background_color":
            set_colour(colour, "Canvas")
        elif name == "Canvas" and typeId in textControls and prop in ["background_color", "off_color", "value"]:
            set_colour(colour, "Controller: BG")
        elif name == "Button: On" and typeId == CHOICEBUTTON and prop == "selected_color":
            set_colour(colour, "Button: On")
        elif name == "Button: On" and typeId == BOOLBUTTON:
            set_colour(colour, "Button: On")
        elif name == "Monitor BG" and typeId in textMonitors and prop == "background_color":
            set_colour(colour, "Monitor: BG")
        elif name == "Black" and typeId in textStatic + [ACTIONBUTTON] and prop == "foreground_color":
            set_colour(colour, "Text: FG")
        elif name == "Green LED: On" and typeId == BYTEMONITOR and prop in ["on_color", "off_color"]:
            set_colour(colour, "Green LED: On" )     
        elif name == "Green LED: Off" and typeId == BYTEMONITOR and prop  in ["on_color", "off_color"]:
            set_colour(colour, "Green LED: Off" )                 
        elif name == "Red LED: On" and typeId == BYTEMONITOR and prop in ["on_color", "off_color"]:
            set_colour(colour, "Red LED: On" )     
        elif name == "Red LED: Off" and typeId == BYTEMONITOR and prop  in ["on_color", "off_color"]:
            set_colour(colour, "Red LED: Off" )                 
        elif name == "Yellow LED: On" and typeId == BYTEMONITOR and prop in ["on_color", "off_color"]:
            set_colour(colour, "Yellow LED: On" )     
        elif name == "Yellow LED: Off" and typeId == BYTEMONITOR and prop  in ["on_color", "off_color"]:
            set_colour(colour, "Yellow LED: Off" )                 
        elif name == "Controller/alt" and typeId == BYTEMONITOR and prop in ["on_color", "off_color"]:
            set_colour(colour, "Blue LED: On")  
        elif name == "cyan-34" and typeId == BYTEMONITOR and prop in ["on_color", "off_color"]:
            set_colour(colour, "Blue LED: Off")  
        elif name == "Monitor: NORMAL" and typeId in textMonitors and prop == "foreground_color":
            set_colour(colour, "Monitor: FG")            
        elif name == "Controller" and typeId in textControls and prop == "foreground_color":
            set_colour(colour, "Controller: FG") 
        elif name == "Shell/reldsp-alt" and typeId in [ACTIONBUTTON] and prop == "foreground_color":
            set_colour(colour, "Text: FG")          
        elif name == "Related display" and typeId in [ACTIONBUTTON] and prop == "foreground_color":
            set_colour(colour, "Related Display: FG")          
        elif name == "Exit/Quit/Kill" and typeId in [ACTIONBUTTON] and prop == "foreground_color":
            set_colour(colour, "Exit: FG")     
        # If we have a static map, then just use that
        elif name in colour_map:
            set_colour(colour, colour_map[name])
        else:
            # remove name
            colour.attrib.pop("name")

def parse(filepath):
    if os.path.exists(filepath) or os.access(filepath, os.R_OK):
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        for widget in root.findall(".//widget"):            
            change_colours(widget)

        # write the new tree out to the same file
        make_writeable(filepath)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        make_read_only(filepath)
    else:
        log.warn("Skipping %s, file not found", filepath)


def build_filelist(basepath):
    """ Execute a grep on the basepath to find all files that contain a menumux
        control

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.debug("Building colourtweak list.")
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                return os.path.join(dirpath, filename)

