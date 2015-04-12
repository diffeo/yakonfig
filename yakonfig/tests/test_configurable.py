'''Tests of various paths through yakonfig.Configurable.

.. This software is released under an MIT/X11 open source license.
   Copyright 2014-2015 Diffeo, Inc.

'''

from __future__ import absolute_import

import argparse

import pytest
from six import iterkeys

import yakonfig
import yakonfig.tests.configurable_module
import yakonfig.toplevel


class ConfigurableSubclass(yakonfig.Configurable):
    @property
    def config_name(self):
        return 'configurable'

    @property
    def default_config(self):
        return {'type': 'object'}


class ConfigurableLike(object):
    config_name = 'configurable'
    default_config = {'type': 'class'}
    runtime_keys = {'key': 'key'}


class ConfigurableArgs(yakonfig.Configurable):
    @property
    def config_name(self):
        return 'config'

    @property
    def default_config(self):
        return {'k': 'k'}

    def add_arguments(self, parser):
        parser.add_argument('-k', '--key', metavar='VALUE')

    @property
    def runtime_keys(self):
        return {'key': 'k'}

    def check_config(self, config, name=''):
        if len(config['k']) != 1:
            raise yakonfig.ConfigurationError("{0} 'k' wrong length"
                                              .format(name))


class ConfigurableBottom(object):
    config_name = 'bottom'
    default_config = {'zzz': '-32768'}

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--zzz', '-z')

    runtime_keys = {'zzz': 'zzz'}


class ConfigurableTop(object):
    config_name = 'top'
    default_config = {'aaa': 'bbb'}
    sub_modules = [ConfigurableBottom]

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--aaa', '-a')

    runtime_keys = {'aaa': 'aaa'}


class ConfigurableAlmostTop(object):
    config_name = 'top'
    default_config = {'aaa': 'bbb'}

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--aaa', '-a')

    runtime_keys = {'aaa': 'aaa'}

    @staticmethod
    def replace_config(config, name):
        return ConfigurableTop


class ConfigurableLikeTop(object):
    config_name = 'top'
    default_config = {'aaa': 'bbb'}

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--aaa', '-a')

    runtime_keys = {'aaa': 'aaa'}

    @staticmethod
    def replace_config(config, name):
        return yakonfig.NewSubModules(ConfigurableLikeTop,
                                      [ConfigurableBottom])


class Dependent(object):
    config_name = 'dependent'

    @staticmethod
    def check_config(config, name):
        yakonfig.check_toplevel_config(ConfigurableArgs(), name)


class Normalized(object):
    config_name = 'normalized'
    default_config = {'k': 'value'}
    runtime_keys = {'k': 'k'}

    @staticmethod
    def normalize_config(config):
        config['k'] = config['k'][0]


class Discovers(object):
    config_name = 'discovers'
    default_config = {'a': 'one', 'c': 'three'}
    runtime_keys = {'a': 'a', 'b': 'b', 'c': 'c'}

    @staticmethod
    def discover_config(config, name):
        if 'a' not in config:
            config['a'] = 'foo'
        if 'b' not in config:
            config['b'] = 'bar'


class NoneDefault(object):
    config_name = 'none_default'
    default_config = {'none': None}


@pytest.fixture(params=['object', 'class', 'module'])
def configurable_type(request):
    return request.param


@pytest.fixture
def a_configurable(configurable_type):
    if configurable_type == 'object':
        return ConfigurableSubclass()
    if configurable_type == 'class':
        return ConfigurableLike
    if configurable_type == 'module':
        return yakonfig.tests.configurable_module
    raise KeyError(configurable_type)


@pytest.yield_fixture
def global_yakonfig(a_configurable):
    yakonfig.set_default_config([a_configurable])
    yield yakonfig.get_global_config()
    yakonfig.clear_global_config()


def test_assemble_default_config(a_configurable, configurable_type):
    c = yakonfig.toplevel.assemble_default_config([a_configurable])
    assert sorted(iterkeys(c)) == ['configurable']
    cc = c['configurable']
    assert sorted(iterkeys(cc)) == ['type']
    assert cc['type'] == configurable_type
    assert cc.get('key') is None


def test_assemble_minimal():
    class MinimallyConfigurable(object):
        config_name = 'minimal'
    c = yakonfig.toplevel.assemble_default_config([MinimallyConfigurable])
    assert sorted(iterkeys(c)) == ['minimal']
    assert c['minimal'] == {}


def test_assemble_broken():
    class NotReallyConfigurable(object):
        pass
    with pytest.raises(yakonfig.ProgrammerError):
        yakonfig.toplevel.assemble_default_config([NotReallyConfigurable])


def test_assemble_two():
    c = yakonfig.toplevel.assemble_default_config([ConfigurableArgs(),
                                                   ConfigurableSubclass()])
    assert sorted(iterkeys(c)) == ['config', 'configurable']
    assert c['config'] == {'k': 'k'}
    assert c['configurable'] == {'type': 'object'}


def test_duplicates():
    with pytest.raises(yakonfig.ProgrammerError):
        yakonfig.toplevel.assemble_default_config([ConfigurableLike,
                                                   ConfigurableSubclass()])


def test_config_type(global_yakonfig, configurable_type):
    c = global_yakonfig
    assert sorted(iterkeys(c)) == ['configurable']
    cc = c['configurable']
    assert sorted(iterkeys(cc)) == ['type']
    assert cc['type'] == configurable_type
    assert cc.get('key') is None


def test_fill_in():
    c = {'configurable': {}}
    yakonfig.toplevel.fill_in_arguments(c, [ConfigurableLike],
                                        {'key': 'value'})
    assert sorted(iterkeys(c)) == ['configurable']
    cc = c['configurable']
    assert sorted(iterkeys(cc)) == ['key']
    assert cc['key'] == 'value'


def test_fill_in_replaces():
    c = { 'configurable': { 'key': 'old' } }
    yakonfig.toplevel.fill_in_arguments(c, [ConfigurableLike],
                                        { 'key': 'new' })
    assert sorted(iterkeys(c)) == ['configurable']
    cc = c['configurable']
    assert sorted(iterkeys(cc)) == ['key']
    assert cc['key'] == 'new'

def test_fill_in_object():
    class Params(object):
        def __init__(self):
            self.key = 'value'
    c = { 'configurable': {} }
    yakonfig.toplevel.fill_in_arguments(c, [ConfigurableLike], Params())
    assert sorted(iterkeys(c)) == ['configurable']
    cc = c['configurable']
    assert sorted(iterkeys(cc)) == ['key']
    assert cc['key'] == 'value'    

def test_default_file(request):
    yakonfig.set_default_config(
        [ConfigurableArgs()],
        filename=str(request.fspath.dirpath('argconfig.yaml')))
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['config']
        cc = c['config']
        assert sorted(iterkeys(cc)) == ['k']
        assert cc['k'] == 'x'
    finally:
        yakonfig.clear_global_config()

def test_fill_in_kvp():
    yakonfig.set_default_config([ConfigurableLike], { 'key': 'value' })
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['configurable']
        cc = c['configurable']
        assert sorted(iterkeys(cc)) == ['key', 'type']
        assert cc['type'] == 'class'
        assert cc['key'] == 'value'
    finally:
        yakonfig.clear_global_config()

def test_prog_yaml():
    the_yaml = """
configurable:
    key: yaml
"""
    yakonfig.set_default_config([ConfigurableLike], yaml=the_yaml)
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['configurable']
        cc = c['configurable']
        assert sorted(iterkeys(cc)) == ['key', 'type']
        assert cc['type'] == 'class'
        assert cc['key'] == 'yaml'
    finally:
        yakonfig.clear_global_config()

def test_prog_yaml():
    # like from the command line, values via params overrides explicit yaml
    the_yaml = """
configurable:
    key: yaml
"""
    yakonfig.set_default_config([ConfigurableLike],
                                params={'key': 'value'},
                                yaml=the_yaml)
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['configurable']
        cc = c['configurable']
        assert sorted(iterkeys(cc)) == ['key', 'type']
        assert cc['type'] == 'class'
        assert cc['key'] == 'value'
    finally:
        yakonfig.clear_global_config()

def test_dont_validate():
    yakonfig.set_default_config([ConfigurableArgs()],
                                params={'key': 'longer than one char'},
                                validate=False)
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['config']
        cc = c['config']
        assert sorted(iterkeys(cc)) == ['k']
        assert cc['k'] == 'longer than one char'
    finally:
        yakonfig.clear_global_config()

def test_two_level():
    yakonfig.set_default_config([ConfigurableTop])
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['top']
        c = c['top']
        assert sorted(iterkeys(c)) == ['aaa', 'bottom']
        assert c['aaa'] == 'bbb'
        c = c['bottom']
        assert sorted(iterkeys(c)) == ['zzz']
        assert c['zzz'] == '-32768'
    finally:
        yakonfig.clear_global_config()

def test_two_level_args():
    yakonfig.set_default_config([ConfigurableTop],
                                { 'aaa': 'a', 'bbb': 'b', 'zzz': 'z' })
    try:
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['top']
        c = c['top']
        assert sorted(iterkeys(c)) == ['aaa', 'bottom']
        assert c['aaa'] == 'a'
        c = c['bottom']
        assert sorted(iterkeys(c)) == ['zzz']
        assert c['zzz'] == 'z'
    finally:
        yakonfig.clear_global_config()

def test_overlay():
    oc = yakonfig.toplevel.overlay_config
    # non-dictionary cases
    assert oc('foo', 'bar') == 'bar'
    assert oc({'k': 'v'}, 'bar') == 'bar'
    assert oc('foo', {'k': 'v'}) == {'k': 'v'}
    # add and remove
    assert oc({'a': 'a'}, {}) == {'a': 'a'}
    assert oc({'a': 'a'}, {'a': None}) == {}
    assert oc({'a': 'a'}, {'a': 'b'}) == {'a': 'b'}
    assert oc({'a': 'a'}, {'b': 'b'}) == {'a': 'a', 'b': 'b'}
    assert oc({'a': 'x', 'b': 'y'}, {}) == {'a': 'x', 'b': 'y'}
    assert oc({'a': 'x', 'b': 'y'}, {'a': None}) == {'b': 'y'}
    assert (oc({'a': 'x', 'b': 'y'}, {'b': 'foo', 'c': 'bar'}) ==
            {'a': 'x', 'b': 'foo', 'c': 'bar'})
    # subobjects
    assert (oc({'a': {'1': 'one'} }, {'a': {'2': 'two'} }) ==
            {'a': {'1': 'one', '2': 'two' }})
    assert (oc({'a': {'1': 'one'} }, {'a': {'1': None} }) ==
            {'a': {} })
    assert (oc({'a': {'1': 'one'} },
               {'a': {'2': 'two'}, 'b': {'3': 'three'} }) ==
            {'a': {'1': 'one', '2': 'two'}, 'b': {'3': 'three'} })

def test_yakonfig_default():
    yakonfig.set_default_config([yakonfig])
    try:
        c = yakonfig.get_global_config()
        assert 'yakonfig' in c
    finally:
        yakonfig.clear_global_config()

def test_yakonfig_cli():
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser, [yakonfig], args=[])
    try:
        c = yakonfig.get_global_config()
        assert 'yakonfig' in c
    finally:
        yakonfig.clear_global_config()    

def test_cli_none():
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser, [ConfigurableArgs()], args=[])
    try:
        c = yakonfig.get_global_config()
        assert 'config' in c
        assert 'k' in c['config']
        assert c['config']['k'] == 'k'
    finally:
        yakonfig.clear_global_config()

def test_cli_good():
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser, [ConfigurableArgs()], args=['--key', 'v'])
    try:
        c = yakonfig.get_global_config()
        assert 'config' in c
        assert 'k' in c['config']
        assert c['config']['k'] == 'v'
    finally:
        yakonfig.clear_global_config()

def test_cli_bad():
    parser = argparse.ArgumentParser()
    with pytest.raises(SystemExit):
        yakonfig.parse_args(parser, [ConfigurableArgs()],
                            args=['--key', 'value'])
        yakonfig.clear_global_config()

def test_cli_file(request):
    yaml = str(request.fspath.dirpath('argconfig.yaml'))
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser,
                        [yakonfig, ConfigurableArgs()],
                        args=['-c', yaml])
    try:
        c = yakonfig.get_global_config()
        assert 'config' in c
        assert 'k' in c['config']
        assert c['config']['k'] == 'x' # from the file
    finally:
        yakonfig.clear_global_config()

def test_cli_overlay(request):
    # config.k is in the default, *and* the config file, *and* the command line
    yaml = str(request.fspath.dirpath('argconfig.yaml'))
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser,
                        [yakonfig, ConfigurableArgs()],
                        args=['-c', yaml, '-k', 'y'])
    try:
        c = yakonfig.get_global_config()
        assert 'config' in c
        assert 'k' in c['config']
        assert c['config']['k'] == 'y' # from the command line
    finally:
        yakonfig.clear_global_config()

def test_check_dependent():
    # give an invalid configuration for args; but it's not the "real"
    # application so it shouldn't be checked
    with yakonfig.defaulted_config([ConfigurableArgs(), ConfigurableLike],
                                   {'key': 'value'}) as config:
        assert sorted(iterkeys(config)) == ['config', 'configurable']
        with pytest.raises(yakonfig.ConfigurationError):
            yakonfig.check_toplevel_config(ConfigurableArgs(), 'test')
        with pytest.raises(yakonfig.ConfigurationError):
            yakonfig.check_toplevel_config(ConfigurableTop, 'test')

def test_check_toplevel():
    '''check_config_toplevel() should work in check_config() implementation'''
    with yakonfig.defaulted_config([ConfigurableArgs(), Dependent],
                                   {'key': 'k'}) as config:
        assert sorted(iterkeys(config)) == ['config', 'dependent']
        assert config['config']['k'] == 'k'
    with pytest.raises(yakonfig.ConfigurationError):
        with yakonfig.defaulted_config([ConfigurableArgs(), Dependent],
                                       {'key': 'key'}):
            pass

def test_check_toplevel_args():
    '''check_config_toplevel() should work in check_config() implementation'''
    parser = argparse.ArgumentParser()
    yakonfig.parse_args(parser, [ConfigurableArgs(), Dependent],
                        ['--key', 'k'])
    try:
        config = yakonfig.get_global_config()
        assert sorted(iterkeys(config)) == ['config', 'dependent']
        assert config['config']['k'] == 'k'
    finally:
        yakonfig.clear_global_config()
    parser = argparse.ArgumentParser()
    with pytest.raises(SystemExit):
        yakonfig.parse_args(parser, [ConfigurableArgs(), Dependent],
                            ['--key', 'key'])
        yakonfig.clear_global_config()

def test_proxy_two_level():
    with yakonfig.defaulted_config(
            [yakonfig.ProxyConfigurable(ConfigurableTop)],
            { 'aaa': 'a', 'bbb': 'b', 'zzz': 'z' }):
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['top']
        c = c['top']
        assert sorted(iterkeys(c)) == ['aaa', 'bottom']
        assert c['aaa'] == 'a'
        c = c['bottom']
        assert sorted(iterkeys(c)) == ['zzz']
        assert c['zzz'] == 'z'

def test_replaces_direct():
    with yakonfig.defaulted_config([ConfigurableAlmostTop]):
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['top']
        c = c['top']
        assert 'bottom' in c
        c = c['bottom']
        assert c['zzz'] == '-32768'

def test_replaces_proxy():
    with yakonfig.defaulted_config([ConfigurableLikeTop]):
        c = yakonfig.get_global_config()
        assert sorted(iterkeys(c)) == ['top']
        c = c['top']
        assert 'bottom' in c
        c = c['bottom']
        assert c['zzz'] == '-32768'

def test_normalize():
    with yakonfig.defaulted_config([Normalized]):
        assert yakonfig.get_global_config('normalized')['k'] == 'v'
    with yakonfig.defaulted_config([Normalized], { 'k': 'foo' }):
        assert yakonfig.get_global_config('normalized')['k'] == 'f'
    with yakonfig.defaulted_config([Normalized],
                                   yaml='''
normalized:
  k: zoom!
'''):
        assert yakonfig.get_global_config('normalized')['k'] == 'z'


def test_discovery():
    with yakonfig.defaulted_config([Discovers]):
        # discovered overwrites default
        assert yakonfig.get_global_config('discovers', 'a') == 'foo'
        # discovered provides missing value
        assert yakonfig.get_global_config('discovers', 'b') == 'bar'
        # undiscovered uses default value
        assert yakonfig.get_global_config('discovers', 'c') == 'three'
    with yakonfig.defaulted_config([Discovers], {'a': 'alpha'}):
        # command-line value overrules discovery
        assert yakonfig.get_global_config('discovers', 'a') == 'alpha'
        assert yakonfig.get_global_config('discovers', 'b') == 'bar'
        assert yakonfig.get_global_config('discovers', 'c') == 'three'


def test_none_default():
    with yakonfig.defaulted_config([NoneDefault]):
        assert yakonfig.get_global_config('none_default', 'none') is None


def test_none_default_rt():
    with yakonfig.defaulted_config([NoneDefault]):
        config = yakonfig.get_global_config()

    with yakonfig.defaulted_config([NoneDefault], config=config):
        assert yakonfig.get_global_config('none_default', 'none') is None
