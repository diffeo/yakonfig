"""Yakonfig exception types.

.. This software is released under an MIT/X11 open source license.
   Copyright 2014 Diffeo, Inc.

"""

from __future__ import absolute_import

class ConfigurationError(Exception):
    """Some part of the user-provided configuration is incomplete or
    incorrect."""
    pass

class ProgrammerError(Exception):
    """Some part of the actual code does not meet requirements."""
    pass
