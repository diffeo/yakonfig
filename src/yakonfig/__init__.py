#!/usr/bin/env python

'''
This software is released under an MIT/X11 open source license.

Copyright 2013-2014 Diffeo, Inc.


Loads a yaml file (with extensions) and makes it available globally to a Python application.


YAML extensions:

key: !include path

Loads a yaml file at path and inserts it as the value associated with key.


key: !runtime [rkey]

From some runtime set of options (via argparse or a dict of options) insert that value under key. If 'rkey' is specified then do dict or property access by that name and use that value instead of the whole.


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


