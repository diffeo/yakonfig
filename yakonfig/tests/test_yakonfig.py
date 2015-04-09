#!python

from __future__ import absolute_import, division, print_function
import argparse
import logging
import os
import tempfile

import pytest
from six import StringIO

from yakonfig import set_global_config, get_global_config, clear_global_config
## for use in fixture below
import yakonfig.yakonfig as yakonfig_internals

logger = logging.getLogger(__name__)

@pytest.fixture
def reset_globals(request):
    '''
    for fixture that makes each test run as if it were the first call
    to yakonfig
    '''
    clear_global_config()


def test_yakonfig_simple(reset_globals):
    YAML_TEXT_ONE = StringIO('''
pipeline_property1: run_fast
pipeline_property2: no_errors
''')
    config = set_global_config(YAML_TEXT_ONE)

    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'


@pytest.fixture
def monkeypatch_open(request):
    ## cannot pytest.monkeypatch a builtin like `open`, so instead,
    ## override method on Loader class
    def other_open(*args, **kwargs):
        fh = StringIO('''
k1: v1
k2: 
 - v21
''')
        fh.__exit__ = lambda x,y,z: None
        fh.__enter__ = lambda : fh
        return fh
    real_open = yakonfig_internals.Loader.open
    yakonfig_internals.Loader.open = other_open
    def fin():
        yakonfig_internals.Loader.open = real_open
    request.addfinalizer(fin)

def test_include_yaml_abstract(reset_globals, monkeypatch_open):
    YAML_TEXT_TWO = StringIO('''
app_one:
  one: car

app_two:
  bad: [cat, horse]
  good: !include_yaml /some-path-that-will-not-be-used
''')
    config = set_global_config(YAML_TEXT_TWO)
    
    assert get_global_config() is config
    sub_config = get_global_config('app_two')

    assert sub_config is config['app_two']
    assert sub_config['good'] == dict(k1='v1', k2=['v21'])

def test_include_abstract(reset_globals, monkeypatch_open):
    YAML_TEXT_TWO = StringIO('''
app_one:
  one: car

app_two:
  bad: [cat, horse]
  good: !include /some-path-that-will-not-be-used
''')
    config = set_global_config(YAML_TEXT_TWO)
    
    assert get_global_config() is config
    sub_config = get_global_config('app_two')

    assert sub_config is config['app_two']
    assert sub_config['good'] == dict(k1='v1', k2=['v21'])

def test_include_real_paths(reset_globals):
    t1 = tempfile.NamedTemporaryFile()
    t2 = tempfile.NamedTemporaryFile()
    t3 = tempfile.NamedTemporaryFile()
    y1 = u'''
t1:
  k3: !include_yaml %s
  k4: !include_yaml %s
''' % (t2.name, os.path.basename(t3.name))
    print(y1)
    y2 = u'dog'
    y3 = u'two'
    t1.write(y1.encode('utf-8'))
    t2.write(y2.encode('utf-8'))
    t3.write(y3.encode('utf-8'))
    t1.flush()
    t2.flush()
    t3.flush()

    config = set_global_config(t1.name)
    assert get_global_config() is config
    print(config)
    sub_config = get_global_config('t1')
    assert sub_config is config['t1']
    assert sub_config['k3'] == y2
    assert sub_config['k4'] == y3
