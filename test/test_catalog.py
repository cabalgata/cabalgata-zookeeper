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
from distutils import version

from cabalgata.silla.util import disk

from cabalgata.zookeeper import catalog


def test_catalog():
    json = {'version': '1.2.3', 'downloaded': [], 'installed': {}}
    c = catalog.Catalog.from_json(json)

    assert c == catalog.Catalog('1.2.3')
    assert c.to_json() == json


def test_initialize():
    with disk.temp_directory() as temp_dir:
        catalog.initialize(catalog_dir=temp_dir)

        with catalog.load_catalog(temp_dir) as c:
            assert c.version
            assert version.StrictVersion(c.version)


def test_installation():
    installation = catalog.Installation(1, '1.2.3', {'a': True}, False, 0)

    assert installation.from_json(installation.to_json()) == installation


def test_next_number():
    c = catalog.Catalog(installed={'zero': catalog.Installation(0, '1.2.3', {}, False, 0)})
    assert c.next_number() == 1

    c = catalog.Catalog(installed={'one': catalog.Installation(1, '1.2.3', {}, False, 0)})
    assert c.next_number() == 0

    c = catalog.Catalog(installed={'zero': catalog.Installation(0, '1.2.3', {}, False, 0),
                                   'three': catalog.Installation(3, '1.2.3', {}, False, 0)})
    assert c.next_number() == 1
