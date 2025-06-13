import jsonpickle
import time
from copy import deepcopy
from typing import Any, Dict, Optional

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


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
        job_info["err_msg"] = tool_response.content[0].text
    else:
        job_info["result"] = jsonpickle.loads(tool_response.content[0].text)
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
