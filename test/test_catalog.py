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
    json = {'version': '1.2.3', 'pid': '456', 'running': False}
    c = catalog.Catalog.from_json(json)

    assert c == catalog.Catalog('1.2.3', '456')
    assert c.to_json() == json


def test_initialize():
    with disk.temp_directory() as temp_dir:
        catalog.initialize(catalog_dir=temp_dir)

        with catalog.load_catalog(temp_dir) as c:
            assert c.version
            assert version.StrictVersion(c.version)
            assert not c.running
