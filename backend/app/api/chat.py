"""
对话 API
支持流式输出
"""

import uuid
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: str
    sources: Optional[List[str]] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    sources: List[str] = []
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口（非流式）
    """
    from backend.app.models import get_database

    db = get_database()
    session_id = request.session_id or str(uuid.uuid4())

    # 确保会话存在
    db.create_session(session_id)

    logger.info(f"[Chat] session={session_id}, message={request.message[:50]}...")

    try:
        # 保存用户消息
        db.add_message(session_id, "user", request.message)

        # 导入工作流
        from backend.app.agents import get_workflow
        from backend.app.agents.state import AgentState

        workflow = get_workflow()

        # 构造初始状态
        initial_state: AgentState = {
            "user_message": request.message,
            "messages": [],
            "retrieved_docs": [],
            "current_agent": "",
            "agent_output": "",
            "sources": [],
            "session_id": session_id,
            "metadata": {},
        }

        # 运行工作流
        result = workflow.invoke(initial_state)

        # 提取结果
        reply = result.get("agent_output", "抱歉，处理过程中出现错误。")
        sources = result.get("sources", [])

        # 保存助手回复
        db.add_message(session_id, "assistant", reply, sources)

        return ChatResponse(
            reply=reply,
            sources=sources,
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"[Chat] 处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    对话接口（流式输出）
    """
    from backend.app.models import get_database, get_llm

    db = get_database()
    session_id = request.session_id or str(uuid.uuid4())

    # 确保会话存在
    db.create_session(session_id)

    logger.info(f"[Chat Stream] session={session_id}, message={request.message[:50]}...")

    async def generate():
        full_reply = ""
        sources = []

        try:
            # 保存用户消息
            db.add_message(session_id, "user", request.message)

            # 先获取 Agent 决策和检索结果
            from backend.app.agents import get_workflow
            from backend.app.agents.supervisor import supervisor_node
            from backend.app.agents.tutor import tutor_node, _build_context, _extract_sources
            from backend.app.agents.state import AgentState
            from backend.app.rag import get_retriever

            # 1. Supervisor 决策
            initial_state: AgentState = {
                "user_message": request.message,
                "messages": [],
                "retrieved_docs": [],
                "current_agent": "",
                "agent_output": "",
                "sources": [],
                "session_id": session_id,
                "metadata": {},
            }

            state_after_supervisor = supervisor_node(initial_state)
            agent_name = state_after_supervisor.get("current_agent", "tutor_agent")

            # 发送 Agent 决策信息
            yield f"data: {json.dumps({'type': 'agent', 'agent': agent_name})}\n\n"

            # 2. 如果是 tutor_agent，先检索文档
            if agent_name == "tutor_agent":
                retriever = get_retriever()
                retrieved_docs = retriever.retrieve(request.message, top_k=5)
                context = _build_context(retrieved_docs)
                sources = _extract_sources(retrieved_docs)

                # 发送检索状态
                yield f"data: {json.dumps({'type': 'retrieval', 'count': len(retrieved_docs)})}\n\n"

                # 构造 prompt
                from langchain_core.messages import HumanMessage, SystemMessage
                from backend.app.agents.tutor import TUTOR_PROMPT

                prompt = f"""参考资料：
{context}

用户问题：{request.message}

请基于参考资料回答用户的问题。"""

                messages = [
                    SystemMessage(content=TUTOR_PROMPT),
                    HumanMessage(content=prompt),
                ]
            else:
                # 其他 Agent 使用直接回答
                from backend.app.agents.direct import DIRECT_PROMPT
                from langchain_core.messages import HumanMessage, SystemMessage

                messages = [
                    SystemMessage(content=DIRECT_PROMPT),
                    HumanMessage(content=request.message),
                ]

            # 3. 流式调用 LLM
            llm = get_llm()

            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_reply += chunk.content
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

            # 4. 发送完成信息
            yield f"data: {json.dumps({'type': 'done', 'sources': sources})}\n\n"

            # 5. 保存到数据库
            db.add_message(session_id, "assistant", full_reply, sources)

        except Exception as e:
            logger.error(f"[Chat Stream] 处理失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """获取对话历史"""
    from backend.app.models import get_database

    db = get_database()
    messages = db.get_messages(session_id)

    return {
        "session_id": session_id,
        "messages": messages,
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清空对话历史"""
    from backend.app.models import get_database

    db = get_database()
    count = db.clear_messages(session_id)

    return {"status": "cleared", "session_id": session_id, "deleted_count": count}


@router.get("/sessions")
async def list_sessions():
    """获取所有会话列表"""
    from backend.app.models import get_database
    from datetime import datetime, timedelta

    db = get_database()
    sessions = db.get_sessions()

    # 为每个会话添加标题（第一条用户消息）和时间分组
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    for session in sessions:
        messages = db.get_messages(session["id"], limit=1)
        first_user_msg = next((m for m in messages if m["role"] == "user"), None)
        session["title"] = first_user_msg["content"][:30] if first_user_msg else "新对话"

        # 时间分组
        try:
            # 处理 "YYYY-MM-DD HH:MM:SS" 格式
            updated_str = session["updated_at"]
            updated = datetime.strptime(updated_str, "%Y-%m-%d %H:%M:%S")
            session_date = updated.date()
        except Exception:
            session_date = today

        if session_date == today:
            session["time_group"] = "今天"
        elif session_date == yesterday:
            session["time_group"] = "昨天"
        elif session_date > week_ago:
            days_diff = (today - session_date).days
            session["time_group"] = f"{days_diff}天内"
        else:
            session["time_group"] = session["updated_at"][:10]  # YYYY-MM-DD

    return {"sessions": sessions}
