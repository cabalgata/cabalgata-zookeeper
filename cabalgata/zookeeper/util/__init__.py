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
import json
import logging
import os
import re

try:
    import urllib2 as urllib
except ImportError:
    from urllib import request as urllib

import bs4


ASF_MIRROR_URL = 'http://www.apache.org/dyn/closer.cgi/zookeeper/?asjson=true'

log = logging.getLogger(__name__)

REGEX = re.compile(r'^zookeeper\-(.*)/$')


def collect_zookeeper_url():
    try:
        data = json.load(urllib.urlopen(ASF_MIRROR_URL))
    except Exception:
        log.error('Unable to download %s', ASF_MIRROR_URL)
        raise

    return data['preferred'] + '/zookeeper'


def collect_zookeeper_versions():
    zookeeper_url = collect_zookeeper_url()
    try:
        soup = bs4.BeautifulSoup(urllib.urlopen(zookeeper_url))
    except Exception:
        log.error('Unable to download %s', zookeeper_url)
        raise

    versions = set()
    for link in soup.find_all('a'):
        href = link.get('href')
        match = REGEX.match(href)
        if match:
            versions.add(match.groups(0)[0])

    return versions


def download_zookeeper(directory, version):
    versions = collect_zookeeper_versions()
    if version not in versions:
        raise ValueError('%s not in available versions %s' % (version, ', '.join(versions)))

    file_name = 'zookeeper-%s.tar.gz' % version

    download_url = collect_zookeeper_url() + '/zookeeper-%s/%s' % (version, file_name)
    download_stream = urllib.urlopen(download_url)

    download_file = os.path.join(directory, file_name)
    with closing(open(download_file, 'wb')) as fh:
        while True:
            buf = download_stream.read(8192)
            if not buf:
                break

            fh.write(buf)

    return download_file
