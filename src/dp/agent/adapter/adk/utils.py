import json
import jsonpickle
import logging
import time
from copy import deepcopy
from typing import Any, Dict, Optional

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


def get_logger(name, level="INFO",
               format="%(asctime)s - %(levelname)s - %(message)s"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))
    handler.setFormatter(logging.Formatter(format))
    logger.addHandler(handler)
    return logger


logger = get_logger(__name__)
SCORE_THRESHOLD = 0.5


def update_session_handler(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext,
    tool_response: dict,
) -> Optional[Dict]:
    """Update session state with job and artifact information."""
    if len(tool_response.content) == 0 \
            or not hasattr(tool_response.content[0], "text"):
        return None
    job_info = getattr(tool_response.content[0], "job_info", {})
    if tool_response.isError:
        err_msg = tool_response.content[0].text
        if err_msg.startswith("Error executing tool"):
            err_msg = err_msg[err_msg.find(":")+2:]
        job_info["err_msg"] = err_msg
    else:
        job_info["result"] = jsonpickle.loads(tool_response.content[0].text)
        # do not handle long running job here
        if "job_id" in job_info["result"]:
            return None
    jobs = tool_context.state.get("jobs", [])
    job_info["tool_name"] = tool.name
    user_args = deepcopy(args)
    user_args.pop("executor", {})
    user_args.pop("storage", {})
    job_info["args"] = user_args
    job_info["agent_name"] = tool_context.agent_name
    job_info["timestamp"] = time.time()
    jobs.append(job_info)
    artifacts = tool_context.state.get("artifacts", [])
    artifacts = {art["uri"]: art for art in artifacts}
    for name, art in job_info.get("input_artifacts", {}).items():
        if art["uri"] not in artifacts:
            artifacts[art["uri"]] = {
                "type": "input",
                "name": name,
                "job_id": job_info["job_id"],
                **art,
            }
    for name, art in job_info.get("output_artifacts", {}).items():
        if art["uri"] not in artifacts:
            artifacts[art["uri"]] = {
                "type": "output",
                "name": name,
                "job_id": job_info["job_id"],
                **art,
            }
    artifacts = list(artifacts.values())
    tool_context.state["jobs"] = jobs
    tool_context.state["artifacts"] = artifacts
    return None


def search_error_in_memory_handler(toolset):
    async def func(
        tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext,
        tool_response: dict,
    ) -> Optional[Dict]:
        if tool_response.isError:
            err_msg = tool_response.content[0].text
            if err_msg.startswith("Error executing tool"):
                err_msg = err_msg[err_msg.find(":")+2:]
            tool_name = tool.name
            args = {
                "query": "The tool %s encountered an error: '%s'." % (
                    tool_name, err_msg),
                "user_id": "public",
                "filters": {
                    "tool_name": tool_name,
                },
            }
            tools = await toolset.get_tools()
            tool = next(filter(lambda t: t.name == "search_tool_error", tools))
            res = await tool.run_async(args=args, tool_context=None)
            result = json.loads(res.content[0].text)
            logger.info("Search tool error result: %s" % result)
            if result.get("results") and result[
                    "results"][0]["score"] < SCORE_THRESHOLD:
                results = {
                    "err_msg": err_msg,
                    "related_memory": result["results"][0]["memory"],
                }
                tool_response.content[0].text = json.dumps(results)
                return tool_response
        return None
    return func
