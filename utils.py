
import os
import subprocess
import logging as log


def parse_module_name(filepath):
    '''
    Return (module_name, version, relative_path)
    '''
    log.debug("Parsing %s.",  filepath)
    parts = filepath.split('/')
    module, version, relative_path = None, None, None

    if 'support' in parts:
        i = parts.index('support')
        module = parts[i+1]
        version = None
        relative_path = None
        if 'prod' in parts and len(parts) > i+2:
            version = parts[i+2]
        if len(parts) > i+3:
            relative_path = '/'.join(parts[i+3:])
    elif 'ioc' in parts:
        index = parts.index('ioc')
        v = -1
        for i, p in enumerate(parts):
            if p == "":
                continue
            if p[0].isdigit() or p == 'Rx-y':
                version = p
                v = i
        module = '/'.join(parts[index+1:v])
        relative_path = '/'.join(parts[v+1:])
    else:
        raise ValueError('Module %s not understood' % filepath)
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


def spoof_edm(script_file, args=[]):
    '''
    Use a script called 'edm' to extract the EDMDATAFILES and PATH variables
    from any script used to run edm.

    Assume that the last two lines of output are those produced by this script.
    '''
    env = os.environ.copy()
    old_dir = os.getcwd()
    script_dir = os.path.dirname(script_file)
    # Change to directory of spoofed script.
    os.chdir(script_dir)
    env['PATH'] = '/home/hgs15624/code/converter/spoof_edm:' + script_dir + env['PATH']
    old_path = env['PATH'].split(':')

    edmdatafiles = None
    path = None

    args_string = "".join(a for a in args)
    args_string = args_string.replace('$PORT', '5064')
    command_string = "%s %s" % (script_file, args_string)
    log.debug("Spoofing script: %s", command_string)

    # These scripts often expect a port number and edl file.
    out = subprocess.check_output([command_string], shell=True, env=env)

    # Change back to original directory.
    os.chdir(old_dir)
    log.debug("Spoof EDM output:\n\n%s", out)
    lines = out.splitlines()
    if lines[-1] != 'Spoof EDM complete.':
        log.warn("EDM spoof failed.")
        return None

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
    log.info("EDMDATAFILES: %s", edmdatafiles)
    log.info("PATH: %s", path)
    return edmdatafiles, path, pwd


if __name__ == '__main__':
    print parse_module_name('/dls_sw/work/R3.14.12.3/support/motor/')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/motorApp/ACRSrc/Makefile')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/support/diagOpi')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/ioc/ME09C/ME09C-EA-IOC-01/1-3')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/ioc/ME09C/ME09C-EA-IOC-01/1-3/ME09C-EA-IOC-01App/data/')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/support/diagOpi/2-44/scripts')
    print parse_module_name('/dls_sw/prod/R3.14.12.3/ioc/Libera/2.05.15/opi/libera/clock_graphs.edl')
    print parse_module_name('/dls_sw/prod/etc/Launcher')
