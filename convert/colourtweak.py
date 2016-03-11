#!/bin/env dls-python
import xml.etree.ElementTree as ET
import os
import logging as log

import utils

COLOR_DEF = 'res/colourtweak.def'

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

# colour_dict["Red"] = (255, 0, 0)
colour_dict = {}
with open(COLOR_DEF) as f:
    for line in f:
        # get rid of comments
        split = line.strip().split("#")
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
    # Originally Tom set this to green, but it was considered too bright.
    "Monitor: NORMAL": "Mid Green",
    "Open/On": "Mid Green",
    # Should this be dark green?
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
    # Look for colour elements two elements below.
    # <foreground_color>
    #   <color blue="32" green="64" name="Related Display: FG" red="128" />
    # </foreground_color>
    # Other colour elements may be inside child widgets (e.g. within grouping
    # containers) and need to be handled in those widgets.
    for colour in widget.findall("./*/color"):
        # Map colours
        name = colour.get("name")
        if name is None:
            continue
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
        elif name == "Related display" and typeId in [ACTIONBUTTON, MENUBUTTON] and prop == "foreground_color":
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
    try:
        if os.path.exists(filepath) or os.access(filepath, os.R_OK):
            tree = ET.parse(filepath)
            root = tree.getroot()

            for widget in root.findall(".//widget"):
                change_colours(widget)

            # write the new tree out to the same file
            utils.make_writeable(filepath)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        else:
            log.warn("Skipping %s, file not found", filepath)
    except ET.ParseError:
        log.warn("Skipping %s, XML invalid", filepath)


def build_filelist(basepath):
    """ Execute a grep on the basepath to find all files that contain a menumux
        control

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.info("Building colourtweak list.")
    files = []
    for dirpath, dirnames, filenames in os.walk(basepath):
        for filename in filenames:
            if filename.endswith(".opi"):
                files.append(os.path.join(dirpath, filename))

    return files
