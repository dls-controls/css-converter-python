import os
import utils
import logging as log
import string
import stat

import spoof
import paths

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'
SCRIPT_TEMPLATE = 'res/runcss.template'

ESCAPE_CHARS = ['.', ':']


def get_apps(node):
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
            apps.extend(get_apps(child))
    return apps


def update_xml(node, apps_dict):
    '''
    Given updated commands in apps_dict, recursively update the
    launcher XML file.
    '''
    if node.tag == 'button':
        name = node.get('text')
        cmd = node.get('command')
        args = node.get('args', default="")
        if (name, cmd, args) in apps_dict:
            new_cmd, new_args = apps_dict[(name, cmd, args)]
            node.set('command', new_cmd)
            node.set('args', ' '.join(new_args))
    else:
        for child in node:
            update_xml(child, apps_dict)


def get_module_dict(launcher_cmd, root_dir):
    '''
    Create a mapping from output path to module name.
    '''
    module_dict = {}
    for directory in launcher_cmd.all_dirs:
        try:
            module_path, module_name, mversion, _ = utils.parse_module_name(directory)
            if mversion is None:
                mversion = ''
            p = os.path.join(root_dir, module_path.lstrip('/'), module_name, mversion)
            module_dict[p] = module_name
        except ValueError:
            continue
    return module_dict


def gen_run_script(launcher_cmd, root_dir):
    '''
    Generate a wrapper script which updates the appropriate
    links before opening a CSS window.

    Arguments:
        - launcher_cmd - the object containing info about the command
        - root_dir - the root of the output directory
    '''
    rel_dir = os.path.dirname(launcher_cmd.path_to_run.lstrip('/'))
    script_dir = os.path.join(root_dir, rel_dir)
    if not os.path.exists(script_dir):
        os.makedirs(script_dir)
    script_path = os.path.join(script_dir, 'runcss.sh')
    links_strings = []
    module_dict = get_module_dict(launcher_cmd, root_dir)
    for path, m in module_dict.iteritems():
        links_strings.append('%s=%s' % (path, os.path.join('/', launcher_cmd.project, m)))
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


def gen_run_cmd(launcher_cmd):
    # Add OPI shell macro to those already there
    launcher_cmd.macros['OPI_SHELL'] = 'true'
    macros_strings = []
    for key, value in launcher_cmd.macros.iteritems():
        macros_strings.append('%s=%s' % (key, value))
    macros_string = ','.join(macros_strings)
    for c in ESCAPE_CHARS:
        macros_string = macros_string.replace(c, '[\%d]' % ord(c))

    run_cmd = '"%s %s"' % (launcher_cmd.launch_opi, macros_string)
    return run_cmd


class LauncherCommand(object):

    def __init__(self, cmd, args):
        self.cmd = cmd
        self.args = args

        self.launch_opi = None
        self.path_to_run = None
        self.project = None
        self.edl_file = None
        self.version = None
        self.macros = {}
        self.all_dirs = []

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
        module_path, module, version, rel_path = utils.parse_module_name(path_to_run)
        if module != '':
            # Project name example: LI_TI_5-2 - i.e. replace / with _
            module_name = '_'.join(module.split('/'))
            project = '%s_%s' % (module_name, version)
            launch_opi = os.path.join('/', project, module, rel_path)
        else:
            project = os.path.basename(self.cmd)
            launch_opi = os.path.join('/', project, os.path.basename(path_to_run))

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

        self._get_macros(args)

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

    def _get_macros(self, edm_args):
        macro_dict = {}
        try:
            x_index = edm_args.index('-m')
            macros_arg = edm_args[x_index + 1]
            macros = macros_arg.split(',')
            for macro in macros:
                key, value = macro.split('=')
                macro_dict[key] = value
        except (ValueError, IndexError):
            pass

        self.macros = macro_dict

