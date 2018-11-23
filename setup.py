#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from shutil import rmtree

from setuptools import setup

# Package meta-data.
NAME = 'image_tools'
DESCRIPTION = 'Image Tools'
URL = 'https://github.com/ezraai/image_tools'
EMAIL = 'diego@ezra.ai'
AUTHOR = 'Diego Cantor'
REQUIRES_PYTHON = '>=2.7.0'
VERSION = '1.0'

# What packages are required for this module to be executed?
REQUIRED = ['numpy', 'pynrrd', 'SimpleITK', 'itkwidgets', 'ipywidgets']
EXTRAS = {}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
about['__version__'] = VERSION


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    # If your package is a single module, use this instead of 'packages':
    packages=['image_tools'],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT'
)
