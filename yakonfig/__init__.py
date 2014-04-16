'''Global configuration management tools.

.. This software is released under an MIT/X11 open source license.
   Copyright 2013-2014 Diffeo, Inc.

Loads a YAML file (with extensions) and makes it available globally to
a Python application.  Application code can call
:func:`yakonfig.get_global_config` to get values from the
configuration store.

In typical use, a program will declare some number of top-level
configuration modules.  These modules mimic the structure of
:class:`yakonfig.Configurable`, and are passed in directly to
:func:`yakonfig.parse_args()`.  This makes the corresponding
configuration available in the global configuration.  For example::

    # I am a_module.py
    import yakonfig

    # Configurable metadata
    config_name = 'a_module'
    default_config = { 'message': 'hello world' }
    def add_arguments(parser):
        parser.add_argument('--message')

    def main():
        parser = argparse.ArgumentParser()
        args = yakonfig.parse_args(parser, [yakonfig, a_module])
        print yakonfig.get_global_config('a_module', 'message')
    if __name__ == '__main__':
        main()

Running ``python -m a_module`` will print out "hello world"; running
``python -m a_module --message goodbye`` will inject the "goodbye"
message into the configuration, and then print it out.

Most of the useful functions and objects in the submodules are
re-exported from the top-level module.

YAML extensions
===============

``key: !include_yaml path``

Loads a yaml file at path and inserts it as the value associated with key.

``key: !runtime [rkey]`` *(deprecated)*

From some runtime set of options (via argparse or a dict of options)
insert that value under key. If 'rkey' is specified then do dict or
property access by that name and use that value instead of the
whole.  See :func:`yakonfig.set_runtime_args_object` for how
argparse results get injected.

``key: !include_func package.path.to.func`` *(deprecated)*

Calls a python function. from a fully specified name of
``package.func`` If the function name ends in "yaml" the return value
is interpreted as a yaml document body in a string and
parsed. Otherwise the return value is assumed to be a dict or other
object that can be simply assigned to they key at this point in the
yaml file.

``key: !include_runtime rkey`` *(deprecated)*

Like ``!runtime`` pulls a value from input to
:func:`yakonfig.set_runtime_args_dict`, but uses that value
as a path as in ``!include_yaml``, reading that file and parsing it
and inserting it at this point in the enclosing yaml file.

Top-level entry points
======================

.. autofunction:: parse_args
.. autofunction:: set_default_config
.. autofunction:: defaulted_config
.. autofunction:: get_global_config

Configurable modules
====================

Modules that can be configured by the user implement the
:class:`yakonfig.Configurable` interface, or more often, have their
classes and modules provide the same names.  Anything that includes a
:attr:`~yakonfig.Configurable.config_name` property can be passed into
the top-level entry points above.

.. autoclass:: Configurable
   :members:

.. autoclass:: ProxyConfigurable
   :members:

.. autoclass:: NewSubModules
   :members:

.. autofunction:: check_toplevel_config
.. autofunction:: check_subconfig

Operations on configuration
===========================

Configuration is always passed around as plain Python dictionaries.
If you can guarantee that a configuration has passed through yakonfig,
then you can generally guarantee that its default values are present
and that any defined checks have passed.

.. autofunction:: overlay_config
.. autofunction:: diff_config

Exceptions
==========

.. autoclass:: ConfigurationError
.. autoclass:: ProgrammerError

Interactive programs
====================

.. currentmodule:: yakonfig.cmd
.. autoclass:: ArgParseCmd
.. currentmodule:: yakonfig

Legacy configuration interface
==============================

Older code worked by creating a "default" YAML file populated with
``!runtime`` YAML directives.  :func:`set_runtime_args_object` would
then populate this with a :class:`argparse.Namespace` object, where
:mod:`argparse` would provide either fixed default values or
command-line arguments.  This interface is deprecated and will be
removed.

.. autofunction:: set_runtime_args_object
.. autofunction:: set_runtime_args_dict
.. autofunction:: set_global_config
.. autofunction:: clear_global_config

'''
from __future__ import absolute_import
from yakonfig.configurable import Configurable, ProxyConfigurable, \
    NewSubModules, check_subconfig
from yakonfig.exceptions import *
from yakonfig.merge import diff_config, overlay_config
from yakonfig.toplevel import parse_args, set_default_config, \
    defaulted_config, check_toplevel_config, \
    config_name, add_arguments, runtime_keys
from yakonfig.yakonfig import set_runtime_args_object, set_runtime_args_dict, \
    clear_global_config, set_global_config, get_global_config
