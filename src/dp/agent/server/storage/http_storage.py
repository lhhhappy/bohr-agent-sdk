import os
import shutil

import requests

from .base_storage import BaseStorage


class HTTPStorage(BaseStorage):
    scheme = "http"

    def __init__(self):
        pass

    def _upload(self, key, path):
        raise NotImplementedError()

    def _download(self, key, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sess = requests.session()
        url = self.scheme + "://" + key
        with sess.get(url, stream=True, verify=False) as req:
            req.raise_for_status()
            with open(path, 'w') as f:
                shutil.copyfileobj(req.raw, f.buffer)
        return path

    def list(self, prefix, recursive=False):
        return [prefix]

    def copy(self, src, dst):
        raise NotImplementedError()

    def get_md5(self, key):
        raise NotImplementedError()


class HTTPSStorage(HTTPStorage):
    scheme = "https"
