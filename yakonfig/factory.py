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
    '''A factory for *discovering* configuration from functions, methods
    or classes.

    Clients that subclass :class:`AutoFactory` must implement the
    :attr:`auto_config` property, which should be an iterable of
    things to automatically a configuration from. Notably, subclasses
    should *not* implement :attr:`~yakonfig.Configurable.sub_modules`,
    as this class provides its own implementation of it using
    :attr:`auto_config`.

    This class hooks into the :mod:`yakonfig` configuration sequence
    to capture its part of the configuration at startup time.  If
    this class is used outside the standard sequence, then you must
    set :attr:`config` before calling :meth:`create`.

    Currently, this class does **not** support a hierarchical
    configuration: items in :attr:`auto_config` may not be
    :class:`~yakonfig.Configurable`, and :class:`AutoFactory` objects
    may not be nested.  This is likely to change in the future.

    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, config=None):
        '''Create a new object factory.

        If `config` is :const:`None` (the default), then the
        :attr:`config` property must be set before calling
        :meth:`create`.  Passing this factory object to
        :func:`yakonfig.parse_args` or a similar high-level
        :mod:`yakonfig` setup method will also accomplish this.

        :param dict config: local configuration dictionary (if available)
        
        '''
        super(AutoFactory, self).__init__()
        self._config = config

    @property
    def sub_modules(self):
        return [AutoConfigured(obj) for obj in self.auto_config]

    @abc.abstractproperty
    def auto_config(self):
        '''Must return a list of objects to automatically configure.

        This list is interpreted shallowly. That is, all configuration
        from each object is discovered through its name and parameter
        list only. Everything else is ignored.

        '''
        pass


    def check_config(self, config, prefix=''):
        for child in self.sub_modules:
            child.check_config(config)

    def normalize_config(self, config):
        '''Rewrite (and capture) the configuration of this object.'''
        self.config = config

    @property
    def config(self):
        '''Saved configuration for the factory and its sub-objects.'''
        if self._config is None:
            raise ProgrammerError(
                'Tried to access saved factory configuration before '
                'yakonfig configuration was run.')
        return self._config
    @config.setter
    def config(self, c):
        self._config = c
        self.new_config()

    def new_config(self):
        '''Hook called when the configuration changes.

        If factory implementations keep properties that are created
        from the configuration, this is a place to create or reset them.
        The base class implementation does nothing.

        '''
        pass

    def create(self, configurable, config=None, **kwargs):
        '''Create a sub-object of this factory.

        Instantiates the `configurable` object with the current saved
        :attr:`config`.  This essentially translates to
        ``configurable(**config)``, except services defined in the
        parent and requested by `configurable` (by setting the
        ``services`` attribute) are injected. If a service is not
        defined on this factory object, then a
        :exc:`yakonfig.ProgrammerError` is raised.

        If `config` is provided, it is a local configuration for
        `configurable`, and it overrides the saved local configuration
        (if any).  If not provided, then :attr:`config` must already be
        set, possibly by passing this object into the :mod:`yakonfig`
        top-level setup sequence.

        :param callable configurable: object to create
        :param dict config: local configuration for `configurable`
        :param kwargs: additional keyword parameters
        :return: ``configurable(**config)``

        '''
        # If we got passed a string, find the thing to make.
        if isinstance(configurable, str):
            candidates = [ac for ac in self.sub_modules
                          if ac.config_name == configurable]
            if len(candidates) == 0:
                raise KeyError(configurable)
            configurable = candidates[0]

        # Regenerate the configuration ifneedbe.
        if not isinstance(configurable, AutoConfigured):
            configurable = AutoConfigured(configurable)

        if config is None:
            config = self.config.get(configurable.config_name, {})
        # shallow-copy config and append kwargs to it
        config = dict(config, **kwargs)
        for other in getattr(configurable, 'services', []):
            # AutoConfigured.check_config() validates that this key
            # wasn't in the global config, so this must have come from
            # either our own config parameter, a keyword arg, or
            # the caller setting factory.config; trust those paths.
            if other not in config:
                # We're not catching an `AttributeError` exception here because
                # it may case a net too wide which makes debugging underlying
                # errors more difficult.
                config[other] = getattr(self, other)
        return configurable(**config)


class AutoConfigured (Configurable):
    '''
    This is an **unexported** wrapper class that provides an
    implementation that satisfies :class:`yakonfig.Configurable`
    for objects that can have their configuration automatically
    discovered.
    '''
    def __init__(self, obj):
        self.obj = obj
        self._discovered = self._discover_config()
        self._config_name = self._discovered['name']
        self._services = self._discovered['required']
        self._default_config = self._discovered['defaults']

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    @property
    def config_name(self):
        return self._config_name

    @property
    def services(self):
        return self._services

    @property
    def default_config(self):
        return self._default_config

    def check_config(self, config, name=''):
        # This is assuming that `config` is the config dictionary of
        # the *config parent*. That is, `config[self.config_name]`
        # exists.
        config = config.get(self.config_name, {})
        extras = set(config.keys()).difference(self.default_config)
        if len(extras) > 0:
            raise ConfigurationError(
                'Unsupported config options for "%s": %s'
                % (self.config_name, ', '.join(extras)))

        missing = set(self.default_config).difference(config)
        if len(extras) > 0:
            raise ConfigurationError(
                'Missing config options for "%s": %s'
                % (self.config_name, ', '.join(missing)))

        for other in self.services:
            if other in config:
                # I don't know what the right thing to do is here,
                # so be conservative and raise an error.
                #
                # N.B. I don't think this can happen when using auto-config
                # because Python will not let you have `arg` and `arg=val`
                # in the same parameter list. (`discover_config`, below,
                # guarantees that positional and named parameters are 
                # disjoint.)
                raise ProgrammerError(
                    'Configured object "%s" expects a '
                    '"%s" object to be available (from its '
                    'parameter list), but "%s" is already '
                    'defined as "%s" in its configuration.'
                    % (repr(self), other, other, config[other]))

    def _discover_config(self):
        '''
        Given an object at ``self.obj``, which must be a function,
        method or class, return a configuration *discovered* from
        the name of the object and its parameter list. This function
        is responsible for doing runtime reflection and providing
        understandable failure modes.

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
        :exc:`yakonfig.ProgrammerError` will be raised.

        If reflection cannot be performed on ``obj``, then a ``TypeError``
        is raised.
        '''
        obj = self.obj
        skip_params = 0
        if inspect.isfunction(obj):
            name = obj.__name__
            inspect_obj = obj
            skip_params = 0
        elif inspect.ismethod(obj):
            name = obj.im_func.__name__
            inspect_obj = obj
            skip_params = 1  # self
        elif inspect.isclass(obj):
            inspect_obj = None
            if hasattr(obj, '__dict__') and '__new__' in obj.__dict__:
                inspect_obj = obj.__new__
            elif hasattr(obj, '__init__'):
                inspect_obj = obj.__init__
            else:
                raise ProgrammerError(
                    'Class "%s" does not have a "__new__" or "__init__" '
                    'method, so it cannot be auto configured.' % str(obj))
            name = obj.__name__
            if hasattr(obj, 'config_name'):
                name = obj.config_name
            if not inspect.ismethod(inspect_obj) \
                    and not inspect.isfunction(inspect_obj):
                raise ProgrammerError(
                    '"%s.%s" is not a method/function (it is a "%s").'
                    % (str(obj), inspect_obj.__name__, type(inspect_obj)))
            skip_params = 1  # self
        else:
            raise ProgrammerError(
                'Expected a function, method or class to '
                'automatically configure, but got a "%s" '
                '(type: "%s").' % (repr(obj), type(obj)))

        argspec = inspect.getargspec(inspect_obj)
        if argspec.varargs is not None or argspec.keywords is not None:
            raise ProgrammerError(
                'The auto-configurable "%s" cannot contain '
                '"*args" or "**kwargs" in its list of '
                'parameters.' % repr(obj))
        if not all(isinstance(arg, strtype) for arg in argspec.args):
            raise ProgrammerError(
                'Expected an auto-configurable with no nested '
                'parameters, but "%s" seems to contain some '
                'tuple unpacking: "%s"'
                % (repr(obj), argspec.args))

        defaults = argspec.defaults or []
        # The index into `argspec.args` at which keyword arguments with default
        # values starts.
        i_defaults = len(argspec.args) - len(defaults)
        return {
            'name': name,
            'required': argspec.args[skip_params:i_defaults],
            'defaults': {k: defaults[i]
                         for i, k in enumerate(argspec.args[i_defaults:])},
        }
