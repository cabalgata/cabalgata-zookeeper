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
import os

from cabalgata.silla import plugins
from cabalgata.silla.util import disk


def test_plugin():
    factory = plugins.load_plugins('zookeeper')

    version = factory.versions().pop()

    with disk.temp_directory() as temp_dir:
        factory.install(version, temp_dir)

        service = factory.load(temp_dir)

        classpath = service.classpath
        for jar in classpath:
            assert os.path.exists(jar)

        service.start()

        service.stop()

        factory.uninstall(temp_dir)

        assert os.path.exists(temp_dir)
