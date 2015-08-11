import os
import utils
import logging as log
import string
import stat
import xml.etree.ElementTree as et

import spoof
import paths

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'
SCRIPT_TEMPLATE = 'res/runcss.template'

ESCAPE_CHARS = ['.', ':']


def _get_macros(edm_args):
    macro_dict = {}
    try:
        flag_index = edm_args.index('-m')
        macros_arg = edm_args[flag_index + 1]
        macros = macros_arg.split(',')
        for macro in macros:
            key, value = macro.split('=')
            macro_dict[key] = value
    except (ValueError, IndexError):
        pass

    return macro_dict


class LauncherXml(object):

    def __init__(self, old_apps_xml, new_apps_xml):
        self.old_apps_xml = old_apps_xml
        self.new_apps_xml = new_apps_xml
        self._xml_tree = et.parse(old_apps_xml)
        self._xml_root = self._xml_tree.getroot()

    def get_cmds(self):
        cmds = []
        apps = self._apps_from_node(self._xml_root)
        for name, cmd, args in apps:
            cmd = LauncherCommand(name, cmd, args.split())
            cmds.append(cmd)
        return cmds

    def write_new(self, cmd_dict):
        '''
        Given updated commands in apps_dict, write a new launcher XML file.
        '''
        self._update_node(self._xml_root, cmd_dict)
        self._xml_tree.write(self.new_apps_xml, encoding='utf-8',
                             xml_declaration=True)

    def _apps_from_node(self, node):
        '''
        Recursively retrieve all commands and arguments from the specified
        node in the launcher XML file.

        Return a list of tuples (name, cmd, args).
        '''
        apps = []
        if node.tag == 'button':
            name = node.get('text')
            cmd = node.get('command')
            args = node.get('args', default="")
            apps.append((name, cmd, args))
        else:
            for child in node:
                apps.extend(self._apps_from_node(child))
        return apps

    def _update_node(self, node, cmd_dict):
        if node.tag == 'button':
            name = node.get('text')
            command = node.get('command')
            args = node.get('args', default="")
            cmd = LauncherCommand(name, command, args.split())
            if cmd in cmd_dict:
                new_cmd, new_args = cmd_dict[cmd]
                node.set('command', new_cmd)
                node.set('args', ' '.join(new_args))
        else:
            for child in node:
                self._update_node(child, cmd_dict)


class LauncherCommand(object):

    def __init__(self, name, cmd, args):
        self.name = name
        self.cmd = cmd
        self.args = args

        self.launch_opi = None
        self.path_to_run = None
        self.project = None
        self.edl_file = None
        self.version = None
        self.macros = {}
        self.all_dirs = []

    def __eq__(self, other):
        return (self.name == other.name and self.cmd == other.cmd
                and self.args == other.args)

    def __hash__(self):
        return 3*hash(self.name) * 5*hash(self.cmd) % 7*hash(tuple(self.args))

    def interpret(self):
        '''
        Given a command and arguments from the launcher, determine
        various properties about the command, useful for conversion.
        If the command was not an EDM script, raise SpoofError.
        '''
        log.info("Updating command: %s, %s", self.cmd, self.args)
        self._spoof_command(self.cmd, self.args, LAUNCHER_DIR)
        path_to_run = paths.full_path(self.all_dirs, self.edl_file)
        if path_to_run.endswith('edl'):
            path_to_run = path_to_run[:-3] + 'opi'
        else:
            path_to_run += '.opi'
        mpath, mname, mversion, rel_path = utils.parse_module_name(path_to_run)
        if mname != '':
            # Project name example: LI_TI_5-2 - i.e. replace / with _
            flat_mname = '_'.join(mname.split('/'))
            project = '%s_%s' % (flat_mname, mversion)
            # Actual path retains any / in module name
            launch_opi = os.path.join('/', project, mname, rel_path)
        else:
            project = os.path.basename(self.cmd)
            launch_opi = os.path.join('/', project,
                                      os.path.basename(path_to_run))

        self.launch_opi = launch_opi
        self.project = project
        self.path_to_run = path_to_run

    def _spoof_command(self, cmd, args, directory):
        log.info('Launcher command: %s', cmd)
        if not os.path.isabs(cmd) and cmd in os.listdir(directory):
            cmd = os.path.join(directory, cmd)
        log.info('Command corrected to %s', cmd)
        # Spoof EDM to find EDMDATAFILES and PATH
        # Index these directories to find which modules
        # relative paths may be in.
        edmdatafiles, path_dirs, working_dir, args = spoof.spoof_edm(cmd, args)

        self.macros = _get_macros(args)

        edl_files = [a for a in args if a.endswith('edl')]
        edl_file = edl_files[0] if len(edl_files) > 0 else args[-1]
        try:
            _, module_name, version, _ = utils.parse_module_name(working_dir)
        except ValueError:
            log.warn("Didn't understand script's working directory!")
            module_name = os.path.basename(cmd)
            version = None

        module_name = module_name.replace('/', '_')

        if version is None:
            version = 'no-version'

        all_dirs = edmdatafiles + path_dirs
        all_dirs.append(working_dir)
        all_dirs = [os.path.realpath(f) for f in all_dirs if f not in ('', '.')]
        all_dirs = set(all_dirs)

        self.all_dirs = all_dirs
        self.module_name = module_name
        self.version = version
        self.edl_file = edl_file

    def get_run_cmd(self):
        # Add OPI shell macro to those already there
        self.macros['Position'] = 'NEW_SHELL'
        macros_strings = []
        for key, value in self.macros.iteritems():
            macros_strings.append('%s=%s' % (key, value))
        macros_string = ','.join(macros_strings)
        for c in ESCAPE_CHARS:
            macros_string = macros_string.replace(c, '[\%d]' % ord(c))

        run_cmd = '"%s %s"' % (self.launch_opi, macros_string)
        return run_cmd

    def gen_run_script(self, root_dir):
        '''
        Generate a wrapper script which updates the appropriate
        links before opening a CSS window.

        Arguments:
            - root_dir - the root of the output directory
        '''
        rel_dir = os.path.dirname(self.path_to_run.lstrip('/'))
        script_dir = os.path.join(root_dir, rel_dir)
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        script_path = os.path.join(script_dir, 'runcss.sh')
        links_strings = []
        module_dict = self._get_module_dict(root_dir)
        for path, m in module_dict.iteritems():
            links_strings.append('%s=%s' %
                                (path, os.path.join('/', self.project, m)))
        links_string = ',\\\n'.join(links_strings)
        for c in ESCAPE_CHARS:
            links_string = links_string.replace(c, '[\%d]' % ord(c))
        with open(script_path, 'w') as f:
            with open(SCRIPT_TEMPLATE) as template:
                content = template.read()
                s = string.Template(content)
                updated_content = s.substitute(links=links_string)
                f.write(updated_content)
        # Give owner and group execute permissions.
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP)
        log.info('Run script written to %s', script_path)
        return script_path

    def _get_module_dict(self, root_dir):
        '''
        Create a mapping from output path to module name.
        '''
        module_dict = {}
        for directory in self.all_dirs:
            try:
                mpath, mname, mversion, _ = utils.parse_module_name(directory)
                if mversion is None:
                    mversion = ''
                p = os.path.join(root_dir, mpath.lstrip('/'),
                                 mname, mversion)
                module_dict[p] = mname
            except ValueError:
                continue
        return module_dict
