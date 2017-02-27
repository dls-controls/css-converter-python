import pkg_resources

pkg_resources.require('jinja2')
pkg_resources.require('pytest')

import html_versions
import jinja2
import os
import json


def test_render():
    test_mod_details = html_versions.ModDetails('dummy')
    test_mod_details.deps['dummy2'] = html_versions.ModDetails('dummy1')
    res_dir = os.path.join(os.curdir, html_versions.RESOURCES_DIR)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(res_dir))
    ans = html_versions.render([test_mod_details], env, html_versions.JSON_TEMPLATE)
    print(ans)
    json.loads(ans)
    assert False
