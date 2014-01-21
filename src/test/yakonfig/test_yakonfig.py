#!python

import argparse
from StringIO import StringIO

import pytest

from yakonfig import \
    set_global_config, get_global_config, \
    set_runtime_args_object, set_runtime_args_dict

# for cheating
import yakonfig.yakonfig as yakonfig_internals


def _reset_globals():
    yakonfig_internals._config_cache = None
    yakonfig_internals._runtime_args_object = None
    yakonfig_internals._runtime_args_dict = None
    yakonfig_internals._config_file_path = None


def test_yakonfig_simple():
    _reset_globals()
    YAML_TEXT_ONE = StringIO('''
pipeline_property1: run_fast
pipeline_property2: no_errors
''')
    config = set_global_config(stream=YAML_TEXT_ONE)

    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'


def test_yakonfig_runtime_argparse():
    _reset_globals()
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
    config = set_global_config(stream=YAML_TEXT_TWO)

    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'
    assert config['runtime_one'] == 'fish'
    assert config['runtime_two'] == 'FISH'
    assert config['runtime_all'] == {'one':'fish', 'two':'FISH'}


def test_yakonfig_runtime_dict():
    _reset_globals()
    set_runtime_args_dict({'one':'fish', 'two':'FISH'})
    
    YAML_TEXT_TWO = StringIO('''
pipeline_property1: run_fast
pipeline_property2: no_errors
runtime_all: !runtime
runtime_one: !runtime one
runtime_two: !runtime two
''')
    config = set_global_config(stream=YAML_TEXT_TWO)
    
    assert get_global_config() is config

    assert config['pipeline_property1'] == 'run_fast'
    assert config['pipeline_property2'] == 'no_errors'
    assert config['runtime_one'] == 'fish'
    assert config['runtime_two'] == 'FISH'
    assert config['runtime_all'] == {'one':'fish', 'two':'FISH'}


def test_yakonfig_get_global_config():
    _reset_globals()
    set_runtime_args_dict(dict(app_one=dict(one='fish', two='FISH'), 
                               app_two=dict(good='dog')))
    
    YAML_TEXT_TWO = StringIO('''
app_one:
  one: car

app_two:
  bad: [cat, horse]
''')
    config = set_global_config(stream=YAML_TEXT_TWO)
    
    assert get_global_config() is config
    sub_config = get_global_config('app_one')

    assert sub_config is config['app_one']
    assert sub_config['one'] == 'car'

    ## no "deep update"
    assert 'two' not in sub_config


# TODO: test !include using pytest.monkeypach of open() to load a StringIO()
