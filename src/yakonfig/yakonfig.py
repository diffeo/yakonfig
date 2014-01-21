'''
This software is released under an MIT/X11 open source license.

Copyright 2013-2014 Diffeo, Inc.
'''

import pdb
import os

import yaml


__all__ = [
    'set_global_config',
    'get_global_config',
    'set_runtime_args_object',
    'set_runtime_args_dict',
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
    _runtime_args_dict = args
    _runtime_args_object = None


class Loader(yaml.Loader):

    def __init__(self, stream):
        streamname = getattr(stream, 'name', None)
        if streamname:
            self._root = os.path.dirname(streamname)
        else:
            self._root = None
        super(Loader, self).__init__(stream)

    def include(self, node):
        if self._root:
            filename = os.path.join(self._root, self.construct_scalar(node))
        else:
            filename = self.construct_scalar(node)
        with open(filename, 'r') as fin:
            return yaml.load(fin, Loader)

    def runtime(self, node):
        #pdb.set_trace()
        runtimedict = _runtime_args_dict or vars(_runtime_args_object)
        if (node is None) or (not node.value):
            return runtimedict  # with no specifier, return the whole thing
        return runtimedict.get(node.value)


Loader.add_constructor('!include', Loader.include)
Loader.add_constructor('!runtime', Loader.runtime)


def set_global_config(path=None, stream=None):
    """Usage: call this from main() with a path or stream object.
    Calling it repeatedly with the same path is safe.
    """
    assert path or stream
    global _config_file_path
    global _config_cache
    if path is None:
        path = _config_file_path
        # TODO: os.environ[{$0}_CONFIG] ?
    else:
        if _config_file_path is None:
            _config_file_path = path
        elif _config_file_path == path:
            pass  # okay!
        else:
            raise Exception("disparate paths attempted to be used for global config path: %r %r" % (_config_file_path, path))

    if _config_cache is not None:
        assert not stream
        return _config_cache

    if path:
        assert not stream
        fin = open(path)
    else:
        assert stream
        fin = stream

    _config_cache = yaml.load(fin, Loader)
    # TODO: convert to frozen dict?
    return _config_cache

def get_global_config(top_level_name=None):
    global _config_cache
    if top_level_name is not None:
        if top_level_name not in _config_cache:
            raise KeyError('%r not in %r' % (top_level_name, _config_cache.keys()))
        else:
            return _config_cache.get(top_level_name)
    else:
        return _config_cache
