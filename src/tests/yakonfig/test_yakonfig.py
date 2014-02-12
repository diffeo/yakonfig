#!python

import argparse
import pytest
import os
import tempfile
from StringIO import StringIO

from yakonfig import \
    set_global_config, get_global_config, \
    clear_global_config, \
    set_runtime_args_object, set_runtime_args_dict

from tests.yakonfig.setup_logging import logger

## for use in fixture below
import yakonfig.yakonfig as yakonfig_internals

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


def test_yakonfig_runtime_argparse(reset_globals):
    ap = argparse.ArgumentParser()
    ap.add_argument('--one')
    ap.add_argument('--two')
    args = ap.parse_args('--one=fish --two=FISH'.split())
    set_runtime_args_object(args)
    
    YAML_TEXT_TWO = StringIO('''
pipeline_property1: run_fast
pipeline_property2: no_errors
runtime_all: !runtime
runtime_one: !runtime one
runtime_two: !runtime two
''')
    config = set_global_config(YAML_TEXT_TWO)

    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'
    assert config['runtime_one'] == 'fish'
    assert config['runtime_two'] == 'FISH'
    assert config['runtime_all'] == {'one':'fish', 'two':'FISH'}


def test_yakonfig_runtime_dict(reset_globals):
    set_runtime_args_dict({'one':'fish', 'two':'FISH'})
    
    YAML_TEXT_TWO = StringIO('''
pipeline_property1: run_fast
pipeline_property2: no_errors
runtime_all: !runtime
runtime_one: !runtime one
runtime_two: !runtime two
''')
    config = set_global_config(YAML_TEXT_TWO)
    
    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'
    assert config['runtime_one'] == 'fish'
    assert config['runtime_two'] == 'FISH'
    assert config['runtime_all'] == {'one':'fish', 'two':'FISH'}


def test_yakonfig_get_global_config(reset_globals):
    set_runtime_args_dict(dict(two='FISH'))
    
    YAML_TEXT_TWO = StringIO('''
app_one:
  one: car
  two: !runtime two

app_two:
  bad: [cat, horse]
''')
    config = set_global_config(YAML_TEXT_TWO)
    
    assert get_global_config() is config
    sub_config = get_global_config('app_one')

    assert sub_config is config['app_one']
    assert sub_config['one'] == 'car'

    ## no "deep update"
    assert sub_config['two'] == 'FISH'

@pytest.fixture
def monkeypatch_open(request):
    ## cannot pytest.monkeypatch a builtin like `open`, so instead,
    ## override method on Loader class
    def other_open(*args, **kwargs):
        fh = StringIO('''
k1: v1
k2: 
 - v21
 - !runtime two
''')
        fh.__exit__ = lambda x,y,z: None
        fh.__enter__ = lambda : fh
        return fh
    real_open = yakonfig_internals.Loader.open
    yakonfig_internals.Loader.open = other_open
    def fin():
        yakonfig_internals.Loader.open = real_open
    request.addfinalizer(fin)

def test_include_abstract(reset_globals, monkeypatch_open):
    set_runtime_args_dict(dict(two='FISH'))    
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
    assert sub_config['good'] == dict(k1='v1', k2=['v21', 'FISH'])


def test_include_real_paths(reset_globals):
    set_runtime_args_dict(dict(two='FISH'))
    t1 = tempfile.NamedTemporaryFile()
    t2 = tempfile.NamedTemporaryFile()
    t3 = tempfile.NamedTemporaryFile()
    y1 = '''
t1:
  k3: !include_yaml %s
  k4: !include_yaml %s
''' % (t2.name, os.path.basename(t3.name))
    print y1
    y2 = 'dog'
    y3 = '!runtime two'
    t1.write(y1)
    t2.write(y2)
    t3.write(y3)
    t1.flush()
    t2.flush()
    t3.flush()

    config = set_global_config(t1.name)
    assert get_global_config() is config
    print config
    sub_config = get_global_config('t1')
    assert sub_config is config['t1']
    assert sub_config['k3'] == y2
    assert sub_config['k4'] == 'FISH'


def func_that_makes_yaml():
    return '''
k9:
  g4: !runtime two
'''

def test_include_func(reset_globals):
    set_runtime_args_dict(dict(two='FISH'))
    YAML_TEXT_TWO = StringIO('''
app_one:
  one: car

app_two:
  bad: [cat, horse]
  good: !include_func tests.yakonfig.test_yakonfig.func_that_makes_yaml
''')
    config = set_global_config(YAML_TEXT_TWO)
    assert get_global_config() is config
    assert get_global_config('app_one') == dict(one='car')
    sub_config = get_global_config('app_two')
    assert sub_config is config['app_two']
    assert sub_config['good'] == dict(k9=dict(g4='FISH'))


def test_include_runtime(reset_globals):
    t1 = tempfile.NamedTemporaryFile()
    t1.write('k3: golden')
    t1.flush()
    ## make the yaml file's name appear as a command line input
    set_runtime_args_dict(dict(two=t1.name))
    YAML_TEXT_TWO = StringIO('''
one: !include_runtime two
''')
    config = set_global_config(YAML_TEXT_TWO)
    assert config == dict(one=dict(k3='golden'))

