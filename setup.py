#!/usr/bin/env python

from setuptools import setup, find_packages

#from version import get_git_version
#VERSION, SOURCE_LABEL = get_git_version()
VERSION = '0.0.1'
SOURCE_LABEL = 'init'
PROJECT = 'streamcorpus_pipeline'
AUTHOR = 'Diffeo, Inc.'
AUTHOR_EMAIL = 'support@diffeo.com'
DESC = 'load a configuration dictionary for a large application'

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    license='MIT/X11 license http://opensource.org/licenses/MIT',
    #long_description=read_file('README.rst'),
    source_label=SOURCE_LABEL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url='',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    #cmdclass={'test': PyTest,},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',  ## MIT/X11 license http://opensource.org/licenses/MIT
    ],
    install_requires=[
        'pyyaml',
    ],
)
