from contextlib import AsyncExitStack
from typing import List, Optional, Tuple

from google.adk.tools.mcp_tool import MCPTool, MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    retry_on_closed_resource
)
from mcp.types import ListToolsResult


class CalculationMCPTool(MCPTool):
    def __init__(
        self,
        *args,
        executor: Optional[dict] = None,
        storage: Optional[dict] = None,
        **kwargs,
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
        super().__init__(*args, **kwargs)
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
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.executor = executor
        self.storage = storage

    @classmethod
    async def from_server(
        cls,
        executor: Optional[dict] = None,
        storage: Optional[dict] = None,
        async_exit_stack: Optional[AsyncExitStack] = None,
        **kwargs,
    ) -> Tuple[List[CalculationMCPTool], AsyncExitStack]:
        async_exit_stack = async_exit_stack or AsyncExitStack()
        toolset = cls(
            executor=executor,
            storage=storage,
            exit_stack=async_exit_stack,
            **kwargs,
        )
        await async_exit_stack.enter_async_context(toolset)
        tools = await toolset.load_tools()
        return (tools, async_exit_stack)

    @retry_on_closed_resource('_initialize')
    async def load_tools(self) -> List[CalculationMCPTool]:
        tools_response: ListToolsResult = await self.session.list_tools()
        return [
            CalculationMCPTool(
                mcp_tool=tool,
                mcp_session=self.session,
                mcp_session_manager=self.session_manager,
                executor=self.executor,
                storage=self.storage,
            )
            for tool in tools_response.tools
        ]
