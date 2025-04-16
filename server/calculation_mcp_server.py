import inspect
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.func_metadata import _get_typed_signature

from .executor import executor_dict
from .storage import storage_dict
from .utils import get_metadata

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


def query_job_status(job_id: str, executor: Optional[dict] = None
                     ) -> Literal["Running", "Succeeded", "Failed"]:
    """
    Query status of a calculation job
    Args:
        job_id (str): The ID of the calculation job
    Returns:
        status (str): One of "Running", "Succeeded" or "Failed"
    """
    executor = init_executor(executor)
    status = executor.query_status(job_id)
    logger.info("Job %s status is %s" % (job_id, status))
    return status


def terminate_job(job_id: str, executor: Optional[dict] = None):
    """
    Terminate a calculation job
    Args:
        job_id (str): The ID of the calculation job
    """
    executor = init_executor(executor)
    executor.terminate(job_id)
    logger.info("Job %s is terminated" % job_id)


def get_job_results(job_id: str, executor: Optional[dict] = None,
                    storage: Optional[dict] = None) -> dict:
    """
    Get results of a calculation job
    Args:
        job_id (str): The ID of the calculation job
    Returns:
        results (dict): results of the calculation job
    """
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


class CalculationMCPServer:
    def __init__(self, *args, **kwargs):
        self.mcp = FastMCP(*args, **kwargs)

    def tool(self):
        def decorator(fn: Callable) -> Callable:
            def submit_job(executor: Optional[dict] = None,
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

            self.mcp.add_tool(fn)
            # replace the function of the tool
            tool = self.mcp._tool_manager.get_tool(fn.__name__)
            tool.fn = submit_job
            # patch the metadata of the tool
            # combine parameters
            parameters = []
            for param in _get_typed_signature(fn).parameters.values():
                if param.annotation is Path:
                    parameters.append(inspect.Parameter(
                        name=param.name, default=param.default,
                        annotation=str, kind=param.kind))
                elif param.annotation is Optional[Path]:
                    parameters.append(inspect.Parameter(
                        name=param.name, default=param.default,
                        annotation=Optional[str], kind=param.kind))
                else:
                    parameters.append(param)
            for param in _get_typed_signature(submit_job).parameters.values():
                if param.name != "kwargs":
                    parameters.append(param)
            func_arg_metadata = get_metadata(
                fn.__name__,
                parameters=parameters,
                skip_names=[tool.context_kwarg]
                if tool.context_kwarg is not None else [],
                globalns=getattr(fn, "__globals__", {})
            )
            parameters = func_arg_metadata.arg_model.model_json_schema()
            tool.fn_metadata = func_arg_metadata
            tool.parameters = parameters
            self.mcp.add_tool(query_job_status)
            self.mcp.add_tool(terminate_job)
            self.mcp.add_tool(get_job_results)
            return fn
        return decorator

    def run(self, **kwargs):
        self.mcp.run(**kwargs)
