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

    def __init__(self, directory, configuration=None):
        self.directory = directory
        self.download_root = os.path.join(directory, 'download')
        self.unpack_root = os.path.join(directory, 'unpack')
        self.install_root = os.path.join(directory, 'install')
        self.configuration = configuration or {}

        if not os.path.exists(self.download_root):
            os.mkdir(self.download_root)

        if not os.path.exists(self.unpack_root):
            os.mkdir(self.unpack_root)

        if not os.path.exists(self.install_root):
            os.mkdir(self.install_root)

    @staticmethod
    def versions():
        return util.collect_zookeeper_versions()

    def install(self, name, version, configuration=None):
        with catalog.load_catalog(self.directory) as c:
            if version not in c.downloaded:
                downloaded_file = c.downloaded[version] = util.download_zookeeper(self.download_root, version)

                with closing(tarfile.open(downloaded_file)) as tar:
                    tar.extractall(self.unpack_root)

            number = c.next_number()

            os.mkdir(install_path(self.install_root, number))

            c.installed[name] = catalog.Installation(number, version, configuration, False)

    def uninstall(self, name):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed.pop(name)
            shutil.rmtree(install_path(self.install_root, installation.number))

    def load(self, name):
        with catalog.load_catalog(self.directory, rw=False) as c:
            installation = c.installed[name]

            return Zookeeper(name,
                             self.directory,
                             unpacked_path(self.unpack_root, installation.version),
                             install_path(self.install_root, installation.number))


class Zookeeper(object):
    definitions = ()

    def __init__(self, name, directory, unpacked_directory, install_directory):
        self.name = name
        self.directory = directory
        self.unpacked_directory = unpacked_directory
        self.install_directory = install_directory

    def configure(self, configuration):
        pass

    def start(self):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]
            installation.running = True

    def stop(self, timeout=None):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]
            installation.running = False

    def kill(self):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]
            installation.running = False

    @property
    def running(self):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]
            return installation.running

    @property
    def classpath(self):
        """Get the classpath necessary to run ZooKeeper."""
        jars = glob((os.path.join(self.unpacked_directory, 'zookeeper-*.jar')))
        jars.extend(glob(os.path.join(self.unpacked_directory, "lib/*.jar")))

        return ':'.join(jars)


def unpacked_path(directory, version):
    return os.path.join(directory, 'zookeeper-%s' % version)


def install_path(directory, number):
    return os.path.join(directory, str(number))
