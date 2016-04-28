#!/usr/bin/env python
# encoding: UTF-8

from distutils.core import setup

setup(
    name = 'sqlplus_commando',
    version = 'VERSION',
    author = 'Michel Casabianca',
    author_email = 'casa@sweetohm.net',
    packages = ['sqlplus_commando'],
    url = 'http://pypi.python.org/pypi/sqlplus_commando/',
    license = 'Apache Software License',
    description = 'sqlplus_commando is an Oracle command line driver calling sqlplus',
    long_description=open('README.rst').read(),
)
