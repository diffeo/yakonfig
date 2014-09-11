from __future__ import absolute_import, division, print_function

import pytest

import yakonfig
from yakonfig import ConfigurationError, ProgrammerError
from yakonfig.factory import AutoFactory, discover_config


def test_no_tuple_unpacking():
    def fun((a, b)): pass
    with pytest.raises(ProgrammerError):
        discover_config(fun)


def test_no_var_args():
    def fun(*args): pass
    with pytest.raises(ProgrammerError):
        discover_config(fun)


def test_no_var_kw_args():
    def fun(**kwargs): pass
    with pytest.raises(ProgrammerError):
        discover_config(fun)


def test_bad_class():
    class OldStyle:
        pass
    with pytest.raises(ProgrammerError):
        discover_config(OldStyle)


def configurable_defaults(a=1, b=2, c=3):
    return {'a': a, 'b': b, 'c': c}


def configurable_services(abc, xyz):
    return {'abc': abc, 'xyz': xyz}


def configurable_both(abc, xyz, a=1, b=2, c=3):
    return dict(configurable_services(abc, xyz),
                **configurable_defaults(a=a, b=b, c=c))


def test_discover_defaults():
    conf = discover_config(configurable_defaults)
    assert conf == {
        'name': 'configurable_defaults',
        'required': [],
        'defaults': {'a': 1, 'b': 2, 'c': 3},
    }


def test_discover_services():
    conf = discover_config(configurable_services)
    assert conf == {
        'name': 'configurable_services',
        'required': ['abc', 'xyz'],
        'defaults': {},
    }


def test_discover_both():
    conf = discover_config(configurable_both)
    assert conf == {
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
    yakonfig.set_default_config([factory], config=config)
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_defaults)
        assert instantiated == configurable_defaults(b=42)
    finally:
        yakonfig.clear_global_config()


def test_factory_defaults_override():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'b': 42}}}
    yakonfig.set_default_config([factory], config=config)
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_defaults, b=43)
        assert instantiated == configurable_defaults(b=43)
    finally:
        yakonfig.clear_global_config()


def test_factory_services():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    yakonfig.set_default_config([factory])
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_services)
        assert instantiated == configurable_services('abc', 'xyz')
    finally:
        yakonfig.clear_global_config()


def test_factory_defaults_and_services():
    factory = create_factory([configurable_both])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    config = {'SimpleAutoFactory': {'configurable_both': {'c': 42}}}
    yakonfig.set_default_config([factory], config=config)
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        instantiated = factory.create(conf, configurable_both)
        assert instantiated == configurable_both('abc', 'xyz', c=42)
    finally:
        yakonfig.clear_global_config()


def test_factory_missing_service():
    factory = create_factory([configurable_services])
    # Not adding any services to `factory`...
    yakonfig.set_default_config([factory])
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        with pytest.raises(ProgrammerError):
            factory.create(conf, configurable_services)
    finally:
        yakonfig.clear_global_config()


def test_factory_service_config_conflict():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    config = {'SimpleAutoFactory': {'configurable_services': {'abc': 'abc'}}}
    yakonfig.set_default_config([factory], config=config)
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        with pytest.raises(ConfigurationError):
            factory.create(conf, configurable_services)
    finally:
        yakonfig.clear_global_config()


def test_factory_extra_config():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'ZZZ': 42}}}
    yakonfig.set_default_config([factory], config=config)
    try:
        conf = yakonfig.get_global_config()['SimpleAutoFactory']
        with pytest.raises(ConfigurationError):
            factory.create(conf, configurable_defaults)
    finally:
        yakonfig.clear_global_config()
