import os
import utils
import logging as log

import paths

LAUNCHER_DIR = '/dls_sw/prod/etc/Launcher/'

class LauncherCommand(object):

    def __init__(self, cmd, args):
        self.cmd = cmd
        self.args = args

        self.launch_opi = None
        self.path_to_run = None
        self.project = None
        self.macros = {}
        self.all_dirs = []


    def interpret(self):
        '''
        Given a command and arguments from the launcher, determine
        the appropriate command for running CSS.
        If the command was not an EDM script, raise SpoofError.

        Returns:
            - script_path - path to the generated CSS wrapper script
            - launch command - command including any macros
            - all_dirs - list of all directories that need conversion
        '''
        log.info("Updating command: %s, %s", self.cmd, self.args)
        all_dirs, module_name, version, file_to_run, macros = utils.interpret_command(self.cmd, self.args, LAUNCHER_DIR)

        path_to_run = paths.full_path(all_dirs, file_to_run)
        path_to_run = os.path.realpath(path_to_run)
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
            project = os.path.basename(cmd)
            launch_opi = os.path.join('/', project, os.path.basename(path_to_run))

        self.macros = macros
        self.project = project
        self.path_to_run = path_to_run
        self.launch_opi = launch_opi
        self.all_dirs = all_dirs

