from __future__ import absolute_import, division, print_function

import pytest

import yakonfig
from yakonfig import ConfigurationError, ProgrammerError
from yakonfig.factory import AutoFactory, AutoConfigured


# AutoFactory rejects this; but in part because it's outright invalid syntax
# in Python 3.  There's no way to really include it in a dual-version file.
#
# def test_no_tuple_unpacking():
#     def fun((a, b)):
#         pass
#     with pytest.raises(ProgrammerError):
#         AutoConfigured.inspect_obj(fun)


def test_no_var_args():
    def fun(*args):
        pass
    with pytest.raises(ProgrammerError):
        AutoConfigured.inspect_obj(fun)


def test_no_var_kw_args():
    def fun(**kwargs):
        pass
    with pytest.raises(ProgrammerError):
        AutoConfigured.inspect_obj(fun)


def test_bad_class():
    class OldStyle:
        pass
    with pytest.raises(ProgrammerError):
        AutoConfigured.inspect_obj(OldStyle)


def configurable_defaults(a=1, b=2, c=3):
    return {'a': a, 'b': b, 'c': c}


def configurable_services(abc, xyz):
    return {'abc': abc, 'xyz': xyz}


def configurable_both(abc, xyz, a=1, b=2, c=3):
    return dict(configurable_services(abc, xyz),
                **configurable_defaults(a=a, b=b, c=c))


class configurable_class(object):
    def __init__(self, k='v'):
        self.k = k


class configurable_new_class(object):
    def __new__(self, k='new'):
        self.k = k

    def __init__(self, k='init'):
        self.k = k


class ConfigurableAltName(object):
    config_name = 'configurable_alt_name'

    def __init__(self, key='value'):
        self.key = key


class configurable_config_param(object):
    def __init__(self, config):
        self.config = config


class configurable_legacy(object):
    config_name = 'configurable_legacy'
    default_config = {'k': 'v'}

    def __init__(self, config):
        self.config = config


def test_discover_defaults():
    conf = AutoConfigured.inspect_obj(configurable_defaults)
    assert conf == {
        'name': 'configurable_defaults',
        'required': [],
        'defaults': {'a': 1, 'b': 2, 'c': 3},
    }


def test_discover_services():
    conf = AutoConfigured.inspect_obj(configurable_services)
    assert conf == {
        'name': 'configurable_services',
        'required': ['abc', 'xyz'],
        'defaults': {},
    }


def test_discover_both():
    conf = AutoConfigured.inspect_obj(configurable_both)
    assert conf == {
        'name': 'configurable_both',
        'required': ['abc', 'xyz'],
        'defaults': {'a': 1, 'b': 2, 'c': 3},
    }


def test_discover_class():
    conf = AutoConfigured.inspect_obj(configurable_class)
    assert conf == {
        'name': 'configurable_class',
        'required': [],
        'defaults': {'k': 'v'},
    }


def test_discover_new_class():
    conf = AutoConfigured.inspect_obj(configurable_new_class)
    assert conf == {
        'name': 'configurable_new_class',
        'required': [],
        'defaults': {'k': 'new'},
    }


def test_discover_class_alt_name():
    conf = AutoConfigured.inspect_obj(ConfigurableAltName)
    assert conf == {
        'name': 'configurable_alt_name',
        'required': [],
        'defaults': {'key': 'value'},
    }


def test_discover_config_param():
    conf = AutoConfigured.inspect_obj(configurable_config_param)
    assert conf == {
        'name': 'configurable_config_param',
        'required': ['config'],
        'defaults': {},
    }


def test_from_obj_config_param():
    proxy = AutoConfigured.from_obj(configurable_config_param)
    assert isinstance(proxy, AutoConfigured)
    proxy = AutoConfigured.from_obj(configurable_config_param,
                                    any_configurable=True)
    assert isinstance(proxy, AutoConfigured)


def test_discover_legacy():
    conf = AutoConfigured.inspect_obj(configurable_legacy)
    assert conf == {
        'name': 'configurable_legacy',
        'required': ['config'],
        'defaults': {},
    }


def test_from_obj_legacy():
    proxy = AutoConfigured.from_obj(configurable_legacy)
    assert isinstance(proxy, AutoConfigured)
    proxy = AutoConfigured.from_obj(configurable_legacy, any_configurable=True)
    assert proxy is configurable_legacy


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
        instantiated = factory.create(configurable_defaults)
        assert instantiated == configurable_defaults(b=42)


def test_factory_defaults_override():
    factory = create_factory([configurable_defaults])
    config = {'SimpleAutoFactory': {'configurable_defaults': {'b': 42}}}
    with yakonfig.defaulted_config([factory], config=config):
        instantiated = factory.create(configurable_defaults, b=43)
        assert instantiated == configurable_defaults(b=43)


def test_factory_without_config():
    factory = create_factory([configurable_defaults])
    with pytest.raises(yakonfig.ProgrammerError):
        factory.create(configurable_defaults)


def test_factory_explicit_config():
    factory = create_factory([configurable_defaults])
    factory.config = {'configurable_defaults': {'b': 42}}
    instantiated = factory.create(configurable_defaults)
    assert instantiated['a'] == 1
    assert instantiated['b'] == 42
    assert instantiated['c'] == 3


def test_factory_param_config():
    factory = create_factory([configurable_defaults])
    instantiated = factory.create(configurable_defaults, config={'b': 42})
    assert instantiated['a'] == 1
    assert instantiated['b'] == 42
    assert instantiated['c'] == 3


def test_factory_services():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    with yakonfig.defaulted_config([factory]):
        instantiated = factory.create(configurable_services)
        assert instantiated == configurable_services('abc', 'xyz')


def test_factory_services_override():
    factory = create_factory([configurable_services])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    with yakonfig.defaulted_config([factory]):
        instantiated = factory.create(configurable_services, xyz='foo')
        assert instantiated == configurable_services('abc', 'foo')


def test_factory_defaults_and_services():
    factory = create_factory([configurable_both])
    factory.abc = 'abc'
    factory.xyz = 'xyz'
    config = {'SimpleAutoFactory': {'configurable_both': {'c': 42}}}
    with yakonfig.defaulted_config([factory], config=config):
        instantiated = factory.create(configurable_both)
        assert instantiated == configurable_both('abc', 'xyz', c=42)


def test_factory_missing_service():
    factory = create_factory([configurable_services])
    # Not adding any services to `factory`...
    with yakonfig.defaulted_config([factory]):
        with pytest.raises(AttributeError):
            factory.create(configurable_services)


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


def test_factory_class():
    factory = create_factory([configurable_class])
    with yakonfig.defaulted_config([factory], config={}) as config:
        assert 'SimpleAutoFactory' in config
        assert 'configurable_class' in config['SimpleAutoFactory']
        assert config['SimpleAutoFactory']['configurable_class']['k'] == 'v'
        instantiated = factory.create(configurable_class)
        assert instantiated.k == 'v'
        instantiated = factory.create(configurable_class, k='k')
        assert instantiated.k == 'k'


def test_factory_class_by_name():
    factory = create_factory([configurable_class])
    with yakonfig.defaulted_config([factory], config={}):
        instantiated = factory.create('configurable_class')
        assert isinstance(instantiated, configurable_class)
        assert instantiated.k == 'v'


def test_factory_class_with_config_name():
    factory = create_factory([ConfigurableAltName])
    with yakonfig.defaulted_config([factory], config={}) as config:
        assert 'SimpleAutoFactory' in config
        assert 'configurable_alt_name' in config['SimpleAutoFactory']
        assert (config['SimpleAutoFactory']['configurable_alt_name']['key'] ==
                'value')
        instantiated = factory.create(ConfigurableAltName)
        assert instantiated.key == 'value'
        instantiated = factory.create(ConfigurableAltName, key='key')
        assert instantiated.key == 'key'


def test_factory_class_config_param_defaults():
    factory = create_factory([configurable_config_param])
    with yakonfig.defaulted_config([factory], config={}) as config:
        assert 'SimpleAutoFactory' in config
        assert 'configurable_config_param' in config['SimpleAutoFactory']
        instantiated = factory.create(configurable_config_param)
        assert instantiated.config == {}
        instantiated = factory.create(configurable_config_param,
                                      config={'k': 'v'})
        assert instantiated.config == {'k': 'v'}
        instantiated = factory.create(configurable_config_param, a='b')
        assert instantiated.config == {'a': 'b'}


def test_factory_class_config_param():
    factory = create_factory([configurable_config_param])
    config = {'SimpleAutoFactory': {'configurable_config_param': {'k': 'v'}}}
    with yakonfig.defaulted_config([factory], config=config) as config:
        assert 'SimpleAutoFactory' in config
        assert 'configurable_config_param' in config['SimpleAutoFactory']
        instantiated = factory.create(configurable_config_param)
        assert instantiated.config == {'k': 'v'}
        instantiated = factory.create(configurable_config_param,
                                      config={'x': 'y'})
        assert instantiated.config == {'x': 'y'}
        instantiated = factory.create(configurable_config_param, a='b')
        assert instantiated.config == {'k': 'v', 'a': 'b'}


def test_factory_legacy_configurable():
    factory = create_factory([configurable_legacy])
    with yakonfig.defaulted_config([factory], config={}) as config:
        assert 'SimpleAutoFactory' in config
        assert 'configurable_legacy' in config['SimpleAutoFactory']
        instantiated = factory.create(configurable_legacy)
        assert instantiated.config == configurable_legacy.default_config


class FactoryWithProperty(AutoFactory):
    config_name = 'factory_with_property'
    auto_config = [configurable_services]

    @property
    def abc(self):
        return 'foo'

    @property
    def xyz(self):
        return 'bar'


def test_factory_with_property():
    factory = FactoryWithProperty()
    with yakonfig.defaulted_config([factory]):
        instantiated = factory.create(configurable_services)
        assert instantiated['abc'] == 'foo'
        assert instantiated['xyz'] == 'bar'
