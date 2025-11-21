import asyncio
import json
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from ..server.utils import get_logger
logger = get_logger(__name__)


class MCPClient:
    def __init__(self, server, query_interval=4):
        self.server = server
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.query_interval = query_interval

    def _is_session_disconnected(self, session: ClientSession) -> bool:
        """Checks if a session is disconnected or closed.

        Args:
            session: The ClientSession to check.

        Returns:
            True if the session is disconnected, False otherwise.
        """
        return session._read_stream._closed or session._write_stream._closed

    async def get_session(self):
        if self.session is not None:
            # Check if the existing session is still connected
            if not self._is_session_disconnected(self.session):
                # Session is still good, return it
                return self.session
            else:
                # Session is disconnected, clean it up
                logger.info(f'Cleaning up disconnected session: {self.server}')
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.warning('Error during disconnected session cleanup: %s',
                               e)
            finally:
                self.session = None

        is_python = self.server.endswith('.py')
        is_js = self.server.endswith('.js')
        is_sse = self.server.startswith('http') and "/sse" in self.server
        is_streamablehttp = self.server.startswith('http') \
            and "/sse" not in self.server
        if not (is_python or is_js or is_sse or is_streamablehttp):
            raise ValueError(
                "Server script must be a .py or .js file or a http link")

        if is_sse:
            try:
                logger.info(f"SSE: {self.server}")
                streams = await self.exit_stack.enter_async_context(sse_client(
                    self.server))
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(*streams))
                await self.session.initialize()
                return self.session
            except Exception as e:
                logger.error(
                    f"An error occurred while connecting to the server: {e}")
                raise
        if is_streamablehttp:
            try:
                logger.info(f"StreamableHTTP: {self.server}")
                transports = await self.exit_stack.enter_async_context(
                    streamablehttp_client(self.server))
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(*transports[:2]))
                await self.session.initialize()
                return self.session
            except Exception as e:
                logger.error(
                    f"An error occurred while connecting to the server: {e}")
                raise

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[self.server],
            env=os.environ.copy(),
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params))
            stdio, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write))
            await self.session.initialize()
            return self.session
        except Exception as e:
            logger.error(
                f"An error occurred while connecting to the server: {e}")
            raise

    async def connect_to_server(self):
        await self.get_session()
        response = await self.session.list_tools()
        tools = []
        for tool in response.tools:
            if tool.name.startswith("submit_") or tool.name in [
                    "query_job_status", "get_job_results", "terminate_job"]:
                continue
            tools.append(tool)
        logger.info(
            f"Connected to server with tools:{[tool.name for tool in tools]}")
        return tools

    async def call_tool(self, tool_name: str, arguments: dict,
                        async_mode=False):
        await self.get_session()
        if not async_mode:
            result = await self.session.call_tool(tool_name, arguments)
            return result

        executor = arguments.get("executor")
        storage = arguments.get("storage")
        res = await self.call_tool("submit_" + tool_name, arguments)
        if res.isError:
            logger.error("Failed to submit %s: %s" % (
                tool_name, res.content[0].text))
            return res
        job_id = json.loads(res.content[0].text)["job_id"]
        job_info = res.content[0].job_info
        logger.info("Job submitted (ID: %s)" % job_id)
        if job_info.get("extra_info"):
            logger.info(job_info["extra_info"])

        while True:
            res = await self.call_tool("query_job_status", {
                "job_id": job_id, "executor": executor})
            if res.isError:
                logger.error(res.content[0].text)
            else:
                status = res.content[0].text
                logger.info("Job %s status is %s" % (job_id, status))
                if status != "Running":
                    break
            await asyncio.sleep(self.query_interval)

        res = await self.call_tool("get_job_results", {
            "job_id": job_id, "executor": executor, "storage": storage})
        if res.isError:
            logger.error("Job %s failed: %s" % (job_id, res.content[0].text))
        else:
            logger.info("Job %s result is %s" % (job_id, res.content))
        res.content[0].job_info = {**job_info,
                                   **getattr(res.content[0], "job_info", {})}
        return res

    async def cleanup(self):
        await self.exit_stack.aclose()

    async def __aenter__(self):
        await self.connect_to_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
