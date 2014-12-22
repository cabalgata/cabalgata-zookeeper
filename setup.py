#!/usr/bin/env python
#
# Copyright 2014 the original author or authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from io import open
import os
import subprocess
import sys

from setuptools import setup, Command

from cabalgata.zookeeper import VERSION


class Doc(Command):
    description = 'generate or test documentation'
    user_options = [('test', 't', 'run doctests instead of generating documentation')]
    boolean_options = ['test']

    def initialize_options(self):
        self.test = False

    def finalize_options(self):
        pass

    def run(self):
        if self.test:
            path = 'docs/build/doctest'
            mode = 'doctest'
        else:
            path = 'docs/build/%s' % VERSION
            mode = 'html'

        try:
            os.makedirs(path)
        except OSError:
            pass

        status = subprocess.call(['sphinx-build', '-E', '-b', mode, '-d', 'docs/build/doctrees', 'docs/source', path])

        if status:
            raise RuntimeError('documentation step "%s" failed' % (mode,))

        sys.stdout.write('\nDocumentation step "%s" performed, results here:\n'
                         '   %s/\n' % (mode, path))


setup(
    name='cabalgata-zookeeper',
    version=VERSION,
    url='http://github.com/cabalgata/cabalgata-zookeeper/',
    license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    author='Alan D. Cabrera',
    author_email='adc@toolazydogs.com',
    description='A simple wrapper for installing and starting zookeeper services.',
    # don't ever depend on refcounting to close files anywhere else
    long_description=open('README.rst', encoding='utf-8').read(),

    packages=['cabalgata',
              'cabalgata/zookeeper',
              'cabalgata/zookeeper/util'],

    zip_safe=False,
    platforms='any',

    tests_require=['tox'],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'doc': Doc},

    entry_points='''
        [cabalgata.factories]
        zookeeper=cabalgata.zookeeper.plugin:ZookeeperFactory
    '''
)
