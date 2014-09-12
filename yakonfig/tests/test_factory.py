from __future__ import absolute_import, division, print_function

import pytest

import yakonfig
from yakonfig import ConfigurationError, ProgrammerError
from yakonfig.factory import AutoFactory, AutoConfigured


def test_no_tuple_unpacking():
    def fun((a, b)): pass
    with pytest.raises(ProgrammerError):
        AutoConfigured(fun)


def test_no_var_args():
    def fun(*args): pass
    with pytest.raises(ProgrammerError):
        AutoConfigured(fun)


def test_no_var_kw_args():
    def fun(**kwargs): pass
    with pytest.raises(ProgrammerError):
        AutoConfigured(fun)


def test_bad_class():
    class OldStyle:
        pass
    with pytest.raises(ProgrammerError):
        AutoConfigured(OldStyle)


def configurable_defaults(a=1, b=2, c=3):
    return {'a': a, 'b': b, 'c': c}


def configurable_services(abc, xyz):
    return {'abc': abc, 'xyz': xyz}


def configurable_both(abc, xyz, a=1, b=2, c=3):
    return dict(configurable_services(abc, xyz),
                **configurable_defaults(a=a, b=b, c=c))


def test_discover_defaults():
    conf = AutoConfigured(configurable_defaults)
    assert conf._discovered == {
        'name': 'configurable_defaults',
        'required': [],
        'defaults': {'a': 1, 'b': 2, 'c': 3},
    }


def test_discover_services():
    conf = AutoConfigured(configurable_services)
    assert conf._discovered == {
        'name': 'configurable_services',
        'required': ['abc', 'xyz'],
        'defaults': {},
    }


def test_discover_both():
    conf = AutoConfigured(configurable_both)
    assert conf._discovered == {
        'name': 'configurable_both',
        'required': ['abc', 'xyz'],
        'defaults': {'a': 1, 'b': 2, 'c': 3},
    }


def create_factory(configurables):
    class SimpleAutoFactory (AutoFactory):
        config_name = 'SimpleAutoFactory'
        @property
        def auto_config(self):
            return configurables
    return SimpleAutoFactory()


def test_factory_defaults():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'b': 42}}}
    with yakonfig.defaulted_config([factory], config=config):
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_defaults)
        assert instantiated == configurable_defaults(b=42)


def test_factory_defaults_override():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'b': 42}}}
    with yakonfig.defaulted_config([factory], config=config):
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_defaults, b=43)
        assert instantiated == configurable_defaults(b=43)


def test_factory_services():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    with yakonfig.defaulted_config([factory]):
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_services)
        assert instantiated == configurable_services('abc', 'xyz')


def test_factory_defaults_and_services():
    factory = create_factory([configurable_both])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    config = {'SimpleAutoFactory': {'configurable_both': {'c': 42}}}
    with yakonfig.defaulted_config([factory], config=config):
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_both)
        assert instantiated == configurable_both('abc', 'xyz', c=42)


def test_factory_missing_service():
    factory = create_factory([configurable_services])
    # Not adding any services to `factory`...
    with yakonfig.defaulted_config([factory]):
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        with pytest.raises(ProgrammerError):
            factory.create(conf, configurable_services)


def test_factory_service_config_conflict():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    config = {'SimpleAutoFactory': {'configurable_services': {'abc': 'abc'}}}
    with pytest.raises(ConfigurationError):
        yakonfig.set_default_config([factory], config=config)


def test_factory_extra_config():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'ZZZ': 42}}}
    with pytest.raises(ConfigurationError):
        yakonfig.set_default_config([factory], config=config)
