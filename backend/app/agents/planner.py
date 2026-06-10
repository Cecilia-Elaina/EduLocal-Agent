"""
Planner Agent
制定学习计划和学习路径
"""

from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm, get_database


# Planner Agent 系统提示
PLANNER_PROMPT = """你是一个专业的学习规划师。根据学生的水平、目标和现有知识，制定个性化的学习计划。

请遵循以下原则：
1. 计划要具体可执行，包含明确的学习步骤
2. 根据学生当前水平调整难度梯度
3. 合理安排学习时间，避免过载
4. 包含复习和自测环节
5. 提供推荐的学习资源

输出格式要求：
- 使用清晰的标题和步骤
- 每个步骤包含：学习内容、预计时间、学习方法、检验标准
- 提供整体时间规划
- 给出鼓励和建议

请用中文回答，语气积极鼓励。"""


def planner_node(state: AgentState) -> AgentState:
    """
    Planner Agent 节点：制定学习计划

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    session_id = state.get("session_id")
    logger.info(f"[Planner] 制定学习计划: {user_message[:50]}...")

    # 获取学生历史数据
    db = get_database()
    records = db.get_learning_records(limit=50)
    session_messages = db.get_messages(session_id, limit=20) if session_id else []

    # 构造学生画像
    student_profile = _build_student_profile(records, session_messages)

    # 调用 LLM 制定计划
    llm = get_llm()

    prompt = f"""请根据以下学生画像，为其制定学习计划：

## 学生画像
{student_profile}

## 学习目标
{user_message}

请制定一份详细的学习计划。"""

    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    plan = response.content

    logger.info("[Planner] 学习计划制定完成")

    return {
        "agent_output": plan,
        "sources": [],
    }


def _build_student_profile(records: list, messages: list) -> str:
    """构建学生画像"""
    profile_parts = []

    # 学习统计
    if records:
        total = len(records)
        correct = sum(1 for r in records if r.get("is_correct") == 1)
        wrong = sum(1 for r in records if r.get("is_correct") == 0)

        profile_parts.append(f"### 学习数据统计")
        profile_parts.append(f"- 总练习数: {total}")
        profile_parts.append(f"- 正确数: {correct}")
        profile_parts.append(f"- 错误数: {wrong}")
        if total > 0:
            accuracy = correct / total * 100
            profile_parts.append(f"- 正确率: {accuracy:.1f}%")

        # 知识点掌握情况
        from collections import Counter
        correct_points = []
        wrong_points = []

        for r in records:
            kp = r.get("knowledge_points")
            if kp and isinstance(kp, list):
                if r.get("is_correct") == 1:
                    correct_points.extend(kp)
                elif r.get("is_correct") == 0:
                    wrong_points.extend(kp)

        if correct_points:
            profile_parts.append("\n### 已掌握的知识点")
            for point, count in Counter(correct_points).most_common(5):
                profile_parts.append(f"- {point}")

        if wrong_points:
            profile_parts.append("\n### 需要加强的知识点")
            for point, count in Counter(wrong_points).most_common(5):
                profile_parts.append(f"- {point}")

    # 最近的学习内容
    if messages:
        profile_parts.append("\n### 最近的学习内容")
        for msg in messages[-6:]:
            role = "学生" if msg["role"] == "user" else "助理"
            profile_parts.append(f"- {role}: {msg['content'][:80]}...")

    if not profile_parts:
        return "暂无学生数据。请根据用户描述的目标制定通用学习计划。"

    return "\n".join(profile_parts)
