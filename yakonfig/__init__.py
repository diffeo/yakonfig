'''Global configuration management tools.

.. This software is released under an MIT/X11 open source license.
   Copyright 2013-2014 Diffeo, Inc.

.. only:: pyapi or all

    Loads a YAML file (with extensions) and makes it available
    globally to a Python application.  Application code can call
    :func:`yakonfig.get_global_config` to get values from the
    configuration store.

    In typical use, a program will declare some number of top-level
    configuration modules.  These modules mimic the structure of
    :class:`yakonfig.Configurable`, and are passed in directly to
    :func:`yakonfig.parse_args()`.  This makes the corresponding
    configuration available in the global configuration.  For
    example::

        # I am a_module.py
        import yakonfig

        # Configurable metadata
        config_name = 'a_module'
        default_config = { 'message': 'hello world' }
        def add_arguments(parser):
            parser.add_argument('--message')
        runtime_keys = { 'message': 'message' }

        def main():
            parser = argparse.ArgumentParser()
            args = yakonfig.parse_args(parser, [yakonfig, a_module])
            print yakonfig.get_global_config('a_module', 'message')
        if __name__ == '__main__':
            main()

    Running ``python -m a_module`` will print out "hello world";
    running ``python -m a_module --message goodbye`` will inject the
    "goodbye" message into the configuration, and then print it out.

    .. note:: Avoid using :meth:`argparse.ArgumentParser.set_defaults`
              in combination with :func:`yakonfig.parse_args`.  Any
              default values set this way will override values set in
              the user's configuration file.

    Most of the useful functions and objects in the submodules are
    re-exported from the top-level module.

.. only:: all

    Common command-line arguments
    =============================

    All programs based on :mod:`yakonfig` support the following
    command-line arguments.

.. only:: cliref or all

    .. program:: yakonfig

    .. option:: --config <file.yaml>, -c <file.yaml>

        Load `file.yaml` as the primary configuration file.  Options
        set in the configuration file override any default values;
        options set on the command line override values in this
        configuration file.

    .. option:: --dump-config {default|effective|full}

        Write the configuration as YAML to standard output, then stop
        immediately.  The argument indicates which configuration is
        dumped: if ``default`` then the default configuration,
        ignoring all user setup, is dumped; if ``full`` then the dump
        contains the complete configuration, including all default
        settings, settings from the configuration file, and
        command-line options; and if ``effective`` then the dump
        contains only those settings that differ from the defaults,
        producing the minimum configuration to recreate the current
        settings.

.. only:: pyapi or all

    YAML extensions
    ===============

    ``key: !include path``
      Loads a yaml file at `path` and inserts it as the value
      associated with `key`.

    Top-level entry points
    ======================

    .. autofunction:: parse_args
    .. autofunction:: set_default_config
    .. autofunction:: defaulted_config
    .. autofunction:: get_global_config
    .. autofunction:: set_global_config
    .. autofunction:: clear_global_config

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

'''
from __future__ import absolute_import
from yakonfig.configurable import Configurable, ProxyConfigurable, \
    NewSubModules, check_subconfig
from yakonfig.exceptions import ConfigurationError, ProgrammerError
from yakonfig.merge import diff_config, overlay_config
from yakonfig.toplevel import parse_args, set_default_config, \
    defaulted_config, check_toplevel_config, \
    config_name, add_arguments, runtime_keys
from yakonfig.yakonfig import clear_global_config, set_global_config, \
    get_global_config
