import asyncio
import json
import logging
from typing import List, Optional

from mcp import ClientSession, types
from google.adk.tools.mcp_tool import MCPTool, MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import MCPSessionManager
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


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
        async_mode: bool = False,
        submit_tool: Optional[MCPTool] = None,
        query_tool: Optional[MCPTool] = None,
        terminate_tool: Optional[MCPTool] = None,
        results_tool: Optional[MCPTool] = None,
        query_interval: int = 10,
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
            async_mode: Submit and query until the job finishes, instead of
                waiting in single connection
            submit_tool: The tool of submitting job
            query_tool: The tool of querying job status
            terminate_tool: The tool of terminating job
            results_tool: The tool of getting job results
            query_interval: time interval of querying job status
        """
        self.executor = executor
        self.storage = storage
        self.async_mode = async_mode
        self.submit_tool = submit_tool
        self.query_tool = query_tool
        self.terminate_tool = terminate_tool
        self.results_tool = results_tool
        self.query_interval = query_interval

    async def run_async(self, args, **kwargs):
        if "executor" not in args:
            args["executor"] = self.executor
        if "storage" not in args:
            args["storage"] = self.storage
        if not self.async_mode:
            return await super().run_async(args=args, **kwargs)

        executor = args["executor"]
        storage = args["storage"]
        res = await self.submit_tool.run_async(args=args, **kwargs)
        try:
            info = json.loads(res.content[0].text)
            job_id = info["job_id"]
        except Exception as e:
            logger.error(str(e))
            logger.error(res.content[0].text)
            return res
        logger.info("Job submitted (ID: %s)" % job_id)
        if info.get("extra_info"):
            logger.info(info["extra_info"])

        while True:
            res = await self.query_tool.run_async(
                args={"job_id": job_id, "executor": executor}, **kwargs)
            status = res.content[0].text
            logger.info("Job %s status is %s" % (job_id, status))
            if status in ["Succeeded", "Failed"]:
                break
            await asyncio.sleep(self.query_interval)

        res = await self.results_tool.run_async(
            args={"job_id": job_id, "executor": executor, "storage": storage},
            **kwargs)
        if status == "Succeeded":
            results = json.loads(res.content[0].text)
            logger.info("Job %s results is %s" % (job_id, results))
            res.content[0].text = json.dumps({**info, **results})
        return res


class CalculationMCPToolset(MCPToolset):
    def __init__(
        self,
        executor: Optional[dict] = None,
        storage: Optional[dict] = None,
        executor_map: Optional[dict] = None,
        async_mode: bool = False,
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
            async_mode: Submit and query until the job finishes, instead of
                waiting in single connection
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
        self.async_mode = async_mode

    async def get_tools(self, *args, **kwargs) -> List[CalculationMCPTool]:
        tools = await super().get_tools(*args, **kwargs)
        tools = {tool.name: tool for tool in tools}
        calc_tools = []
        for tool in tools.values():
            if tool.name.startswith("submit_") or tool.name in [
                    "query_job_status", "terminate_job", "get_job_results"]:
                continue
            calc_tool = CalculationMCPTool(
                executor=self.executor_map.get(tool.name, self.executor),
                storage=self.storage,
                async_mode=self.async_mode,
                submit_tool=tools.get("submit_" + tool.name),
                query_tool=tools.get("query_job_status"),
                terminate_tool=tools.get("terminate_job"),
                results_tool=tools.get("get_job_results"),
            )
            calc_tool.__dict__.update(tool.__dict__)
            calc_tools.append(calc_tool)
        return calc_tools
