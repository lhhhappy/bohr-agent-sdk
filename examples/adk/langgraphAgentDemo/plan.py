import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, AIMessage,BaseMessage
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Union
from langgraph.checkpoint.memory import MemorySaver
load_dotenv()
tools = [TavilySearch(max_results=3)]

# Choose the LLM that will drive the agent
llm = ChatOpenAI(
                model=os.environ['LLM_MODEL'],
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ['OPENAI_API_BASE_URL']
            )
prompt = "You are a helpful assistant."
agent_executor = create_react_agent(llm, tools, prompt=prompt)
# res = agent_executor.invoke({"messages": [("user", "who is the winnner of the us open")]})
# print(res)


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str
    messages: Annotated[List[BaseMessage], add_messages]

class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )
class Response(BaseModel):
    """Response to user."""
    response: str
class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )


planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
                model=os.environ['LLM_MODEL'],
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ['OPENAI_API_BASE_URL']
            ).with_structured_output(Plan)
# res = planner.invoke(
#     {
#         "messages": [
#             ("user", "制定去游玩北京的规划，中文回答")
#         ]
#     }
# )
# print(res)


replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}



**If all steps have been completed and you have the final answer, respond immediately with a Response object and do not add more steps.** \
Otherwise, update the plan with only the remaining steps. Do not repeat already completed steps."""
)


replanner = replanner_prompt | ChatOpenAI(
                model=os.environ['LLM_MODEL'],
                api_key=os.environ['OPENAI_API_KEY'],
                base_url=os.environ['OPENAI_API_BASE_URL']
            ).with_structured_output(Act)

async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }
async def plan_step(state: PlanExecute):
    print("plan_step")
    print(state)
    inputstr = state["messages"][-1].content
    plan = await planner.ainvoke({"messages": [("user", inputstr)]})
    # plan = await planner.ainvoke(state["messages"][-1].content)
    return {"input":inputstr,"plan": plan.steps}

async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        # 假设这里是模型生成的最终回复
        final_response = output.action.response
        return {"response": final_response,"messages": [AIMessage(content=final_response)],}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        print("should_end")
        # print(state)
        return END
    else:
        return "agent"
workflow = StateGraph(State)
# Add the plan node
workflow.add_node("planner", plan_step)
# Add the execution step
workflow.add_node("agent", execute_step)
# Add a replan node
workflow.add_node("replan", replan_step)
workflow.add_edge(START, "planner")
# From plan we go to agent
workflow.add_edge("planner", "agent")
# From agent, we replan
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges(
    "replan",
    # Next, we pass in the function that will determine which node is called next.
    should_end,
    ["agent", END],
)


# 创建一个内存检查点存储器
checkpointer = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile(checkpointer=checkpointer)
# config = {
#     "recursion_limit": 50,
#     "configurable": {
#         "thread_id": "test-thread-1"  # 必填！
#     }
# }
# 用 HumanMessage 模拟用户提问
# inputs = {
#     "messages": [HumanMessage(content=" 实现一个简单的计划能够完成番茄炒鸡蛋?中文回答")]
# }
# async def main():
#     async for event in app.astream(inputs, config=config):
#         for k, v in event.items():
#             if k != "__end__":
#                 print(v)
# asyncio.run(main())