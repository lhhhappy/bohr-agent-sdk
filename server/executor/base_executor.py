from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Literal, Union


class BaseExecutor(ABC):
    @abstractmethod
    def submit(self, fn: Callable, kwargs: dict) -> Union[int, str]:
        pass

    @abstractmethod
    def query_status(self, job_id: Union[int, str]) -> Literal[
            "Running", "Succeeded", "Failed"]:
        pass

    def terminate(self, job_id: Union[int, str]) -> None:
        pass

    def get_results(self, job_id: Union[int, str]) -> dict:
        pass
