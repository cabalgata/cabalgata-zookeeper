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
from contextlib import closing
from glob import glob
import os
import shutil
import tarfile
import subprocess
import signal

from cabalgata.silla.configuration import Definition
from cabalgata.silla.util import pid

from cabalgata.zookeeper import catalog, util


class ZookeeperFactory(object):
    definitions = (
        Definition('server_id', int, False),
        Definition('client_port', int, False),
        Definition('election_port', int, False),
        Definition('leader_port', int, False),
        Definition('peers', list, False, [])
    )

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

            c.installed[name] = catalog.Installation(number, version, configuration, False, 0)

            install_path = compute_install_path(self.install_root, number)
            data_path = os.path.join(install_path, 'data')
            log_path = os.path.join(install_path, 'log')

            os.mkdir(install_path)
            os.mkdir(data_path)
            os.mkdir(log_path)

    def uninstall(self, name):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed.pop(name)
            shutil.rmtree(compute_install_path(self.install_root, installation.number))

    def load(self, name):
        with catalog.load_catalog(self.directory, rw=False) as c:
            installation = c.installed[name]

            return Zookeeper(name,
                             self.directory,
                             compute_unpacked_path(self.unpack_root, installation.version),
                             compute_install_path(self.install_root, installation.number))


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
            configuration = installation.configuration

            data_path = os.path.join(self.install_directory, 'data')
            log_path = os.path.join(self.install_directory, 'log')

            config_path = os.path.join(self.install_directory, 'zoo.cfg')
            log4j_path = os.path.join(self.install_directory, 'log4j.properties')

            with open(config_path, 'w') as config:
                config.write('tickTime=2000\n')
                config.write('dataDir=%s\n' % data_path)
                config.write('maxClientCnxns=0\n')
                config.write('clientPort=%s\n' % configuration['client_port'])

                # setup a replicated setup if peers are specified
                if 'peers' in configuration and configuration['peers']:
                    config.write('initLimit=4\n')
                    config.write('syncLimit=2\n')
                    config.write('server.%s=localhost:%s:%s\n' % (
                        configuration['server_id'], configuration['leader_port'], configuration['election_port']))
                    for server_id, leader_port, election_port in configuration['peers']:
                        config.write('server.%s=localhost:%s:%s\n' % (server_id, leader_port, election_port))

            with open(log4j_path, 'w') as log4j:
                log4j.write("""
# DEFAULT: console appender only
log4j.rootLogger=INFO, ROLLINGFILE
log4j.appender.ROLLINGFILE.layout=org.apache.log4j.PatternLayout
log4j.appender.ROLLINGFILE.layout.ConversionPattern=%d{ISO8601} [myid:%X{myid}] - %-5p [%t:%C{1}@%L] - %m%n
log4j.appender.ROLLINGFILE=org.apache.log4j.RollingFileAppender
log4j.appender.ROLLINGFILE.Threshold=DEBUG
log4j.appender.ROLLINGFILE.File=""" + (log_path + os.sep + 'zookeeper.log\n'))

            process = subprocess.Popen(args=['java',
                                             '-cp', self.classpath,
                                             '-Dreadonlymode.enabled=true',
                                             '-Dzookeeper.log.dir=%s' % log_path,
                                             '-Dzookeeper.root.logger=INFO,CONSOLE',
                                             '-Dlog4j.configuration=file:%s' % log4j_path,
                                             # '-Dlog4j.debug',
                                             'org.apache.zookeeper.server.quorum.QuorumPeerMain',
                                             config_path])
            installation.pid = process.pid

    def stop(self, timeout=None):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]

            installation.running = False

            os.kill(installation.pid, signal.SIGTERM)

            pid.wait_pid(installation.pid, timeout=timeout)

    def kill(self):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]

            installation.running = False

            os.kill(installation.pid, signal.SIGKILL)

            pid.wait_pid(installation.pid)

    @property
    def running(self):
        with catalog.load_catalog(self.directory) as c:
            installation = c.installed[self.name]
            return installation.running

    @property
    def classpath(self):
        """Get the classpath necessary to run ZooKeeper."""
        jars = glob((os.path.join(self.unpacked_directory, 'zookeeper-*.jar')))
        jars.extend(glob(os.path.join(self.unpacked_directory, 'lib/*.jar')))

        return ':'.join(jars)


def compute_unpacked_path(directory, version):
    return os.path.join(directory, 'zookeeper-%s' % version)


def compute_install_path(directory, number):
    return os.path.join(directory, str(number))
