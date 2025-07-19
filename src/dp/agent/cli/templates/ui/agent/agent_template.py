"""
DP Agent UI 示例 Agent
这是一个简单的 Agent 模板，您可以基于此开发自己的 Agent
"""
import asyncio
from typing import AsyncIterator

from google_adk import Agent, Session, Tool, ToolResult


# 定义一个简单的工具
hello_tool = Tool(
    name="hello",
    description="向用户打招呼",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "用户的名字"}
        },
        "required": ["name"]
    }
)


class DPAgent(Agent):
    """DP Agent 示例实现"""
    
    def __init__(self):
        super().__init__(
            name="DP Agent Assistant",
            model="claude-3-5-sonnet-20241022",
            instructions="""你是一个基于 DP Agent SDK 开发的智能助手。
            
你可以：
1. 回答用户的问题
2. 执行各种任务
3. 管理文件和数据
4. 运行计算任务

请友好、专业地与用户交流。""",
            tools=[hello_tool],
        )
    
    async def on_tool_call(self, session: Session, name: str, arguments: dict) -> ToolResult:
        """处理工具调用"""
        if name == "hello":
            user_name = arguments.get("name", "朋友")
            return ToolResult(
                output=f"你好，{user_name}！很高兴认识你。我是 DP Agent Assistant，有什么可以帮助你的吗？"
            )
        
        return ToolResult(error=f"未知的工具: {name}")
    
    async def on_message(self, session: Session, message: str) -> AsyncIterator[str]:
        """处理用户消息"""
        # 这里可以添加自定义的消息处理逻辑
        # 默认情况下，消息会被发送到模型进行处理
        async for chunk in super().on_message(session, message):
            yield chunk


# 创建 Agent 实例
root_agent = DPAgent()


# 可选：添加更多自定义功能
class AdvancedDPAgent(DPAgent):
    """高级 DP Agent 示例，展示更多功能"""
    
    def __init__(self):
        super().__init__()
        # 添加更多工具
        self.tools.extend([
            Tool(
                name="calculate",
                description="执行简单的数学计算",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式"}
                    },
                    "required": ["expression"]
                }
            ),
            Tool(
                name="save_file",
                description="保存内容到文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "文件名"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["filename", "content"]
                }
            )
        ])
    
    async def on_tool_call(self, session: Session, name: str, arguments: dict) -> ToolResult:
        """处理额外的工具调用"""
        if name == "calculate":
            try:
                expression = arguments.get("expression", "")
                # 注意：在生产环境中应该使用更安全的计算方法
                result = eval(expression)
                return ToolResult(output=f"计算结果：{expression} = {result}")
            except Exception as e:
                return ToolResult(error=f"计算错误：{str(e)}")
        
        elif name == "save_file":
            try:
                filename = arguments.get("filename", "")
                content = arguments.get("content", "")
                
                # 保存到输出目录
                output_dir = session.get_file_path("output")
                file_path = output_dir / filename
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                return ToolResult(output=f"文件已保存到：{file_path}")
            except Exception as e:
                return ToolResult(error=f"保存文件失败：{str(e)}")
        
        # 调用父类处理其他工具
        return await super().on_tool_call(session, name, arguments)


# 如果需要使用高级版本，取消下面的注释
# root_agent = AdvancedDPAgent()