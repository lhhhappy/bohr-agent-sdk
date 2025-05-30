from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from mcp.server.fastmcp.server import Context


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

    @abstractmethod
    async def async_run(
        self, fn: Callable, kwargs: dict, context: Context) -> TypedDict(
            'results', {'job_id': str, 'extra_info': dict, 'result': Any}):
        pass
