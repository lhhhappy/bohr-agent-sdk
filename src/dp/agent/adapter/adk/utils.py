import jsonpickle
import time
from copy import deepcopy
from typing import Any, Dict, Optional

from google.adk.events import Event, EventActions
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


def update_session_handler(session_service, session):
    """Update session with job and artifact information after tool calling."""
    async def after_tool_handler(
        tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext,
        tool_response: dict,
    ) -> Optional[Dict]:
        results = jsonpickle.loads(tool_response.content[0].text)
        jobs = session.state.get("jobs", [])
        results["tool_name"] = tool.name
        user_args = deepcopy(args)
        user_args.pop("executor", {})
        user_args.pop("storage", {})
        results["args"] = user_args
        results["agent_name"] = tool_context.agent_name
        jobs.append(results)
        artifacts = session.state.get("artifacts", [])
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
        state_changes = {
            "jobs": jobs,
            "artifacts": artifacts,
        }
        actions_with_update = EventActions(state_delta=state_changes)
        system_event = Event(
            invocation_id="inv_login_update",
            author="system",
            actions=actions_with_update,
            timestamp=time.time()
        )
        await session_service.append_event(session, system_event)
        return None
    return after_tool_handler
