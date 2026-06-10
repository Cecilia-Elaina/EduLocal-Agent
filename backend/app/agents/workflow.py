"""
LangGraph 工作流定义
多 Agent 协作的核心编排逻辑
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.agents.supervisor import supervisor_node
from backend.app.agents.tutor import tutor_node
from backend.app.agents.exercise import exercise_node
from backend.app.agents.analyst import analyst_node
from backend.app.agents.planner import planner_node
from backend.app.agents.direct import direct_node


def should_continue(state: AgentState) -> Literal["tutor_agent", "exercise_agent", "analyst_agent", "planner_agent", "direct_agent", "__end__"]:
    """路由函数：根据 current_agent 决定下一个节点"""
    agent = state.get("current_agent", "direct_agent")
    logger.debug(f"[Router] 下一个 Agent: {agent}")

    # 支持的 Agent 列表
    valid_agents = {
        "tutor_agent": "tutor_agent",
        "exercise_agent": "exercise_agent",
        "analyst_agent": "analyst_agent",
        "planner_agent": "planner_agent",
        "direct_agent": "direct_agent",
    }

    if agent in valid_agents:
        return valid_agents[agent]
    else:
        logger.warning(f"[Router] Agent {agent} 暂未实现，使用 direct_agent")
        return "direct_agent"


def create_workflow() -> StateGraph:
    """
    创建 LangGraph 工作流

    工作流结构：
    User -> Supervisor -> [Tutor | Exercise | Direct] -> End

    Returns:
        编译后的工作流图
    """
    logger.info("创建 LangGraph 工作流...")

    # 创建状态图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("tutor_agent", tutor_node)
    workflow.add_node("exercise_agent", exercise_node)
    workflow.add_node("analyst_agent", analyst_node)
    workflow.add_node("planner_agent", planner_node)
    workflow.add_node("direct_agent", direct_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 添加边
    workflow.add_conditional_edges(
        "supervisor",
        should_continue,
        {
            "tutor_agent": "tutor_agent",
            "exercise_agent": "exercise_agent",
            "analyst_agent": "analyst_agent",
            "planner_agent": "planner_agent",
            "direct_agent": "direct_agent",
        }
    )

    # Agent 节点到结束
    workflow.add_edge("tutor_agent", END)
    workflow.add_edge("exercise_agent", END)
    workflow.add_edge("analyst_agent", END)
    workflow.add_edge("planner_agent", END)
    workflow.add_edge("direct_agent", END)

    # 编译
    app = workflow.compile()

    logger.info("LangGraph 工作流创建完成")
    return app


# 全局工作流实例
_workflow = None


def get_workflow():
    """获取全局工作流实例"""
    global _workflow
    if _workflow is None:
        _workflow = create_workflow()
    return _workflow
