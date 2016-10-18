
import os
import subprocess
import logging as log

EDM_SCRIPTS = ['runDiEdm.sh']
CONFIGURE_IOC = 'configure-ioc'
CONFIGURE_IOC_SCRIPT = 'from_configure_ioc.sh'
SCRIPT_FROM_DIR = 'script_from_dir.sh'


def _is_edm_script(filename):
    if os.path.basename(filename) in EDM_SCRIPTS:
        return True
    try:
        with open(filename) as f:
            for line in f.readlines():
                if (line.strip().startswith('edm ') or
                    line.strip().startswith('exec edm')):
                    return True
        return False
    except IOError as e:
        log.warn('Error opening %s: %s', filename, e)
        return False


def redirect(script, args):
    """
    Emulate the launcher scripts to interpret the actual script and
    arguments being used from the launcher.
    """
    if os.path.basename(script) == CONFIGURE_IOC_SCRIPT:
        relative_path = args[2] if len(args) > 2 else None
        script = _from_configure_ioc(args[1], relative_path)
        # from_configure_ioc does not pass arguments
        args = []
    elif os.path.basename(script) == SCRIPT_FROM_DIR:
        relative_path = args[2] if len(args) > 2 else None
        script = _script_from_dir(args[1], relative_path)
        # Arguments after the first three are passed to the
        # script found by script_from_dir.sh.
        args = args[3:]
    return script, args


def _from_configure_ioc(key, relative_path=None):
    """
    Recreate the behaviour of the script from_configure_ioc.sh.
    """
    try:
        output = subprocess.check_output([CONFIGURE_IOC, 's', '-p', key])
        output = output.strip()
        if relative_path is not None:
            output = os.path.join(os.path.dirname(output), relative_path)
    except subprocess.CalledProcessError:
        output = None
    return output


def _script_from_dir(key, relative_path=None):
    """
    Recreate the behaviour of the script from_configure_ioc.sh.
    """
    try:
        output = subprocess.check_output([CONFIGURE_IOC, 's', '-p', key])
        output = output.strip()
        if relative_path is not None:
            output = os.path.join(output, relative_path)
    except subprocess.CalledProcessError:
        output = None
    return output


class SpoofError(Exception):
    pass


def capture_spoof_output(env, script_dir, script_file, args):
    """
    Execute script with any arguments after replacing 'edm' on the path
    with the spoof version.  Capture and return the output.
    """
    os.chdir(script_dir)
    this_dir = os.path.dirname(__file__)
    spoof_edm_dir = os.path.join(this_dir, '..', 'res')
    # Put spoof edm first on the path.
    env['PATH'] = '%s:%s:%s' % (spoof_edm_dir, script_dir, env['PATH'])

    args_string = " ".join(a for a in args)
    args_string = args_string.replace('$PORT', '5064')
    command_string = '%s %s' % (script_file, args_string)
    log.debug('Spoofing script: %s', command_string)

    out = subprocess.check_output([command_string], shell=True, env=env)
    return out


def process_output(output, old_path):
    """
    Convert lines of output from spoof edm script into:
        * edmdatafiles directories
        * path directories
        * working directory
        * script arguments
    Return as a tuple.
    """
    lines = output.splitlines()
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
    log.debug('EDMDATAFILES: %s', edmdatafiles)
    log.debug('PATH: %s', path)
    log.debug('Script arguments: %s', args)
    return edmdatafiles, path, pwd, args


def spoof_edm(script_file, args=[]):
    """
    Use a dummy script called 'edm' to extract:
     - the EDMDATAFILES variable
     - the PATH variable
     - the script's working directory
     - the command-line arguments
    from any script used to run edm.

    Assume that the last four lines of output are those produced by this script.

    Returns:
        edmdatafiles:
        path:
        pwd:
        args: List of additional arguments (may include $PORT or a number).
    """
    # Special cases: launcher scripts from_configure_ioc.sh and
    # script_from_dir.sh
    if os.path.basename(script_file) in (CONFIGURE_IOC_SCRIPT, SCRIPT_FROM_DIR):
        script_file, args = redirect(script_file, args)

    if script_file is None:
        raise SpoofError('Error calling configure-ioc on script file %s.' %
                         script_file)
    if not _is_edm_script(script_file):
        raise SpoofError('Script file %s does not use EDM.' % script_file)
    env = os.environ.copy()
    old_path = env['PATH'].split(':')
    old_dir = os.getcwd()
    script_dir = os.path.dirname(script_file)
    try:
        output = capture_spoof_output(env, script_dir, script_file, args)
    except subprocess.CalledProcessError as exc:
        raise SpoofError('Error spoofing script: {}'.format(exc))
    finally:
        # Change back to original directory.
        os.chdir(old_dir)
    log.debug('Spoof EDM output:\n\n%s', output)
    edmdatafiles, path, pwd, args = process_output(output, old_path)
    return edmdatafiles, path, pwd, args
