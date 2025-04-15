from .base_executor import BaseExecutor
from .local_executor import LocalExecutor

__all__ = ["BaseExecutor"]
executor_dict = {
    "local": LocalExecutor,
}
