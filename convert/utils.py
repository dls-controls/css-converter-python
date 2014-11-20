
import os
import subprocess
import logging as log
import string


PROJECT_TEMPLATE = 'res/project.template'
PROJECT_FILENAME = '.project'

def parse_module_name(filepath):
    """
    Return (module_name, version, relative_path)

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
    if module == '':
        raise ValueError('No module found in %s' % filepath)
    relative_path = '/'.join(parts[v+1:])

    return module, version, relative_path


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


def is_edm_script(filename):
    try:
        with open(filename) as f:
            for line in f.readlines():
                if line.strip().startswith('edm '):
                    return True
        return False
    except IOError as e:
        log.warn('Error opening %s: %s', filename, e)
        return False


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


def spoof_edm(script_file, args=[]):
    """
    Use a dummy script called 'edm' to extract:
     - the EDMDATAFILES variable
     - the PATH variable
     - the script's working directory
     - the command-line arguments
    from any script used to run edm.

    Assume that the last four lines of output are those produced by this script.
    """

    if not is_edm_script(script_file):
        raise ValueError('Script file does not use EDM.')
    env = os.environ.copy()
    old_dir = os.getcwd()
    script_dir = os.path.dirname(script_file)
    # Change to directory of spoofed script.
    os.chdir(script_dir)

    this_dir = os.path.dirname(__file__)
    spoof_edm_dir = os.path.join(this_dir, '..', 'res')
    # Put spoof edm first on the path.
    env['PATH'] = '%s:%s:%s' % (spoof_edm_dir, script_dir, env['PATH'])
    old_path = env['PATH'].split(':')

    edmdatafiles = None
    path = None

    args_string = " ".join(a for a in args)
    args_string = args_string.replace('$PORT', '5064')
    command_string = '%s %s' % (script_file, args_string)
    log.debug('Spoofing script: %s', command_string)

    out = subprocess.check_output([command_string], shell=True, env=env)

    # Change back to original directory.
    os.chdir(old_dir)
    log.debug('Spoof EDM output:\n\n%s', out)
    lines = out.splitlines()
    if len(lines) == 0 or lines[-1] != 'Spoof EDM complete.':
        log.warn('EDM spoof failed.')
        return [], [], "", []

    if len(lines) > 1:
        path = lines[-2]
        path = path.strip().split(':')
        path = [p for p in path if p not in old_path]
    if len(lines) > 2:
        edmdatafiles = lines[-3]
        edmdatafiles = edmdatafiles.strip().split(':')
        edmdatafiles = [e for e in edmdatafiles if e != '']
    if len(lines) > 3:
        pwd = lines[-4].strip()
    if len(lines) > 4:
        args = lines[-5].strip().split()
    log.info('EDMDATAFILES: %s', edmdatafiles)
    log.info('PATH: %s', path)
    log.info('Script working directory: %s', pwd)
    log.info('Script arguments: %s', args)
    return edmdatafiles, path, pwd, args


def interpret_command(cmd, args, directory):
    log.info('Launcher command: %s', cmd)
    symbols = {}
    if not os.path.isabs(cmd):
        cmd = os.path.join(directory, cmd)
    # Spoof EDM to find EDMDATAFILES and PATH
    # Index these directories to find which modules
    # relative paths may be in.
    edmdatafiles, path_dirs, working_dir, args = spoof_edm(cmd, args)
    try:
        module_name, version, _ = parse_module_name(working_dir)
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
