'''
This software is released under an MIT/X11 open source license.

Copyright 2013-2014 Diffeo, Inc.


Loads a yaml file (with extensions) and makes it available globally to a Python application.


YAML extensions:

key: !runtime [rkey]

From some runtime set of options (via argparse or a dict of options) insert that value under key. If 'rkey' is specified then do dict or property access by that name and use that value instead of the whole. [See set_runtime_args_dict(args)]


key: !include_yaml path

Loads a yaml file at path and inserts it as the value associated with key.


key: !include_func package.path.to.func

Calls a python function. from a fully specified name of package.func
If the function name ends in "yaml" the return value is interpreted as a yaml document body in a string and parsed. Otherwise the return value is assumed to be a dict or other object that can be simply assigned to they key at this point in the yaml file.


key: !include_runtime rkey

Like !runtime pulls a value from input to set_runtime_args_dict(), but uses that value as a path as in !include_yaml, reading that file and parsing it and inserting it at this point in the enclosing yaml file.



get_global_config(path=None, stream=None)

Call this once from main() with a path or stream of config yaml to parse.
Call this throughout the application without any arguments to get the cached global config dictionary.


set_runtime_args_object(args)

Set an object to reference in !runtime directives in the config yaml.
e.g. ap = argparse.ArgumentParser()
ap.add_argument('--foo')
set_runtime_args_object(ap.parse_args())


set_runtime_args_dict(args)

Set a dictionary to be reference by !runtime directives in the config yaml.
'''
from __future__ import absolute_import
from yakonfig.yakonfig import *


