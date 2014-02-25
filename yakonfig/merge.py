"""Configuration merging and diffing.

Purpose
=======

This module provides common functions to add one configuration block
to another (`overlay_config()`), and to do the reverse (`diff_config()`).

-----

This software is released under an MIT/X11 open source license.

Copyright 2014 Diffeo, Inc.

"""
from __future__ import absolute_import
import collections

def overlay_config(c0, c1):
    """Overlay one configuration over another.

    This overlays `c1` on top of `c0` as follows:

    * If either isn't a dictionary, returns `c1`.
    * Any key in `c0` not present in `c1` is present in the result with
      its original value.
    * Any key in `c1` with value None is not present in the result.
    * Any key in `c1` not present in `c0` and not None is present in
      the result with its new value.
    * Any key in both `c1` and `c0` with a non-None value is
      recursively overlaid.

    :param dict c0: original configuration
    :param dict c1: overlay configuration
    :return: new overlaid configuration
    :returntype dict:

    """
    if not isinstance(c0, collections.Mapping): return c1
    if not isinstance(c1, collections.Mapping): return c1
    result = dict()
    for k in c0.iterkeys():
        if k not in c1:
            result[k] = c0[k]
    for k,v in c1.iteritems():
        if v is not None:
            if k in c0:
                v = overlay_config(c0[k], v)
            result[k] = v
    return result

def diff_config(c0, c1):
    """Find the differences between two configurations.

    This finds a delta configuration from `c0` to `c1`, such that
    calling `overlay_config()` with `c0` and the result of this function
    yields `c1`.  This works as follows:

    * If both are identical (of any type), returns an empty dictionary.
    * If either isn't a dictionary, returns `c1`.
    * Any key in `c1` not present in `c0` is included in the output
      with its value from `c1`.
    * Any key in `c0` not present in `c1` is included in the output
      with value `None`.
    * Any keys present in both dictionaries are recursively merged.

    :param dict c0: original configuration
    :param dict c1: new configuration
    :return: overlay configuration
    :returntype dict:

    """
    if not isinstance(c0, collections.Mapping):
        if c0 == c1:
            return {}
        return c1
    if not isinstance(c1, collections.Mapping): return c1
    result = dict()
    for k in c0.iterkeys():
        if k not in c1:
            result[k] = None
    for k,v in c1.iteritems():
        if k in c0:
            merged = diff_config(c0[k], v)
            if merged != {}: result[k] = merged
        else:
            result[k] = v
    return result
