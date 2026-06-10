"""
Agent 状态定义
LangGraph 工作流的状态管理
"""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.documents import Document
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Agent 工作流状态"""

    # 用户输入
    user_message: str

    # 对话历史
    messages: Annotated[List[BaseMessage], add_messages]

    # RAG 检索结果
    retrieved_docs: List[Document]

    # 当前路由的 Agent
    current_agent: str

    # Agent 输出
    agent_output: str

    # 引用来源
    sources: List[str]

    # 会话 ID
    session_id: str

    # 元数据
    metadata: dict
