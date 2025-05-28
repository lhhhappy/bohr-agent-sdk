import asyncio
import os

from dp.agent.adapter.adk import CalculationMCPToolset, update_session_handler
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.genai import types
model = LiteLlm(model="xxx")


async def async_main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name='demo_app',
        user_id='demo_user',
        session_id="demo_session",
    )

    toolset = CalculationMCPToolset(
        connection_params=SseServerParams(
            url="http://localhost:8000/sse",
        ),
        executor={
            "type": "dispatcher",
            "machine": {
                "batch_type": "Bohrium",
                "context_type": "Bohrium",
                "remote_profile": {
                    "email": os.environ.get("BOHRIUM_USERNAME"),
                    "password": os.environ.get("BOHRIUM_PASSWORD"),
                    "program_id": int(os.environ.get("BOHRIUM_PROJECT_ID")),
                    "input_data": {
                        "image_name": "registry.dp.tech/dptech/ubuntu:22.04-py3.10",
                        "job_type": "container",
                        "platform": "ali",
                        "scass_type": "c2_m4_cpu",
                    },
                },
            },
        },
        storage={
            "type": "bohrium",
            "username": os.environ.get("BOHRIUM_USERNAME"),
            "password": os.environ.get("BOHRIUM_PASSWORD"),
            "project_id": int(os.environ.get("BOHRIUM_PROJECT_ID")),
        }
    )
    root_agent = Agent(
        model=model,
        name='root_agent',
        description='Agent to fulfill user needs using available tools.',
        instruction='Fulfill user needs using appropriate tools',
        tools=[toolset],
        after_tool_callback=update_session_handler(session_service, session),
    )

    runner = Runner(
        app_name='demo_app',
        agent=root_agent,
        session_service=session_service,
    )

    query = "Please train a Deep Potential (DP) Model using local:///Users/x.liu/training_data as the training data."
    content = types.Content(role='user', parts=[types.Part(text=query)])

    print("Running agent...")
    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=content
    )

    async for event in events_async:
        print(f"Event received: {event}")

    updated_session = await session_service.get_session(
        app_name=session.app_name,
        user_id=session.user_id,
        session_id=session.id,
    )
    print(f"State after event: {updated_session.state}")


if __name__ == "__main__":
    asyncio.run(async_main())
