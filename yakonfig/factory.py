from __future__ import absolute_import, division, print_function
import abc
import copy
import inspect

from yakonfig.configurable import Configurable
from yakonfig.exceptions import ConfigurationError, ProgrammerError


try:
    strtype = basestring
except NameError:
    strtype = str


class AutoFactory (Configurable):
    '''
    A factory for *discovering* configuration from functions, methods
    or classes. Clients that subclass ``AutoFactory`` must implement
    the ``auto_config`` property, which should be an iterable of things
    to automatically a configuration from. Notably, subclasses should
    *not* implement ``sub_modules``, as this class provides its own
    implementation of it using ``auto_config``.

    Currently, this class does **not** support a hierarchical
    configuration.
    '''
    __metaclass__ = abc.ABCMeta

    @property
    def sub_modules(self):
        return [create_configurable(obj) for obj in self.auto_config]

    @abc.abstractproperty
    def auto_config(self):
        '''
        Must return a list of objects to automatically configure.

        This list is interpreted shallowly. That is, all configuration
        from each object is discovered through its name and parameter
        list only. Everything else is ignored.
        '''
        pass

    def create(self, config, configurable):
        '''
        Instantiates the ``configurable`` object with the
        configuration ``config`` given. This essentially translates
        to ``configurable(**config)``, except services defined
        in the parent and requested by ``configurable`` (by
        setting the ``services`` attribute) are injected. If a
        service is not defined on this factory object, then a
        :exc:`yakonfig.ProgrammerError` is raised.

        If ``configurable`` does not satisfy the
        :class:`yakonfig.Configurable` interface, then its
        configuration is automatically discovered.

        ``config`` should be a dictionary with the key
        ``configurable.config_name``. If the key does not exist, then
        an empty configuration is given to ``configurable``.

        Neither ``config`` or ``configurable`` are modified.
        ``configurable`` is given a *deep* copy of the configuration.
        '''
        # XXX: This whole approach may be bogus. @dmaze should review it.
        # N.B. This would be much more convenient if we could eliminate the
        # `config` parameter somehow (thereby eliminating global config!?!).

        # Regenerate the configuration ifneedbe.
        if not hasattr(configurable, 'config_name'):
            configurable = create_configurable(configurable)

        # don't mutate given config
        kwargs = copy.deepcopy(config.get(configurable.config_name, {}))
        # Check to make sure there is nothing in `kwargs` that isn't in the
        # default config. If there is, then the user has provided a
        # configuration option that isn't supported.
        extras = set(kwargs.keys()).difference(configurable.default_config)
        if len(extras) > 0:
            raise ConfigurationError(
                'Unsupported config options for "%s": %s'
                % (configurable.config_name, ', '.join(extras)))
        for other in getattr(configurable, 'services', []):
            if other in kwargs:
                # I don't know what the right thing to do is here,
                # so be conservative and raise an error.
                #
                # N.B. I don't think this can happen when using auto-config
                # because Python will not let you have `arg` and `arg=val`
                # in the same parameter list. (`discover_config`, below,
                # guarantees that positional and named parameters are 
                # disjoint.)
                raise ProgrammerError('Configured object "%s" expects a '
                                      '"%s" object to be available (from its '
                                      'parameter list), but "%s" is already '
                                      'defined as "%s" in its configuration.'
                                      % (repr(configurable), other, other,
                                         kwargs[other]))
            if not hasattr(self, other):
                raise ProgrammerError('Configured object "%s" expects a '
                                      '"%s" object to be available (from its '
                                      'parameter list), but "%s" does not '
                                      'provide it.'
                                      % (repr(configurable), other,
                                         repr(self)))
            kwargs[other] = getattr(self, other)
        return configurable(**kwargs)


def create_configurable(obj):
    '''
    Given an ``obj``, which must be a function, method
    or class, this returns a function that satisfies the
    :class:`yakonfig.Configurable` interface with a configuration
    discovered from ``obj``. ``obj`` is not modified.

    A :exc:`yakonfig.ProgrammerError` is also raised if there was a
    problem discovering a configuration from ``obj``.
    '''
    # Using a function probably isn't a tenable strategy going forward if
    # we want to allow auto-configurable things to have children.
    def as_configurable(obj, config_name, services, default_config):
        def init(*args, **kwargs):
            return obj(*args, **kwargs)
        init.config_name = config_name
        init.services = services
        init.default_config = default_config
        return init
    c = discover_config(obj)
    return as_configurable(obj, c['name'], c['required'], c['defaults'])


def discover_config(obj):
    '''
    Given an object ``obj``, which must be a function, method or class,
    return a configuration *discovered* from the name of the object and
    its parameter list. This function is responsible for doing runtime
    reflection and providing understandable failure modes.

    The return value is a dictionary with three keys: ``name``,
    ``required`` and ``defaults``. ``name`` is the name of the
    function/method/class. ``required`` is a list of parameters
    *without* default values. ``defaults`` is a dictionary mapping
    parameter names to default values. The sets of parameter names in
    ``required`` and ``defaults`` are disjoint.

    When given a class, the parameters are taken from its ``__init__``
    method.

    Note that this function is purposefully conservative in the things
    that is will auto-configure. All of the following things will result
    in a :exc:`yakonfig.ProgrammerError` exception being raised:

    1. A parameter list that contains tuple unpacking. (This is invalid
       syntax in Python 3.)
    2. A parameter list that contains variable arguments (``*args``) or
       variable keyword words (``**kwargs``). This restriction forces
       an auto-configurable to explicitly state all configuration.

    Similarly, if given an object that isn't a function/method/class, a
    :exc:`yakonfig.ProgrammerError` will be raised. (It is a bug if any
    other exception is raised.)
    '''
    if inspect.isfunction(obj):
        name = obj.__name__
        inspect_obj = obj
    elif inspect.ismethod(obj):
        name = obj.im_func.__name__
        inspect_obj = obj
    elif inspect.isclass(obj):
        if not hasattr(obj, '__init__'):
            raise ProgrammerError('Class "%s" does not have an "__init__" '
                                  'method, so it cannot be auto configured.'
                                  % str(obj))
        name = obj.__name__
        inspect_obj = obj.__init__
        if not inspect.ismethod(inspect_obj):
            raise ProgrammerError('"%s.__init__" is not a method '
                                  '(it is a "%s").' % (str(obj), type(obj)))
    else:
        raise ProgrammerError('Expected a function, method or class to '
                              'automatically configure, but got a "%s" '
                              '(type: "%s").' % (repr(obj), type(obj)))

    try:
        argspec = inspect.getargspec(obj)
    except TypeError as e:
        raise ProgrammerError('Cannot detect config for "%s": %s'
                              % (repr(obj), str(e)))
    if argspec.varargs is not None or argspec.keywords is not None:
        raise ProgrammerError('The auto-configurable "%s" cannot contain '
                              '"*args" or "**kwargs" in its list of '
                              'parameters.' % repr(obj))
    if not all(isinstance(arg, strtype) for arg in argspec.args):
        raise ProgrammerError('Expected an auto-configurable with no nested '
                              'parameters, but "%s" seems to contain some '
                              'tuple unpacking: "%s"'
                              % (repr(obj), argspec.args))

    defaults = argspec.defaults or []
    # The index into `argspec.args` at which keyword arguments with default
    # values starts.
    i_defaults = len(argspec.args) - len(defaults)
    return {
        'name': name,
        'required': argspec.args[0:i_defaults],
        'defaults': {k: defaults[i]
                     for i, k in enumerate(argspec.args[i_defaults:])},
    }
