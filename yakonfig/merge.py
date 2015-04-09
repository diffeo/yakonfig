'''Configuration merging and diffing.

.. This software is released under an MIT/X11 open source license.
   Copyright 2014-2015 Diffeo, Inc.

This module provides common functions to add one configuration block
to another (:func:`overlay_config`), and to do the reverse
(:func:`diff_config`).

.. autofunction:: overlay_config
.. autofunction:: diff_config

'''
from __future__ import absolute_import
import collections

from six import iteritems, iterkeys


def overlay_config(base, overlay):
    '''Overlay one configuration over another.

    This overlays `overlay` on top of `base` as follows:

    * If either isn't a dictionary, returns `overlay`.
    * Any key in `base` not present in `overlay` is present in the
      result with its original value.
    * Any key in `overlay` with value :const:`None` is not present in
      the result, unless it also is :const:`None` in `base`.
    * Any key in `overlay` not present in `base` and not :const:`None`
      is present in the result with its new value.
    * Any key in both `overlay` and `base` with a non-:const:`None` value
      is recursively overlaid.

    >>> overlay_config({'a': 'b'}, {'a': 'c'})
    {'a': 'c'}
    >>> overlay_config({'a': 'b'}, {'c': 'd'})
    {'a': 'b', 'c': 'd'}
    >>> overlay_config({'a': {'b': 'c'}},
    ...                {'a': {'b': 'd', 'e': 'f'}})
    {'a': {'b': 'd', 'e': 'f'}}
    >>> overlay_config({'a': 'b', 'c': 'd'}, {'a': None})
    {'c': 'd'}

    :param dict base: original configuration
    :param dict overlay: overlay configuration
    :return: new overlaid configuration
    :returntype dict:

    '''
    if not isinstance(base, collections.Mapping):
        return overlay
    if not isinstance(overlay, collections.Mapping):
        return overlay
    result = dict()
    for k in iterkeys(base):
        if k not in overlay:
            result[k] = base[k]
    for k, v in iteritems(overlay):
        if v is not None or (k in base and base[k] is None):
            if k in base:
                v = overlay_config(base[k], v)
            result[k] = v
    return result


def diff_config(base, target):
    '''Find the differences between two configurations.

    This finds a delta configuration from `base` to `target`, such that
    calling :func:`overlay_config` with `base` and the result of this
    function yields `target`.  This works as follows:

    * If both are identical (of any type), returns an empty dictionary.
    * If either isn't a dictionary, returns `target`.
    * Any key in `target` not present in `base` is included in the output
      with its value from `target`.
    * Any key in `base` not present in `target` is included in the output
      with value :const:`None`.
    * Any keys present in both dictionaries are recursively merged.

    >>> diff_config({'a': 'b'}, {})
    {'a': None}
    >>> diff_config({'a': 'b'}, {'a': 'b', 'c': 'd'})
    {'c': 'd'}

    :param dict base: original configuration
    :param dict target: new configuration
    :return: overlay configuration
    :returntype dict:

    '''
    if not isinstance(base, collections.Mapping):
        if base == target:
            return {}
        return target
    if not isinstance(target, collections.Mapping):
        return target
    result = dict()
    for k in iterkeys(base):
        if k not in target:
            result[k] = None
    for k, v in iteritems(target):
        if k in base:
            merged = diff_config(base[k], v)
            if merged != {}:
                result[k] = merged
        else:
            result[k] = v
    return result
