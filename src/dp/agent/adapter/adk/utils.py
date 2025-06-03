import jsonpickle
from copy import deepcopy
from typing import Any, Dict, Optional

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


def update_session_handler(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext,
    tool_response: dict,
) -> Optional[Dict]:
    """Update session state with job and artifact information."""
    results = jsonpickle.loads(tool_response.content[0].text)
    jobs = tool_context.state.get("jobs", [])
    results["tool_name"] = tool.name
    user_args = deepcopy(args)
    user_args.pop("executor", {})
    user_args.pop("storage", {})
    results["args"] = user_args
    results["agent_name"] = tool_context.agent_name
    jobs.append(results)
    artifacts = tool_context.state.get("artifacts", [])
    artifacts = {art["uri"]: art for art in artifacts}
    for name, art in results["input_artifacts"].items():
        if art["uri"] not in artifacts:
            artifacts[art["uri"]] = {
                "type": "input",
                "name": name,
                "job_id": results["job_id"],
                **art,
            }
    for name, art in results["output_artifacts"].items():
        if art["uri"] not in artifacts:
            artifacts[art["uri"]] = {
                "type": "output",
                "name": name,
                "job_id": results["job_id"],
                **art,
            }
    artifacts = list(artifacts.values())
    tool_context.state["jobs"] = jobs
    tool_context.state["artifacts"] = artifacts
    return None
