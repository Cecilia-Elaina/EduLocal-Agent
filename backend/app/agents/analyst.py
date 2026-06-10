"""
Analyst Agent
学情分析：分析薄弱点，生成学习建议
"""

from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm, get_database


# Analyst Agent 系统提示
ANALYST_PROMPT = """你是一个专业的学情分析师。根据学生的历史问答记录和学习数据，分析其学习情况。

请完成以下分析：
1. 识别学生掌握较好的知识点
2. 识别学生薄弱的知识点
3. 分析学生的学习习惯和偏好
4. 给出个性化的学习建议

输出格式要求：
- 使用清晰的标题和列表
- 薄弱点要具体，说明为什么薄弱
- 建议要可操作，有具体的下一步行动

请用中文回答，语气鼓励积极。"""


def analyst_node(state: AgentState) -> AgentState:
    """
    Analyst Agent 节点：学情分析

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    session_id = state.get("session_id")
    logger.info(f"[Analyst] 分析学情: {user_message[:50]}...")

    # 获取历史学习记录
    db = get_database()
    records = db.get_learning_records(limit=30)

    # 如果指定了会话，也获取该会话的消息
    session_messages = []
    if session_id:
        session_messages = db.get_messages(session_id, limit=20)

    # 构造分析上下文
    context = _build_analysis_context(records, session_messages)

    # 调用 LLM 进行分析
    llm = get_llm()

    prompt = f"""请分析以下学习数据，给出学情报告：

{context}

用户的具体问题：{user_message}"""

    messages = [
        SystemMessage(content=ANALYST_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    analysis = response.content

    logger.info("[Analyst] 学情分析完成")

    return {
        "agent_output": analysis,
        "sources": [],
    }


def _build_analysis_context(
    records: list,
    messages: list,
) -> str:
    """构造分析上下文"""
    context_parts = []

    # 学习记录统计
    if records:
        context_parts.append("## 学习记录统计")
        context_parts.append(f"总记录数: {len(records)}")

        # 分类统计
        correct_count = sum(1 for r in records if r.get("is_correct") == 1)
        wrong_count = sum(1 for r in records if r.get("is_correct") == 0)
        context_parts.append(f"正确: {correct_count}, 错误: {wrong_count}")

        # 知识点统计
        all_points = []
        for r in records:
            kp = r.get("knowledge_points")
            if kp and isinstance(kp, list):
                all_points.extend(kp)

        if all_points:
            from collections import Counter
            point_counts = Counter(all_points)
            context_parts.append("\n涉及知识点:")
            for point, count in point_counts.most_common(10):
                context_parts.append(f"- {point}: {count}次")

        # 最近的问题
        context_parts.append("\n## 最近的问题")
        for r in records[:10]:
            correct = "✓" if r.get("is_correct") == 1 else ("✗" if r.get("is_correct") == 0 else "?")
            context_parts.append(f"[{correct}] {r['question'][:100]}")

    # 会话消息
    if messages:
        context_parts.append("\n## 最近对话")
        for msg in messages[-10:]:
            role = "学生" if msg["role"] == "user" else "助理"
            context_parts.append(f"{role}: {msg['content'][:100]}")

    if not context_parts:
        return "暂无学习记录数据。请基于用户的问题给出一般性建议。"

    return "\n".join(context_parts)
