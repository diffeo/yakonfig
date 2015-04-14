'''Global configuration state.

.. This software is released under an MIT/X11 open source license.
   Copyright 2013-2014 Diffeo, Inc.

This maintains a global configuration dictionary.
:func:`get_global_config` will get the entire dictionary, or specific
keys from it.

'''
from __future__ import absolute_import
import collections
import contextlib
import logging
import os

from six import string_types
import yaml

logger = logging.getLogger('yakonfig')

_config_file_path = None

_config_cache = None


class Loader(yaml.Loader):
    '''YAML loader aware of yakonfig extensions.'''

    def __init__(self, stream):
        # find root path for !include relative path
        streamname = getattr(stream, 'name', None)
        if streamname:
            self._root = os.path.dirname(streamname)
        else:
            self._root = None
        super(Loader, self).__init__(stream)

    def include_yaml(self, node):
        '''
        load another yaml file from the path specified by node's value
        '''
        filename = self.construct_scalar(node)
        if not filename.startswith('/'):
            if self._root is None:
                raise Exception('!include_yaml %s is a relative path, '
                                'but stream lacks path' % filename)
            filename = os.path.join(self._root, self.construct_scalar(node))
        with self.open(filename, 'r') as fin:
            return yaml.load(fin, Loader)

    def open(self, *args, **kwargs):
        '''
        method that looks like the regular python builtin `open`, and
        an be replaced by tests with different behavior
        '''
        return open(*args, **kwargs)

Loader.add_constructor('!include_yaml', Loader.include_yaml)
Loader.add_constructor('!include', Loader.include_yaml)


def clear_global_config():
    '''Reset the global configuration to an empty state.'''
    global _config_cache, _config_file_path
    _config_cache = None
    _config_file_path = None


def set_global_config(path_dict_or_stream):
    '''Set the global configuration.

    Call this from `main()` with a file system path, stream
    object, or a dict.  Calling it repeatedly with the same path is
    safe.  Calling it with a different path or repeatedly with a
    stream or dict requires an explicit call to :func:`clear_global_config`.

    :param path_dict_or_stream: source of configuration

    '''
    path = None
    mapping = None
    stream = None

    global _config_file_path
    global _config_cache

    if isinstance(path_dict_or_stream, string_types):
        path = path_dict_or_stream
        if _config_file_path and _config_file_path != path:
            raise Exception('set_global_config(%r) differs from %r, '
                            'consider calling clear_global_config first' %
                            (path, _config_file_path))
        _config_file_path = path
        stream = open(path)

    elif isinstance(path_dict_or_stream, collections.Mapping):
        mapping = path_dict_or_stream

    elif hasattr(path_dict_or_stream, 'read'):
        stream = path_dict_or_stream

    else:
        raise Exception('set_global_config(%r) instead of a path, '
                        'mapping object, or stream open for reading' %
                        path_dict_or_stream)

    if stream is not None:
        mapping = yaml.load(stream, Loader)

    _config_cache = mapping

    # TODO: convert to frozen dict?
    return _config_cache


def get_global_config(*args):
    '''Get (a subset of) the global configuration.

    If no arguments are provided, returns the entire configuration.
    Otherwise, start with the entire configuration, and get the item
    named by the first parameter; then search that for the second
    parameter; and so on.

    :param args: configuration name path to fetch
    :return: configuration item or subtree
    :raise KeyError: if an argument is missing

    '''
    global _config_cache
    c = _config_cache
    if c is None:
        if len(args) == 0:
            args = (None,)
        raise KeyError(args[0])
    for a in args:
        c = c[a]
    return c


@contextlib.contextmanager
def _temporary_config():
    '''Temporarily replace the global configuration.

    Use this in a 'with' statement.  The inner block may freely manipulate
    the global configuration; the original global configuration is restored
    at exit.

    >>> with yakonfig.yakonfig._temporary_config():
    ...   yakonfig.yakonfig.set_global_config({'a': 'b'})
    ...   print yakonfig.yakonfig.get_global_config('a')
    b

    '''
    global _config_cache, _config_file_path
    old_cc = _config_cache
    old_cfp = _config_file_path
    clear_global_config()
    yield
    _config_cache = old_cc
    _config_file_path = old_cfp
