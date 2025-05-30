import logging
from typing import List, Optional

from mcp import ClientSession, types
from google.adk.tools.mcp_tool import MCPTool, MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import MCPSessionManager
logger = logging.getLogger(__name__)


async def logging_handler(
    params: types.LoggingMessageNotificationParams,
) -> None:
    logger.log(getattr(logging, params.level.upper()), params.data)


class MCPSessionManagerWithLoggingCallback(MCPSessionManager):
    def __init__(
      self,
      logging_callback=None,
      **kwargs,
    ):
        super().__init__(**kwargs)
        self.logging_callback = logging_callback

    async def create_session(self) -> ClientSession:
        session = await super().create_session()
        session._logging_callback = self.logging_callback
        return session


class CalculationMCPTool(MCPTool):
    def __init__(
        self,
        executor: Optional[dict] = None,
        storage: Optional[dict] = None,
    ):
        """Calculation MCP tool
        extended from google.adk.tools.mcp_tool.MCPTool

        Args:
            executor: The executor configuration of the calculation tool.
                It is a dict where the "type" field specifies the executor
                type, and other fields are the keyword arguments of the
                corresponding executor type.
            storage: The storage configuration for storing artifacts. It is
                a dict where the "type" field specifies the storage type,
                and other fields are the keyword arguments of the
                corresponding storage type.
        """
        self.executor = executor
        self.storage = storage

    async def run_async(self, args, **kwargs):
        if "executor" not in args:
            args["executor"] = self.executor
        if "storage" not in args:
            args["storage"] = self.storage
        return await super().run_async(args=args, **kwargs)


class CalculationMCPToolset(MCPToolset):
    def __init__(
        self,
        executor: Optional[dict] = None,
        storage: Optional[dict] = None,
        executor_map: Optional[dict] = None,
        **kwargs,
    ):
        """
        Calculation MCP toolset

        Args:
            executor: The default executor configuration of the calculation
                tools. It is a dict where the "type" field specifies the
                executor type, and other fields are the keyword arguments of
                the corresponding executor type.
            storage: The storage configuration for storing artifacts. It is
                a dict where the "type" field specifies the storage type,
                and other fields are the keyword arguments of the
                corresponding storage type.
            executor_map: A dict mapping from tool name to executor
                configuration for specifying particular executor for certain
                tools
        """
        super().__init__(**kwargs)
        self._mcp_session_manager = MCPSessionManagerWithLoggingCallback(
            connection_params=self._connection_params,
            errlog=self._errlog,
            logging_callback=logging_handler,
        )
        self.executor = executor
        self.storage = storage
        self.executor_map = executor_map or {}

    async def get_tools(self, *args, **kwargs) -> List[CalculationMCPTool]:
        tools = await super().get_tools(*args, **kwargs)
        calc_tools = []
        for tool in tools:
            calc_tool = CalculationMCPTool(
                executor=self.executor_map.get(tool.name, self.executor),
                storage=self.storage)
            calc_tool.__dict__.update(tool.__dict__)
            calc_tools.append(calc_tool)
        return calc_tools
