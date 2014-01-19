#!/usr/bin/env python

import fnmatch
import os
import sys
import subprocess

from setuptools import setup, find_packages
from distutils.core import Command

from version import get_git_version
VERSION, SOURCE_LABEL = get_git_version()
PROJECT = 'yakonfig'
AUTHOR = 'Diffeo, Inc.'
AUTHOR_EMAIL = 'support@diffeo.com'
URL = 'http://github.com/diffeo/yakonfig'
DESC = 'load a configuration dictionary for a large application'

def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()

def _myinstall(pkgspec):
    setup(
        script_args = ['-q', 'easy_install', '-v', pkgspec],
        script_name = 'easy_install'
    )

class PyTest(Command):
    '''run py.test'''
    description = 'runs py.test to execute all tests'
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass

    def run(self):
        if self.distribution.install_requires:
            for ir in self.distribution.install_requires:
                _myinstall(ir)
        if self.distribution.tests_require:
            for ir in self.distribution.tests_require:
                _myinstall(ir)

        # reload sys.path for any new libraries installed
        import site
        site.main()
        print sys.path
        pytest = __import__('pytest')
        if pytest.main(['-n', '8', '-vvs', 'src']):
            sys.exit(1)

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    license=read_file('LICENSE.txt'),
    long_description=read_file('README.md'),
    #source_label=SOURCE_LABEL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    cmdclass={'test': PyTest,},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',  ## MIT/X11 license http://opensource.org/licenses/MIT
    ],
    install_requires=[
        'pyyaml',
    ],
    tests_require=[
        'pytest',
        'ipdb',
        'pytest-cov',
        'pytest-xdist',
        'pytest-timeout',
        'pytest-incremental',
        'pytest-capturelog',
    ],
)
