import sys

from dotenv import load_dotenv

from dp.agent.adapter.adk import CalculationMCPToolset
from google.adk.agents import LlmAgent, Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

def create_agent(ak: str, app_key: str, project_id: int) -> LlmAgent:
    """动态创建 agent，使用传入的 access_key 和 app_key"""
    # if project_id is not None:
    #     project_id = int(project_id)
    print(ak, app_key, project_id)
    # app_key = "mat-master" ## HACK

    BOHRIUM_EXECUTOR_CALC = {
        "type": "dispatcher",
        "machine": {
            "batch_type": "OpenAPI",
            "context_type": "OpenAPI",
            "remote_profile": {
                "access_key": ak,
                "app_key": app_key,  # 使用传入的 app_key
                "project_id": project_id,
                "image_address": "registry.dp.tech/dptech/dp/native/prod-19853/dpa-mcp:dev-0704",
                "job_type": "container",
                "platform": "ali",
                "machine_type": "1 * NVIDIA V100_32g"
            }
        }
    }

    BOHRIUM_EXECUTOR_TE = {
        "type": "dispatcher",
        "machine": {
            "batch_type": "OpenAPI",
            "context_type": "OpenAPI",
            "remote_profile": {
                "access_key": ak,
                "app_key": app_key,  # 使用传入的 app_key
                "project_id": project_id,
                "image_address": "registry.dp.tech/dptech/dp/native/prod-435364/agents:0.1.0",
                "job_type": "container",
                "platform": "ali",
                "machine_type": "1 * NVIDIA V100_32g"
            }
        }
    }

    HTTPS_STORAGE = {
        "type": "https",
        "plugin": {
            "type": "bohrium",
            "access_key": ak,
            "app_key": app_key,  # 使用传入的 app_key
            "project_id": project_id
        }
    }

    mcp_tools_dpa = CalculationMCPToolset(
        connection_params=SseServerParams(url="https://dpa-uuid1750659890.app-space.dplink.cc/sse?token=a0d87a7abf8d47cb92403018fd4a9468"),
        storage=HTTPS_STORAGE,
        executor=BOHRIUM_EXECUTOR_CALC,
        executor_map={
            "build_bulk_structure": None,
            "build_molecule_structure": None,
            "build_surface_slab": None,
            "build_surface_adsorbate": None
        }
    )
    mcp_tools_thermoelectric = CalculationMCPToolset(
        connection_params=SseServerParams(url="https://thermoelectricmcp000-uuid1750905361.app-space.dplink.cc/sse?token=1c1f2140a5504ebcb680f6a7fa2c03db"),
        storage=HTTPS_STORAGE,
        executor=BOHRIUM_EXECUTOR_TE
    )

    return Agent(
        model=LiteLlm(model="deepseek/deepseek-chat"),        
        # model=LiteLlm(model="azure/gpt-4o"),
        name="dpa_agent",
        description="An agent specialized in computational research using Deep Potential",
        instruction=(
            "You are an expert in materials science and computational chemistry. "
            "Help users perform Deep Potential calculations including structure optimization, molecular dynamics and property calculations. "
            "Use default parameters if the users do not mention, but let users confirm them before submission. "
            "In multi-step workflows involving file outputs, always use the URI of the previous step's file as the input for the next tool. "
            "Always verify the input parameters to users and provide clear explanations of results."
        ),
        tools=[
            mcp_tools_dpa,
            mcp_tools_thermoelectric,
        ],
    )