"""
Direct Agent
直接回答：处理简单问候、闲聊等不需要专业知识的问题
"""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm


# Direct Agent 系统提示
DIRECT_PROMPT = """你是一个友好的智能教学助理。

当用户只是在闲聊或问候时，你可以：
1. 礼貌地回应
2. 简单介绍你的功能
3. 引导用户提出学习相关的问题

保持回答简洁友好。"""


def direct_node(state: AgentState) -> AgentState:
    """
    Direct Agent 节点：直接回答

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    logger.info(f"[Direct] 处理直接回答: {user_message[:50]}...")

    llm = get_llm()

    messages = [
        SystemMessage(content=DIRECT_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    answer = response.content

    logger.info("[Direct] 生成回答完成")

    return {
        "agent_output": answer,
        "sources": [],
    }
