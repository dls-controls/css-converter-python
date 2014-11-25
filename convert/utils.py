
import spoof

import os
import subprocess
import logging as log
import string


PROJECT_TEMPLATE = 'res/project.template'
PROJECT_FILENAME = '.project'

def parse_module_name(filepath):
    """
    Return (module_path, module_name, version, relative_path)

    If the path is not an ioc or a support module, raise ValueError.

    version may be None
    """
    log.debug("Parsing %s.", filepath)
    filepath = os.path.realpath(filepath)
    filepath = os.path.normpath(filepath)
    parts = filepath.split('/')
    version = None

    if 'support' in parts:
        root_index = parts.index('support')
    elif 'ioc' in parts:
        root_index = parts.index('ioc')
    else:
        raise ValueError('Module %s not understood' % filepath)

    v = root_index + 2
    for i, p in enumerate(parts):
        if p == "":
            continue
        if p[0].isdigit() or p == 'Rx-y':
            version = p
            v = i
    module = '/'.join(parts[root_index+1:v])
    module_path = '/'.join(parts[:root_index+1])
    if module == '':
        raise ValueError('No module found in %s' % filepath)
    relative_path = '/'.join(parts[v+1:])

    return module_path, module, version, relative_path


def make_read_only(filename, executable=False):
    if executable:
        perms = 0o555
    else:
        perms = 0o444
    if os.path.exists(filename):
        os.chmod(filename, perms)


def make_writeable(filename):
    if os.path.exists(filename):
        os.chmod(filename, 0o777)


def read_symbols_file(filename):
    symbols = []
    with open(filename) as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines]
        lines = [l for l in lines if l != "" and not l.startswith('#')]
        for line in lines:
            parts = line.split(':')
            symbols.append(parts[0])
    return symbols


def generate_project_file(outdir, module_name, version):
    """
    Create an Eclipse project file for this set of OPIs.
    """
    import os
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    with open(os.path.join(outdir, PROJECT_FILENAME), 'w') as f:
        with open(PROJECT_TEMPLATE) as template:
            content = template.read()
            s = string.Template(content)
            updated_content = s.substitute(module_name=module_name,
                                           version=version)
            f.write(updated_content)


def interpret_command(cmd, args, directory):
    log.info('Launcher command: %s', cmd)
    if not os.path.isabs(cmd) and cmd in os.listdir(directory):
        cmd = os.path.join(directory, cmd)
    log.info('CMD now %s', cmd)
    # Spoof EDM to find EDMDATAFILES and PATH
    # Index these directories to find which modules
    # relative paths may be in.
    edmdatafiles, path_dirs, working_dir, args = spoof.spoof_edm(cmd, args)
    try:
        _, module_name, version, _ = parse_module_name(working_dir)
    except ValueError:
        log.warn("Didn't understand script's working directory!")
        module_name = os.path.basename(cmd)
        version = None

    module_name = module_name.replace('/', '_')

    if version is None:
        version = 'no-version'

    all_dirs = [f for f in edmdatafiles if f not in ('', '.')]
    all_dirs.extend(path_dirs)
    all_dirs.append(working_dir)
    all_dirs = set(all_dirs)

    return all_dirs, module_name, version
