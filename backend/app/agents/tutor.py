"""
Tutor Agent
知识答疑：基于 RAG 检索教材内容，生成带引用的回答
"""

from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.documents import Document
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm
from backend.app.rag import get_retriever


# Tutor Agent 系统提示
TUTOR_PROMPT = """你是一个专业的教学助理，负责回答学生和教师的问题。

你的回答应该：
1. 基于提供的参考资料（如果有的话）
2. 准确、清晰、易于理解
3. 在回答中引用来源（如：根据教材第X页...）
4. 如果参考资料不足，可以基于通用知识回答，但要说明

请用中文回答，格式清晰，适当使用 Markdown 格式。"""


def tutor_node(state: AgentState) -> AgentState:
    """
    Tutor Agent 节点：知识答疑

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    logger.info(f"[Tutor] 处理知识问答: {user_message[:50]}...")

    # 1. 检索相关文档
    retriever = get_retriever()
    retrieved_docs = retriever.retrieve(user_message, top_k=5)

    logger.info(f"[Tutor] 检索到 {len(retrieved_docs)} 个相关文档")

    # 2. 构造上下文
    context = _build_context(retrieved_docs)

    # 3. 调用 LLM 生成回答
    llm = get_llm()

    messages = [
        SystemMessage(content=TUTOR_PROMPT),
        HumanMessage(content=f"""参考资料：
{context}

用户问题：{user_message}

请基于参考资料回答用户的问题。"""),
    ]

    response = llm.invoke(messages)
    answer = response.content

    # 4. 提取引用来源
    sources = _extract_sources(retrieved_docs)

    logger.info(f"[Tutor] 生成回答完成，引用 {len(sources)} 个来源")

    return {
        "agent_output": answer,
        "retrieved_docs": retrieved_docs,
        "sources": sources,
    }


def _build_context(docs: List[Document]) -> str:
    """构造 RAG 上下文"""
    if not docs:
        return "（暂无相关参考资料）"

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        content = doc.page_content[:500]  # 限制长度
        context_parts.append(f"[{i}] 来源: {source}\n{content}")

    return "\n\n".join(context_parts)


def _extract_sources(docs: List[Document]) -> List[str]:
    """提取引用来源"""
    sources = []
    seen = set()

    for doc in docs:
        source = doc.metadata.get("source", "")
        if source and source not in seen:
            sources.append(source)
            seen.add(source)

    return sources
