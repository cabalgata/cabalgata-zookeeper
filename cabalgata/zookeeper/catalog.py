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


class Catalog(object):
    def __init__(self, version, pid=0, running=False):
        self.version = version
        self.pid = pid
        self.running = running

    def as_tuple(self):
        return self.version, self.pid, self.running

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __repr__(self):
        return 'Catalog(%r, %r, %r)' % self.as_tuple()

    @classmethod
    def from_json(cls, json):
        return cls(json['version'], json['pid'], json['running'])

    def to_json(self):
        return {
            'version': self.version,
            'pid': self.pid,
            'running': self.running
        }


def initialize(catalog_dir):
    with load_catalog(catalog_dir):
        pass


@contextlib.contextmanager
def load_catalog(catalog_dir, rw=False):
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
        catalog = Catalog(zookeeper.VERSION)

    yield catalog

    if rw:
        try:
            json_catalog = catalog.to_json()
            with open(catalog_file, 'w') as fp:
                json.dump(json_catalog, fp)
        except Exception:
            log.exception('Unable to write %s' % catalog_file)
            raise CorruptedCatalogError('Unable to write %s' % catalog_file)
