import pkg_resources

pkg_resources.require('jinja2')
pkg_resources.require('pytest')

from html_versions import ModDetails, render, RESOURCES_DIR, JSON_TEMPLATE
import jinja2
import os
import json
import pytest


@pytest.fixture
def dummy_md():
    return ModDetails('dummy')


def test_render_creates_valid_json(dummy_md):
    dummy_md.deps['dummy2'] = ModDetails('dummy1')
    res_dir = os.path.join(os.curdir, RESOURCES_DIR)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(res_dir))
    ans = render([dummy_md], env, JSON_TEMPLATE)
    # throws an exception if json invalid
    json.loads(ans)


@pytest.mark.parametrize('cfg,latest,expected', [
        ('1-0', '1-1', ModDetails.OUT_OF_DATE),
        ('1-0', '1-0', ModDetails.OK),
        ('1-1', '1-0', ModDetails.OK),
        ('1-0', '1-0-1', ModDetails.OUT_OF_DATE),
        ('2-8dls4-8', '2-8dls4-8-1', ModDetails.OUT_OF_DATE)
    ])
def test_assess_cfg_ioc_versions_handles_different_cases(dummy_md,
                                                         cfg,
                                                         latest,
                                                         expected):
    md = ModDetails('dummy', cfg_ioc_version=cfg, latest_release=latest)
    assert md.cfg_ioc_version_class == expected
