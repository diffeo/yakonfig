"""Top-level entry points to yakonfig.

.. This software is released under an MIT/X11 open source license.
   Copyright 2014 Diffeo, Inc.

Purpose
=======

Most programs' `main()` functions will call yakonfig as:

>>> parser = argparse.ArgumentParser()
>>> yakonfig.parse_args(parser, [yakonfig, module, module...])

where the list of modules are top-level modules or other
:class:`yakonfig.Configurable` objects the program uses.

Test code and other things not driven by argparse can instead call

>>> yakonfig.set_default_config([yakonfig, module, module, ...])

Module Contents
===============

"""

from __future__ import absolute_import
import collections
import contextlib
from cStringIO import StringIO
import sys

import yaml

import yakonfig
from yakonfig.merge import overlay_config, diff_config
from yakonfig.yakonfig import _temporary_config

# These implement the Configurable interface for yakonfig proper!
config_name = 'yakonfig'
def add_arguments(parser):
    '''Add command-line arguments for yakonfig proper.

    This is part of the :class:`~yakonfig.Configurable` interface, and
    is usually run by including :mod:`yakonfig` in the
    :func:`parse_args()` module list.

    :param argparse.ArgumentParser parser: command-line argument
      parser

    '''
    parser.add_argument('--config', '-c', metavar='FILE',
                        help='read configuration from FILE')
    parser.add_argument('--dump-config', metavar='WHAT', nargs='?',
                        help='dump out configuration then stop '
                        '(default, effective, full)')
runtime_keys = { 'config': 'config' }

def parse_args(parser, modules, args=None):
    """Set up global configuration for command-line tools.

    `modules` is an iterable of
    :class:`yakonfig.Configurable` objects, or anything
    equivalently typed.  This function iterates through those objects
    and calls
    :meth:`~yakonfig.Configurable.add_arguments` on
    each to build up a complete list of command-line arguments, then
    calls :meth:`argparse.ArgumentParser.parse_args` to actually
    process the command line.  This produces a configuration that is a
    combination of all default values declared by all modules;
    configuration specified in ``--config`` arguments; and overriding
    configuration values specified in command-line arguments.

    This returns the :class:`argparse.Namespace` object, in case the
    application has defined its own command-line parameters and
    needs to process them.  The new global configuration can be
    obtained via :func:`yakonfig.get_global_config`.

    :param argparse.ArgumentParser parser: application-provided
      argument parser
    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.Configurable`
    :param args: command-line options, or `None` to use `sys.argv`
    :return: the new global configuration

    """
    collect_add_argparse(parser, modules)
    namespace = parser.parse_args(args)
    try:
        yakonfig.set_default_config(modules, params=vars(namespace))
        if getattr(namespace, 'dump_config', None):
            if namespace.dump_config == 'full':
                to_dump = yakonfig.get_global_config()
            elif namespace.dump_config == 'default':
                to_dump = assemble_default_config(modules)
            else: # 'effective'
                to_dump = diff_config(assemble_default_config(modules),
                                      yakonfig.get_global_config())
            yaml.dump(to_dump, sys.stdout)
            parser.exit()
    except yakonfig.ConfigurationError, e:
        parser.error(e)
    return namespace

def set_default_config(modules, params={}, yaml=None, filename=None,
                       config=None, validate=True):
    """Set up global configuration for tests and noninteractive tools.

    `modules` is an iterable of
    :class:`yakonfig.Configurable` objects, or anything
    equivalently typed.  This function iterates through those objects
    to produce a default configuration, reads `yaml` as though it were
    the configuration file, and fills in any values from `params` as
    though they were command-line arguments.  The resulting
    configuration is set as the global configuration.

    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.Configurable`
    :param dict params: dictionary of command-line argument key to values
    :param str yaml: global configuration file
    :param str filename: location of global configuration file
    :param dict config: global configuration object
    :param bool validate: check configuration after creating
    :return: the new global configuration
    :returntype: dict

    """

    # Get the configuration from the file, or from params['config']
    file_config = {}
    if yaml is None and filename is None and config is None:
        if 'config' in params and params['config'] is not None:
            filename = params['config']
    if yaml is not None or filename is not None or config is not None:
        import yaml as y
        if yaml is not None:
            file_config = y.load(StringIO(yaml))
        elif filename is not None:
            with open(filename, 'r') as f:
                file_config = y.load(f)
        elif config is not None:
            file_config = config

    # Assemble the configuration from defaults + file + arguments
    default_config = assemble_default_config(modules)
    base_config = overlay_config(default_config, file_config)
    fill_in_arguments(base_config, modules, params)
    
    # Replace the modules list (accommodate external modules)
    def replace_module(config, m):
        name = getattr(m, 'config_name')
        c = config.get(name, {})
        if hasattr(m, 'replace_config'):
            return getattr(m, 'replace_config')(c, name)
        return m
    modules = [replace_module(base_config, m) for m in modules]

    # Reassemble the configuration again
    default_config = assemble_default_config(modules)
    base_config = overlay_config(default_config, file_config)
    fill_in_arguments(base_config, modules, params)

    # Validate the configuration
    if validate and len(modules) > 0:
        mod = modules[-1]
        checker = getattr(mod, 'check_config', None)
        if checker is not None:
            with _temporary_config():
                yakonfig.set_global_config(base_config)
                checker(base_config[mod.config_name], mod.config_name)

    # All done, normalize and set the global configuration
    normalize_config(base_config, modules)
    yakonfig.set_global_config(base_config)
    return base_config

@contextlib.contextmanager
def defaulted_config(modules, params={}, yaml=None, filename=None,
                     config=None, validate=True):
    """Context manager version of :func:`set_default_config()`.

    Use this with a Python 'with' statement, like

    >>> config_yaml = '''
    ... toplevel:
    ...   param: value
    ... '''
    >>> with yakonfig.defaulted_config([toplevel], yaml=config_yaml) as config:
    ...    assert 'param' in config['toplevel']
    ...    assert yakonfig.get_global_config('toplevel', 'param') == 'value'

    On exit the global configuration is restored to its previous state
    (if any).

    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.Configurable`
    :param dict params: dictionary of command-line argument key to values
    :param str yaml: global configuration file
    :param str filename: location of global configuration file
    :param dict config: global configuration object
    :param bool validate: check configuration after creating
    :return: the new global configuration

    """
    with _temporary_config():
        set_default_config(modules, params=params, yaml=yaml,
                           filename=filename, config=config, validate=validate)
        yield yakonfig.get_global_config()

def check_toplevel_config(what, who):
    """Verify that some dependent configuration is present and correct.

    This will generally be called from a
    :meth:`~yakonfig.Configurable.check_config` implementation.
    `what` is a :class:`~yakonfig.Configurable`-like object.  If the
    corresponding configuration isn't present in the global
    configuration, raise a :exc:`yakonfig.ConfigurationError`
    explaining that `who` required it.  Otherwise call that module's
    :meth:`~yakonfig.Configurable.check_config` (if any).

    :param yakonfig.Configurable what: top-level module to require
    :param str who: name of the requiring module
    :raise yakonfig.ConfigurationError: if configuration for
      `what` is missing or incorrect

    """
    config_name = what.config_name
    config = yakonfig.get_global_config()
    if config_name not in config:
        raise yakonfig.ConfigurationError(
            '{} requires top-level configuration for {}'
            .format(who, config_name))
    checker = getattr(what, 'check_config', None)
    if checker:
        checker(config[config_name], config_name)

def _walk_config(config, modules, f, prefix='', required=True):
    """Recursively walk through a module list.

    For every module, calls ``f(config, module, name)`` where
    `config` is the configuration scoped to that module, `module`
    is the Configurable-like object, and `name` is the complete
    path (ending in the module name).

    If `required` is true, every name encountered must exist,
    and `yakonfig.ProgrammerError` will be raised if it doesn't.
    If `required` is false, every name encountered must not exist,
    and `yakonfig.ProgrammerError` will be raised if it does.
    `required=False` is intended to only be used when setting up
    the default configuration.

    :param dict config: configuration to walk and possibly update
    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.configurable.Configurable`
    :param f: callback function for each module
    :param str prefix: prefix name of the config
    :param bool required: if true, config names already exist
    :return: config

    """
    for module in modules:
        name = getattr(module, 'config_name', None)
        if name is None:
            raise yakonfig.ProgrammerError('{!r} must provide a config_name'
                                           .format(module))
        new_name = '{}{}'.format(prefix, name)
        if required:
            if name not in config:
                raise yakonfig.ProgrammerError('{} not present in configuration'
                                               .format(new_name))
            if not isinstance(config[name], collections.Mapping):
                raise yakonfig.ConfigurationError(
                    '{} must be an object configuration'.format(new_name))
        else:
            if name in config:
                raise yakonfig.ProgrammerError('multiple modules providing {}'
                                               .format(new_name))
            config[name] = {}

        # do the work!
        f(config[name], module, new_name)

        # recurse into submodules (if defined)
        _walk_config(config=config[name],
                     modules=getattr(module, 'sub_modules', []),
                     f=f,
                     prefix=new_name + '.',
                     required=required)
    return config

def collect_add_argparse(parser, modules):
    """Add all command-line options.

    `modules` is an iterable of
    :class:`yakonfig.configurable.Configurable` objects, or anything
    equivalently typed.  This calls
    :meth:`~yakonfig.configurable.Configurable.add_arguments` (if
    present) on all of them to set the global command-line arguments.

    :param argparse.ArgumentParser parser: argparse parser
    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.configurable.Configurable`

    """
    def work_in(config, module, name):
        f = getattr(module, 'add_arguments', None)
        if f is not None:
            f(parser)
    # this is *really handy* so we'll use it -- but it builds up a
    # partial config tree that we'll 100% ignore
    _walk_config(dict(), modules, work_in, required=False)
    return parser

def assemble_default_config(modules):

    """Build the default configuration from a set of modules.

    `modules` is an iterable of
    :class:`yakonfig.configurable.Configurable` objects, or anything
    equivalently typed.  This produces the default configuration from
    that list of modules.

    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.configurable.Configurable`
    :return: configuration dictionary

    """
    def work_in(config, module, name):
        local_config = dict(getattr(module, 'default_config', {}))
        config.update(local_config)
    return _walk_config(dict(), modules, work_in, required=False)

def fill_in_arguments(config, modules, args):
    """Fill in configuration fields from command-line arguments.

    `config` is a dictionary holding the initial configuration,
    probably the result of :func:`assemble_default_config`.  It reads
    through `modules`, and for each, fills in any configuration values
    that are provided in `args`.

    `config` is modified in place.  `args` may be either a dictionary
    or an object (as the result of :mod:`argparse`).

    :param dict config: configuration tree to update
    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.configurable.Configurable`
    :param args: command-line objects
    :paramtype args: dict or object
    :return: config

    """
    def work_in(config, module, name):
        rkeys = getattr(module, 'runtime_keys', {})
        for (attr, cname) in rkeys.iteritems():
            v = args.get(attr, None)
            if v is not None:
                config[cname] = v
    if not isinstance(args, collections.Mapping):
        args = vars(args)
    return _walk_config(config, modules, work_in)

def normalize_config(config, modules):
    """Normalize configuration values in the entire tree.

    `config` is a dictionary holding the almost-final configuration.
    Each module's
    :method:`yakonfig.configurable.Configurable.normalize_config`
    function is called to make changes such as pushing configuration
    into sub-module configuration blocks and making file paths
    absolute.

    :param dict config: configuration tree to update
    :param modules: modules or Configurable instances to use
    :type modules: iterable of :class:`~yakonfig.configurable.Configurable`

    """
    def work_in(config, module, name):
        f = getattr(module, 'normalize_config', None)
        if f: f(config)
    return _walk_config(config, modules, work_in)
