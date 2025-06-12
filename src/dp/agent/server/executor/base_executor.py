import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from mcp.server.fastmcp.server import Context
logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    @abstractmethod
    def submit(self, fn: Callable, kwargs: dict) -> TypedDict(
            'results', {'job_id': str, 'extra_info': dict}):
        pass

    @abstractmethod
    def query_status(self, job_id: str) -> Literal[
            "Running", "Succeeded", "Failed"]:
        pass

    @abstractmethod
    def terminate(self, job_id: str) -> None:
        pass

    @abstractmethod
    def get_results(self, job_id: str) -> dict:
        pass

    async def async_run(
        self, fn: Callable, kwargs: dict, context: Context) -> TypedDict(
            'results', {'job_id': str, 'extra_info': dict, 'result': Any}):
        info = self.submit(fn, kwargs)
        job_id = info["job_id"]
        logger.info("Job submitted (ID: %s)" % job_id)
        await context.log(level="info", message="Job submitted (ID: %s)"
                          % job_id)
        if info.get("extra_info"):
            await context.log(level="info", message=info["extra_info"])
        while True:
            status = self.query_status(job_id)
            logger.info("Job %s status is %s" % (job_id, status))
            await context.log(level="info", message="Job status: %s" % status)
            if status != "Running":
                break
            await asyncio.sleep(10)
        result = self.get_results(job_id)
        if status == "Succeeded":
            await context.log(level="info", message="Job succeeded.")
            return {**info, "result": result}
        elif status == "Failed":
            raise RuntimeError("Job failed.")
