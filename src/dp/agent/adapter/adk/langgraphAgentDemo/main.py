"""
Google ADK Agent for UI Component Demo
This agent connects to the existing MCP server and provides AI-powered
control of the todo list component.
"""

import os
from my_langgraph_agent import MyLangGraphAgent
from dotenv import load_dotenv
from plan import app
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # 用于创建消息 Content/Parts
import warnings
# 忽略所有警告
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

print("Libraries imported.")
load_dotenv()

def create_agent():
    agent = MyLangGraphAgent(
        name="plan_agent",
       graph=app,
       instruction='You are a helpful assistant.'
    )
    return agent  

async def call_agent_async(query: str):
    """Sends a query to the agent and prints the final response."""
    session_service = InMemorySessionService()

    # Define constants for identifying the interaction context
    APP_NAME = "APP_NAME"
    USER_ID = "user_1"
    SESSION_ID = "session_001" # Using a fixed ID for simplicity
    session = await session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
    )
    runner = Runner(
    agent=create_agent(), # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
    )

    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "智能体没有产生最终响应。" # 默认值

    # 关键概念：run_async 执行智能体逻辑并产生事件。
    # 我们遍历事件以找到最终答案。
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        # 你可以取消注释下面的行以查看执行期间的*所有*事件
        print(f"  [事件] 作者：{event.author}，类型：{type(event).__name__}，最终：{event.is_final_response()}，内容：{event.content}")

        # 关键概念：is_final_response() 标记轮次的结束消息。
        if event.is_final_response():
            if event.content and event.content.parts:
                # 假设第一部分中的文本响应
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # 处理潜在错误/升级
                final_response_text = f"智能体升级：{event.error_message or '无特定消息。'}"
            # 如果需要，在这里添加更多检查（例如，特定错误代码）
            break # 找到最终响应后停止处理事件

    print(f"<<< Agent Response: {final_response_text}")
import asyncio
asyncio.run(call_agent_async('实现一个简单的计划能够完成番茄炒鸡蛋'))