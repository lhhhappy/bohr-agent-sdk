import inspect
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .executor import executor_dict
from .storage import storage_dict

logger = logging.getLogger(__name__)


def parse_uri(uri):
    scheme = urlparse(uri).scheme
    if scheme == "":
        key = uri
        scheme = "local"
    else:
        key = uri[len(scheme)+3:]
    return scheme, key


def init_storage(storage_config: Optional[dict] = None):
    if storage_config is None:
        storage_config = {"type": "local"}
    storage_config = storage_config.copy()
    storage_type = storage_config.pop("type")
    storage = storage_dict[storage_type](**storage_config)
    return storage_type, storage


def init_executor(executor_config: Optional[dict] = None):
    if executor_config is None:
        executor_config = {"type": "local"}
    executor_config = executor_config.copy()
    executor_type = executor_config.pop("type")
    return executor_dict[executor_type](**executor_config)


class CalculationMCPServer:
    def __init__(self, *args, **kwargs):
        self.mcp = FastMCP(*args, **kwargs)

    def tool(self):
        def decorator(fn: Callable) -> Callable:
            def submit_fn(executor: Optional[dict] = None,
                          storage: Optional[dict] = None, **kwargs):
                storage_type, storage = init_storage(storage)
                sig = inspect.signature(fn)
                for name, param in sig.parameters.items():
                    if param.annotation is Path or (
                        param.annotation is Optional[Path] and
                            kwargs.get(name) is not None):
                        uri = kwargs[name]
                        scheme, key = parse_uri(uri)
                        assert scheme == storage_type
                        path = storage.download(key, "inputs/%s" % name)
                        logger.info("Artifact %s downloaded to %s" % (
                            uri, path))
                        kwargs[name] = Path(path)
                executor = init_executor(executor)
                job_id = executor.submit(fn, kwargs)
                logger.info("Job submitted (ID: %s)" % job_id)
                return job_id

            def query_status_fn(job_id, executor: Optional[dict] = None):
                executor = init_executor(executor)
                status = executor.query_status(job_id)
                logger.info("Job %s status is %s" % (job_id, status))
                return status

            def terminate_fn(job_id, executor: Optional[dict] = None):
                executor = init_executor(executor)
                executor.terminate(job_id)
                logger.info("Job %s is terminated" % job_id)

            def get_results_fn(job_id, executor: Optional[dict] = None,
                               storage: Optional[dict] = None):
                storage_type, storage = init_storage(storage)
                executor = init_executor(executor)
                results = executor.get_results(job_id)
                prefix = str(uuid.uuid4())
                for name in results:
                    if isinstance(results[name], Path):
                        key = storage.upload("%s/outputs/%s" % (prefix, name),
                                             results[name])
                        uri = storage_type + "://" + key
                        logger.info("Artifact %s uploaded to %s" % (
                            results[name], uri))
                        results[name] = uri
                logger.info("Job %s results is %s" % (job_id, results))
                return results

            self.submit_fn = submit_fn
            self.query_status_fn = query_status_fn
            self.get_results_fn = get_results_fn
            return fn
        return decorator
