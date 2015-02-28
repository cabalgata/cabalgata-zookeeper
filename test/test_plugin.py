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

from cabalgata.silla import factories
from cabalgata.silla.util import disk


def test_plugin():
    with disk.temp_directory() as temp_dir:
        factory = factories.load_factory('zookeeper', temp_dir)

        version = factory.versions().pop()

        factory.install('test', version, {'server_id': 0,
                                          'client_port': 20001,
                                          'election_port': 20002,
                                          'leader_port': 20003})

        service = factory.load('test')

        classpath = service.classpath.split(':')
        assert classpath
        for jar in classpath:
            assert os.path.exists(jar)

        service.start()

        assert service.running

        service.stop()

        assert not service.running

        factory.uninstall('test')

        assert os.path.exists(temp_dir)
