"""Base type for objects supporting yakonfig.

.. This software is released under an MIT/X11 open source license.
   Copyright 2014 Diffeo, Inc.

Purpose
=======

Provides a common place to declare command-line arguments and default
configuration to yakonfig.  Configurable object classes can be passed
into :func:`yakonfig.toplevel.parse_args`.  This will cause
yakonfig to instantiate the relevant command-line arguments, parse any
inbound YAML configuration, fill in defaults, and produce a complete
configuration.

Only :attr:`Configurable.config_name` is strictly required, the
remainder of the functions can be absent or have defaults similar to
what is here.

Implementations of these methods may also find :func:`check_subconfig`
useful.

Implementation Details
======================

:func:`yakonfig.toplevel.parse_args` doesn't actually require
:class:`Configurable` subclasses as its parameter; any object (e.g.,
module objects) that include the required names can be used.

Module Contents
===============
"""

from __future__ import absolute_import
import abc
import collections

import yakonfig

class Configurable(object):
    """Description of yakonfig configuration.

    This class provides a common place to define information that
    drives the configuration process.  Yakonfig doesn't actually
    require instances of this type, merely objects that provide the
    object and method names described here, and of these only
    :attr:`config_name` is truly required.

    For instance, if you create a subclass of this and then use
    yakonfig to configure it, yakonfig will fill in the default
    values described here

    >>> class MyConfigurable(object):
    ...     config_name = "me"
    ...     default_config = { 'key': 'value' }
    >>> yakonfig.set_default_config([MyConfigurable])
    >>> yaml.dump(yakonfig.get_global_config())
    me:
        key: value

    If you subclass this, you will need to pass instances of this
    object to the :module:`yakonfig.toplevel` methods, not the class
    itself.  A corollary to this is that it is possible for the
    command-line arguments to vary based on parameters to this
    object's constructor.

    If you want command-line arguments to be able to affect the
    configuration this object describes, add them in
    :meth:`add_arguments()`, and set :attr:`runtime_keys` to a mapping
    from argparse name to config key name.

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def config_name(self):
        """Name of this configuration block."""
        return None

    @property
    def default_config(self):
        """Default values for configuration.

        This is a dictionary mapping configuration key name to configuration
        value.  It should not include any configured sub-objects.

        """
        return {}

    @property
    def sub_modules(self):
        """Modules this module controls.

        This is any iterable containing a sequence of
        :class:`Configurable` objects (or objects that act like them).
        Those configurations will be stored under this object's
        configuration, with the names specified by their
        :attr:`config_name` properties.

        """
        return []

    def add_arguments(self, parser):
        """Add additional command-line arguments to `parser`.

        :param parser: command-line argument parser
        :type parser: :class:`argparse.ArgumentParser`

        """
        pass

    @property
    def runtime_keys(self):
        """Mapping of argparse keys to configuration keys.

        This is used to capture the command-line arguments in
        :meth:`add_arguments`.  It is a dictionary mapping argparse
        argument name to configuration key name.

        """
        return {}

    def replace_config(self, config, name=''):
        '''Look at `config` and return a new :class:`Configurable`.

        This can, for instance, load external modules pointed to by
        a configuration file, and return a new :class:`ProxyConfigurable`
        for this with a new :attr:`sub_modules` list.  The yakonfig
        framework will not recursively call this function on submodules.

        :param dict config: configuration of this object and its children
        :param str name: name of the configuration block
        :return: replacement for `self`
        :rtype: :class:`Configurable`
        :raises yakonfig.exceptions.ConfigurationError: if the new
          configuration cannot be generated
        '''
        return self

    def check_config(self, config, name=''):
        """Validate the configuration of this object.

        If something is missing, incorrect, or inconsistent, raise a
        :exc:`yakonfig.exceptions.ConfigurationError`.

        :param dict config: configuration of this object and its children
        :param str name: name of the configuration block, ending in
          :attr:`config_name`
        :raises yakonfig.exceptions.ConfigurationError: if the
          configuration is invalid in some way

        """
        pass

    pass

class ProxyConfigurable(Configurable):
    '''A yakonfig configurable object that passes calls on to something else.

    The object this proxies can be any any configurable thing, not
    necessarily a :class:`Configurable` instance.  Any methods that
    are not implemented in the underlying object return default
    values.

    This class is intended to be used as a base class for
    :meth:`Configurable.replace_config` implementations.

    .. automethod:: __init__
    '''

    def __init__(self, config=None, *args, **kwargs):
        '''Create a new proxy configurable.

        :param config: object to pass options on to
        :type config: :class:`Configurable`

        '''
        super(ProxyConfigurable, self).__init__(*args, **kwargs)
        self.config = config

    def _property(self, name):
        if hasattr(self.config, name):
            return getattr(self.config, name)
        return getattr(super(ProxyConfigurable, self), name)

    @property
    def config_name(self): return self._property('config_name')
    @property
    def default_config(self): return self._property('default_config')
    @property
    def sub_modules(self): return self._property('sub_modules')

    def add_arguments(self, parser):
        if hasattr(self.config, 'add_arguments'):
            return getattr(self.config, 'add_arguments')(parser)
        return super(ProxyConfigurable, self).add_arguments(parser)

    @property
    def runtime_keys(self): return self._property('runtime_keys')

    def replace_config(self, config, name=''):
        if hasattr(self.config, 'replace_config'):
            return getattr(self.config, 'replace_config')(config, name)
        return super(ProxyConfigurable, self).replace_config(config, name)

    def check_config(self, config, name=''):
        if hasattr(self.config, 'check_config'):
            return getattr(self.config, 'check_config')(config, name)
        return super(ProxyConfigurable, self).check_config(config, name)

class NewSubModules(ProxyConfigurable):
    '''A proxy that only replaces the :attr:`sub_modules` list.

    This is expected to be the common use case for
    :meth:`replace_config()`.

    .. automethod: __init__
    '''
    def __init__(self, config=None, sub_modules=[], *args, **kwargs):
        '''Create a new proxy with new :attr:`sub_modules`.

        :param config: original `Configurable` object
        :type config: :class:`Configurable`
        :param sub_modules: new `sub_modules` list
        :type sub_modules: list of :class:`Configurable`

        '''
        super(NewSubModules, self).__init__(config=config, *args, **kwargs)
        self._sub_modules = sub_modules

    @property
    def sub_modules(self): return self._sub_modules

def check_subconfig(config, name, sub):
    """Validate the configuration of an object within this.

    This calls :meth:`Configurable.check_config` or equivalent on `sub`.
    A dictionary configuration for `sub` is required in `config`.

    >>> def check_config(config, name):
    ...     for sub in sub_modules:
    ...         check_subconfig(config, name, sub)

    :param dict config: parent configuration
    :param str name: name of the parent configuration block
    :param sub: Configurable-like subobject to check
    :raise yakonfig.exceptions.ConfigurationError: if there is no
      configuration for `sub`, or it is not a dictionary

    """
    subname = sub.config_name
    subconfig = config.setdefault(subname, {})
    if not isinstance(subconfig, collections.Mapping):
        raise yakonfig.ProgrammerError('configuration for {} in {} '
                                       'must be a mapping'
                              .format(subname, name))
    checker = getattr(sub, 'check_config', None)
    if checker is not None:
        checker(subconfig, '{}.{}'.format(name, subname))
