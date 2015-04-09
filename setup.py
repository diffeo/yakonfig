#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from version import get_git_version

VERSION, SOURCE_LABEL = get_git_version()
PROJECT = 'yakonfig'
AUTHOR = 'Diffeo, Inc.'
AUTHOR_EMAIL = 'support@diffeo.com'
URL = 'http://github.com/diffeo/yakonfig'
DESC = 'load a configuration dictionary for a large application'


def read_file(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name), 'r') as f:
        return f.read()

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    license=read_file('LICENSE.txt'),
    long_description=read_file('README.md'),
    # source_label=SOURCE_LABEL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        # MIT/X11 license http://opensource.org/licenses/MIT
        'License :: OSI Approved :: MIT License',
    ],
    install_requires=[
        'pyyaml',
        'six',
    ],
)
