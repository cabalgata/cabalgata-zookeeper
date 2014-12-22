import os
import urllib

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
