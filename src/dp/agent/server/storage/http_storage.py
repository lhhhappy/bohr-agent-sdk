import os
import shutil

import requests

from .base_storage import BaseStorage

config = {
    "plugin_type": os.environ.get("HTTP_PLUGIN_TYPE"),
}


class HTTPStorage(BaseStorage):
    scheme = "http"

    def __init__(self, plugin: dict = None):
        self.plugin = None
        if plugin is None and config["plugin_type"] is not None:
            plugin = {"type": config["plugin_type"]}
        if plugin is not None:
            from . import storage_dict
            storage_type = plugin.pop("type")
            self.plugin = storage_dict[storage_type](**plugin)

    def _upload(self, key, path):
        if self.plugin is not None:
            key = self.plugin._upload(key, path)
            url = self.plugin.get_http_url(key)
            return url.split("://")[1]
        else:
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
