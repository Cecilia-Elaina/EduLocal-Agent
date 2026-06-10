"""
Supervisor Agent
意图识别与任务路由
"""

from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm


# Supervisor 系统提示
SUPERVISOR_PROMPT = """你是一个智能教学助理的路由系统。根据用户的消息，决定应该调用哪个 Agent 来处理。

可选的 Agent：
1. tutor_agent - 知识答疑：回答关于教材内容、知识点解释、概念理解等问题
2. exercise_agent - 习题生成：生成练习题、测验、考试题目
3. planner_agent - 学习规划：制定学习计划、学习路径推荐
4. analyst_agent - 学情分析：分析学习情况、薄弱点诊断
5. direct_agent - 直接回答：简单问候、闲聊、不需要专业知识的问题

请分析用户的消息，返回应该调用的 Agent 名称。只返回 Agent 名称，不要包含其他内容。"""


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor 节点：意图识别与路由

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    logger.info(f"[Supervisor] 分析用户意图: {user_message[:50]}...")

    # 调用 LLM 进行意图识别
    llm = get_llm()

    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    agent_name = response.content.strip().lower()

    # 验证 Agent 名称
    valid_agents = [
        "tutor_agent",
        "exercise_agent",
        "planner_agent",
        "analyst_agent",
        "direct_agent",
    ]

    if agent_name not in valid_agents:
        logger.warning(f"[Supervisor] 未知 Agent: {agent_name}，默认使用 tutor_agent")
        agent_name = "tutor_agent"

    logger.info(f"[Supervisor] 路由到: {agent_name}")

    return {
        "current_agent": agent_name,
        "messages": [HumanMessage(content=user_message)],
    }
