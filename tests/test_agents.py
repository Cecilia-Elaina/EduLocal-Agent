"""
Agent 模块单元测试
"""

import pytest
from backend.app.agents.state import AgentState


class TestAgentState:
    """Agent 状态测试"""

    def test_create_state(self):
        """测试创建状态"""
        state: AgentState = {
            "user_message": "你好",
            "messages": [],
            "retrieved_docs": [],
            "current_agent": "",
            "agent_output": "",
            "sources": [],
            "session_id": "test-session",
            "metadata": {},
        }

        assert state["user_message"] == "你好"
        assert state["session_id"] == "test-session"
        assert len(state["messages"]) == 0


class TestSupervisor:
    """Supervisor Agent 测试"""

    def test_supervisor_prompt(self):
        """测试 Supervisor 提示词"""
        from backend.app.agents.supervisor import SUPERVISOR_PROMPT

        assert "tutor_agent" in SUPERVISOR_PROMPT
        assert "exercise_agent" in SUPERVISOR_PROMPT
        assert "analyst_agent" in SUPERVISOR_PROMPT
        assert "planner_agent" in SUPERVISOR_PROMPT
        assert "direct_agent" in SUPERVISOR_PROMPT


class TestTutorAgent:
    """Tutor Agent 测试"""

    def test_tutor_prompt(self):
        """测试 Tutor 提示词"""
        from backend.app.agents.tutor import TUTOR_PROMPT

        assert "参考资料" in TUTOR_PROMPT
        assert "引用" in TUTOR_PROMPT

    def test_build_context_empty(self):
        """测试空文档上下文构建"""
        from backend.app.agents.tutor import _build_context

        context = _build_context([])
        assert "暂无" in context

    def test_extract_sources_empty(self):
        """测试空引用提取"""
        from backend.app.agents.tutor import _extract_sources

        sources = _extract_sources([])
        assert sources == []


class TestExerciseAgent:
    """Exercise Agent 测试"""

    def test_exercise_prompt(self):
        """测试 Exercise 提示词"""
        from backend.app.agents.exercise import EXERCISE_PROMPT

        assert "选择题" in EXERCISE_PROMPT
        assert "填空题" in EXERCISE_PROMPT
        assert "JSON" in EXERCISE_PROMPT


class TestPlannerAgent:
    """Planner Agent 测试"""

    def test_planner_prompt(self):
        """测试 Planner 提示词"""
        from backend.app.agents.planner import PLANNER_PROMPT

        assert "学习计划" in PLANNER_PROMPT
        assert "学习" in PLANNER_PROMPT


class TestAnalystAgent:
    """Analyst Agent 测试"""

    def test_analyst_prompt(self):
        """测试 Analyst 提示词"""
        from backend.app.agents.analyst import ANALYST_PROMPT

        assert "学情" in ANALYST_PROMPT
        assert "薄弱" in ANALYST_PROMPT


class TestWorkflow:
    """工作流测试"""

    def test_workflow_creation(self):
        """测试工作流创建"""
        from backend.app.agents.workflow import create_workflow

        workflow = create_workflow()
        assert workflow is not None
