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
""" Catalog management functions
"""
import contextlib
import json
import logging
import os

from cabalgata import zookeeper


CATALOG_FILE = 'catalog.json'

log = logging.getLogger(__name__)


class CorruptedCatalogError(Exception):
    """Error for corrupted catalog."""


class Installation(object):
    def __init__(self, number, version, configuration, running, pid):
        self.number = number
        self.version = version
        self.configuration = configuration
        self.running = running
        self.pid = pid

    def as_tuple(self):
        return self.number, self.version, self.configuration, self.running, self.pid

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __repr__(self):
        return 'Installation(%r, %r, %r, %r, %r)' % self.as_tuple()

    def to_json(self):
        return {'number': self.number,
                'version': self.version,
                'configuration': self.configuration,
                'running': self.running,
                'pid': self.pid}

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data['number'], json_data['version'], json_data['configuration'], json_data['running'], json_data['pid'])


class Catalog(object):
    def __init__(self, version=zookeeper.VERSION, downloaded=None, installed=None):
        self.version = version
        self.downloaded = downloaded or {}
        self.installed = installed or {}

    def as_tuple(self):
        return self.version, self.downloaded, self.installed

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __repr__(self):
        return 'Catalog(%r, %r, %r)' % self.as_tuple()

    def next_number(self):
        count = 0
        while True:
            for i in self.installed.values():
                if i.number == count:
                    break
            else:
                return count

            count += 1

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data['version'],
                   set(json_data['downloaded']),
                   dict((k, Installation.from_json(v)) for k, v in json_data['installed'].items()))

    def to_json(self):
        return {
            'version': self.version,
            'downloaded': [v for v in self.downloaded],
            'installed': dict((k, v.to_json()) for k, v in self.installed.items())
        }


def initialize(catalog_dir):
    with load_catalog(catalog_dir):
        pass


@contextlib.contextmanager
def load_catalog(catalog_dir, rw=True):
    catalog_file = os.path.join(catalog_dir, CATALOG_FILE)
    if os.path.exists(catalog_file):
        try:
            with open(catalog_file) as fp:
                json_catalog = json.load(fp)
                catalog = Catalog.from_json(json_catalog)
        except Exception:
            log.exception('Unable to read %s' % catalog_file)
            raise CorruptedCatalogError('Unable to read %s' % catalog_file)
    else:
        catalog = Catalog()

    yield catalog

    if rw:
        try:
            json_catalog = catalog.to_json()
            with open(catalog_file, 'w') as fp:
                json.dump(json_catalog, fp)
        except Exception:
            log.exception('Unable to write %s' % catalog_file)
            raise CorruptedCatalogError('Unable to write %s' % catalog_file)
