#
# Copyright 2014-15 the original author or authors
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
import os

try:
    import urllib2 as urllib
except ImportError:
    from urllib import request as urllib

from cabalgata.silla.util import disk

from cabalgata.zookeeper import util


def test_collect_zookeeper_url():
    url = util.collect_zookeeper_url()

    assert urllib.urlopen(url)


def test_collect_zookeeper_versions():
    versions = util.collect_zookeeper_versions()

    assert versions


def test_download_zookeeper():
    with disk.temp_directory() as temp_dir:
        try:
            util.download_zookeeper('0.0.0', temp_dir)
            assert False, '0.0.0 should not exist'
        except ValueError:
            pass

    with disk.temp_directory() as temp_dir:
        downloaded_file = util.download_zookeeper(temp_dir, util.collect_zookeeper_versions().pop())

        assert os.path.exists(downloaded_file)
        assert os.path.dirname(downloaded_file) == temp_dir
