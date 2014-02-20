'''
This software is released under an MIT/X11 open source license.

Copyright 2013-2014 Diffeo, Inc.
'''
import collections
import importlib
import logging
import pdb
import os

import yaml

logger = logging.getLogger('yakonfig')

__all__ = [
    'clear_global_config',
    'set_global_config',
    'get_global_config',
    'set_runtime_args_object',
    'set_runtime_args_dict',
    'Loader',
]


_runtime_args_object = None
_runtime_args_dict = None

_config_file_path = None

_config_cache = None


def set_runtime_args_object(args):
    """Set an agrguments object, from argparse ArgumentParser.parse_args() or similar. Will be used for substituting into !runtime values in the config yaml."""
    global _runtime_args_object
    global _runtime_args_dict
    _runtime_args_object = args
    _runtime_args_dict = None


def set_runtime_args_dict(args):
    """Set a dictionary of global options. Will be used for substituting into !runtime values in the config yaml."""
    global _runtime_args_object
    global _runtime_args_dict
    if args:
        _runtime_args_dict = args
        _runtime_args_object = None


class Loader(yaml.Loader):

    def __init__(self, stream):
        ## find root path for !include relative path
        streamname = getattr(stream, 'name', None)
        if streamname:
            self._root = os.path.dirname(streamname)
        else:
            self._root = None
        super(Loader, self).__init__(stream)

    def include_func(self, node):
        '''
        call a python function to inject values into the yaml, such as
        a function that provides default yaml for loading.
        '''
        mod_name = self.construct_scalar(node)
        parts = mod_name.split('.')
        if not len(parts) >= 2:
            raise Exception('!include_func expects full.path.to.func(), not %r' % mod_name)
        func_name = parts[-1]
        mod_name = '.'.join(parts[:-1])
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name, None)
        if not func:
            raise Exception('%r not found in %r, dir(%r) = %r' % (func_name, mod_name, mod_name, dir(mod)))

        if func_name.endswith('yaml'):
            ## functions named ".*yaml$" must return YAML to which we
            ## apply this Loader
            return yaml.load(func(), Loader)
        else:
            return func()

    def include_yaml(self, node):
        '''
        load another yaml file from the path specified by node's value
        '''
        filename = self.construct_scalar(node)
        if not filename.startswith('/'):
            if self._root is None:
                raise Exception('!include_yaml %s is a relative path, but stream lacks path' % filename)
            filename = os.path.join(self._root, self.construct_scalar(node))
        with self.open(filename, 'r') as fin:
            return yaml.load(fin, Loader)

    def include_runtime(self, node):
        '''
        load another yaml file from the path specified by runtime arg
        named by node's value
        '''
        if _runtime_args_dict is None and _runtime_args_object is None:
            raise Exception('!runtime requires a prior call to set_runtime_args_dict or set_runtime_args_object')
        runtimedict = _runtime_args_dict or vars(_runtime_args_object)
        filename = runtimedict.get(node.value)
        if filename is None:
            raise Exception('%r not in runtime args: %r' % (node.value, runtimedict))
        if not filename.startswith('/'):
            if self._root is None:
                raise Exception('!include_runtime %s is a relative path, but stream lacks path' % filename)
            filename = os.path.join(self._root, self.construct_scalar(node))
        with self.open(filename, 'r') as fin:
            return yaml.load(fin, Loader)

    def open(self, *args, **kwargs):
        '''
        method that looks like the regular python builtin `open`, and
        an be replaced by tests with different behavior
        '''
        return open(*args, **kwargs)

    def runtime(self, node):
        '''
        provide !runtime values from having set_runtime_args_dict or
        set_runtime_args_object
        '''
        if _runtime_args_dict is None and _runtime_args_object is None:
            raise Exception('!runtime requires a prior call to set_runtime_args_dict or set_runtime_args_object')
        runtimedict = _runtime_args_dict or vars(_runtime_args_object)
        if (node is None) or (not node.value):
            return runtimedict  # with no specifier, return the whole thing
        return runtimedict.get(node.value)


Loader.add_constructor('!include_runtime', Loader.include_runtime)
Loader.add_constructor('!include_func', Loader.include_func)
Loader.add_constructor('!include_yaml', Loader.include_yaml)
Loader.add_constructor('!runtime', Loader.runtime)


def clear_global_config():
    global _config_cache, _config_file_path, _runtime_args_object, _runtime_args_dict
    _config_cache = None
    _runtime_args_object = None
    _runtime_args_dict = None
    _config_file_path = None


def set_global_config(path_dict_or_stream):
    """Usage: call this from main() with a file system path, stream
    object, or a dict.  Calling it repeatedly with the same path is
    safe.  Calling it with a different path or repeatedly with a
    stream or dict requires an explicit call to clear_global_config.
    """
    path = None
    mapping = None
    stream = None

    global _config_file_path
    global _config_cache

    if isinstance(path_dict_or_stream, basestring):
        path = path_dict_or_stream
        if _config_file_path and _config_file_path != path:
            raise Exception('set_global_config(%r) differs from %r, consider calling clear_global_config first' % (path, _config_file_path))
        _config_file_path = path
        stream = open(path)

    elif isinstance(path_dict_or_stream, collections.Mapping):
        mapping = path_dict_or_stream

    elif hasattr(path_dict_or_stream, 'read'):
        stream = path_dict_or_stream

    else:
        raise Exception('set_global_config(%r) instead of a path, mapping object, or stream open for reading' % path_dict_or_stream)

    if stream is not None:
        mapping = yaml.load(stream, Loader)

    if _config_cache is not None:
        logger.warn('resetting config to all new values')

    _config_cache = mapping

    # TODO: convert to frozen dict?
    return _config_cache

def get_global_config(top_level_name=None):
    global _config_cache
    if top_level_name is not None:
        if _config_cache is None:
            raise KeyError('_config_cache has not been set, so %s is not in it' % top_level_name)
        elif top_level_name not in _config_cache:
            raise KeyError('%r not in %r' % (top_level_name, _config_cache.keys()))
        else:
            return _config_cache.get(top_level_name)
    else:
        return _config_cache
