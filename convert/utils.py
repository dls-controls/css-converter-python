

import os
import stat
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
        log.warn('Module %s not understood', filepath)
        return filepath, '', '', ''

    v = None
    for i, p in enumerate(parts):
        if p == "":
            continue
        if p[0].isdigit() or p == 'Rx-y':
            version = p
            v = i
    if v is None:
        module = '/'.join(parts[root_index+1:root_index+2])
        relative_path = '/'.join(parts[root_index+2:])
    else:
        module = '/'.join(parts[root_index+1:v])
        relative_path = '/'.join(parts[v+1:])

    module_path = '/'.join(parts[:root_index+1])
    if module == '':
        raise ValueError('No module found in %s' % filepath)

    return module_path, module, version, relative_path


def make_read_only(filename, executable=False):
    """
    Remove write permissions from the file for everyone.
    """
    try:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
    except OSError:
        pass


def make_writeable(filename):
    """
    Make the file writeable by the owner.
    """
    try:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IWUSR)
    except OSError:
        pass


def read_conf_file(filename):
    """
    Read generic config file into list of lines.
    """
    with open(filename) as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines if not line.startswith('#')]
        lines = [line.strip() for line in lines if not line == '']
    return lines


def read_symbols_file(filename):
    """
    Read config file consisting of lines of the form:
    key: value
    Return a list of keys.  This is specifically useful for parsing
    our symbols configuration.
    """
    lines = read_conf_file(filename)
    symbols = [l.split(':')[0] for l in lines]
    return symbols


def generate_project_file(outdir, module_name, version):
    """
    Create an Eclipse project file for this set of OPIs.
    """
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


