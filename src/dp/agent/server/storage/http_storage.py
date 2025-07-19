import os
import shutil
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning

import requests

from .base_storage import BaseStorage

# 禁用 SSL 警告（当使用 verify=False 时）
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logger = logging.getLogger(__name__)

config = {
    "plugin_type": os.environ.get("HTTP_PLUGIN_TYPE"),
    "ssl_verify": os.environ.get("HTTP_SSL_VERIFY", "false").lower() == "true",
    "timeout": int(os.environ.get("HTTP_TIMEOUT", "30")),
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
        url = self.scheme + "://" + key
        
        # 创建会话并设置通用参数
        sess = requests.session()
        sess.headers.update({
            'User-Agent': 'bohr-agent-sdk/1.0'
        })
        
        # 根本解决方案：统一处理 HTTP 和 HTTPS
        # 默认不验证 SSL 证书，除非环境变量明确要求
        verify = config.get("ssl_verify", False)
        timeout = config.get("timeout", 30)
        
        logger.debug(f"Downloading from {url} (verify SSL: {verify})")
        
        try:
            response = sess.get(
                url, 
                stream=True, 
                verify=verify,  # 统一使用配置的验证策略
                timeout=timeout,
                allow_redirects=True  # 允许重定向
            )
            response.raise_for_status()
            
            # 使用二进制模式写入，支持所有类型的文件
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            logger.info(f"Successfully downloaded {url} to {path}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            raise
            
        return path

    def list(self, prefix, recursive=False):
        return [prefix]

    def copy(self, src, dst):
        raise NotImplementedError()

    def get_md5(self, key):
        raise NotImplementedError()


class HTTPSStorage(HTTPStorage):
    scheme = "https"
