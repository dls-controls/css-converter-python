#!/bin/env dls-python
import logging as log
import os
import xml.etree.ElementTree as ET

import utils

COLOR_DEF_FILE = 'res/colourtweak.def'

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

# dictionary of KEY:(r,g,b) tuple
colour_dict = {}


def init(filepath=COLOR_DEF_FILE):
    """ Parse a colour definitions file containing "key = r, g, b" lines
    Args:
        filepath: file to load

    """
    with open(filepath) as f:
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
COLOUR_MAP = {
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

TEXT_CONTROLS = [ACTIONBUTTON, TEXTINPUT, MENUBUTTON, CHOICEBUTTON, BOOLBUTTON]
TEXT_MONITORS = [TEXTUPDATE]
TEXT_STATIC = [LINKINGCONTAINER, LABEL, DETAILPANEL, GROUPINGCONTAINER]
NON_TEXT = [MULTISTATESYMBOLMONITOR, RECTANGLE, BYTEMONITOR]


def change_colours(widget):
    """ Perform colour substitutions in the constructed OPI files.

        These are specified as specific widget/colour updates or statically
        defined colour mapping (COLOUR_MAP)

        Look for colour elements two elements below, e.g.

        <foreground_color>
          <color blue="32" green="64" name="Related Display: FG" red="128" />
        </foreground_color>

        and in rules blocks

        <rules>
          <rule name="onColorAlarm" out_exp="false" prop_id="on_color">
            <exp bool_exp="pvSev0==-1" >
              <value><color name="Major" /></value>
            </exp>
            <exp bool_exp= ... >
              <value><color name= "Minor" /></value>
            </exp>
            ...
          </rule>
        </rules>

        Other colour elements may be inside child widgets (e.g. within grouping
        containers) and need to be handled in those widgets.
    Args:
        widget: XML widget element

    """
    # Get the widget type
    type_id = widget.get("typeId")
    # Parent lookup for colours
    colour_prop = {c:p.tag for p in widget.iter() for c in p}

    # Note: ElementTree doesn't support xpath 'or' (|) so we parse the document
    # twice
    for colour in widget.findall("./*/color"):
        name = colour.get("name")
        if name is not None:
            process_element(colour, name, type_id, colour_prop[colour])

    for colour in widget.findall("./*/rule/*/*/color"):
        name = colour.get("name")
        if name is not None:
            process_element(colour, name, type_id, colour_prop[colour])


def process_element(colour, name, type_id, prop):
    """ Execute role specific overrides on the passed colour XML element
    Args:
        colour: XML color element
        prop: enclosing element name
        name: EDM colour name
        type_id: CSS widget typeId

    Returns:

    """
    def match_colour_role(n, t, p=None, reference_name=None):
        """ Helper method to evaluate match on three arguments.

            The arguments define the subset of widget color rules the
            transformation should be applied to.

        Args:
            n (String): EDM colour name for rule
            t: (String or [String]): name or list of element typeIds
            p (String or [String]) (optional): property name or list
            reference_name (String) (optional): EDM colour name for comparison,
                defaults to process_element 'name' argument
        """
        if reference_name is None:
            reference_name = name
        return reference_name == n and type_id in t and (p is None or prop in p)

    if match_colour_role("canvas", TEXT_STATIC + [DISPLAY], "background_color",
                         reference_name=name.split()[-1].lower()):
        set_colour(colour, "Canvas")
    elif match_colour_role("Canvas", TEXT_CONTROLS, ["background_color", "off_color", "value"]):
        set_colour(colour, "Controller: BG")
    elif match_colour_role("Button: On", CHOICEBUTTON, "selected_color"):
        set_colour(colour, "Button: On")
    elif match_colour_role("Button: On", BOOLBUTTON):
        set_colour(colour, "Button: On")
    elif match_colour_role("Monitor BG", TEXT_MONITORS, "background_color"):
        set_colour(colour, "Monitor: BG")
    elif match_colour_role("Black", TEXT_STATIC + [ACTIONBUTTON], "foreground_color"):
        set_colour(colour, "Text: FG")
    elif match_colour_role("Green LED: On", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Green LED: On")
    elif match_colour_role("Green LED: Off", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Green LED: Off")
    elif match_colour_role("Red LED: On", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Red LED: On")
    elif match_colour_role("Red LED: Off", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Red LED: Off")
    elif match_colour_role("Yellow LED: On", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Yellow LED: On")
    elif match_colour_role("Yellow LED: Off", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Yellow LED: Off")
    elif match_colour_role("Controller/alt", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Blue LED: On")
    elif match_colour_role("cyan-34", BYTEMONITOR, ["on_color", "off_color"]):
        set_colour(colour, "Blue LED: Off")
    elif match_colour_role("Monitor: NORMAL", TEXT_MONITORS, "foreground_color"):
        set_colour(colour, "Monitor: FG")
    elif match_colour_role("Controller", TEXT_CONTROLS, "foreground_color"):
        set_colour(colour, "Controller: FG")
    elif match_colour_role("Shell/reldsp-alt", ACTIONBUTTON, "foreground_color"):
        set_colour(colour, "Text: FG")
    elif match_colour_role("Related display", [ACTIONBUTTON, MENUBUTTON], "foreground_color"):
        set_colour(colour, "Related Display: FG")
    elif match_colour_role("Exit/Quit/Kill", ACTIONBUTTON, "foreground_color"):
        set_colour(colour, "Exit: FG")
    # If we have a static map, then just use that
    elif name in COLOUR_MAP:
        set_colour(colour, COLOUR_MAP[name])
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
    """ Find all OPI files.

        Arguments:
            basepath - root of search
        Returns:
            iterator over relative filepaths
    """
    log.info("Building colourtweak list.")
    return utils.find_opi_files(basepath)
