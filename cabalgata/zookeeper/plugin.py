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
from contextlib import closing
from glob import glob
import os
import shutil
import tarfile

from cabalgata.zookeeper import catalog, util


class ZookeeperFactory(object):
    definitions = ()

    @staticmethod
    def versions():
        return util.collect_zookeeper_versions()

    @classmethod
    def install(cls, version, directory, configuration=None):
        downloaded_file = util.download_zookeeper(version, directory)

        with closing(tarfile.open(downloaded_file)) as tar:
            tar.extractall(directory)

        with catalog.load_catalog(directory, rw=True) as c:
            c.version = version

    @classmethod
    def uninstall(cls, directory):
        with catalog.load_catalog(directory) as c:
            shutil.rmtree(install_path(c.version, directory))

    @classmethod
    def load(cls, directory):
        with catalog.load_catalog(directory) as c:
            version = c.version

        return Zookeeper(version, install_path(version, directory))


class Zookeeper(object):
    definitions = ()

    def __init__(self, version, directory):
        self.version = version
        self.directory = directory
        self.install_path = install_path(version, directory)

    def configure(self, configuration):
        pass

    def start(self):
        with catalog.load_catalog(self.directory, rw=True) as c:
            c.running = True

    def stop(self, timeout=None):
        with catalog.load_catalog(self.directory, rw=True) as c:
            c.running = False

    def kill(self):
        with catalog.load_catalog(self.directory, rw=True) as c:
            c.running = False

    @property
    def running(self):
        with catalog.load_catalog(self.directory) as c:
            return c.running

    @property
    def classpath(self):
        """Get the classpath necessary to run ZooKeeper."""
        jars = glob((os.path.join(self.install_path, 'zookeeper-*.jar')))
        jars.extend(glob(os.path.join(self.install_path, "lib/*.jar")))

        return ":".join(jars)


def install_path(version, directory):
    return os.path.join(directory, 'zookeeper-%s' % version)
