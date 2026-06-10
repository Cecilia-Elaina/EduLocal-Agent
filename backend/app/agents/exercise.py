"""
Exercise Agent
生成习题/测验
"""

from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.app.agents.state import AgentState
from backend.app.models import get_llm


# Exercise Agent 系统提示
EXERCISE_PROMPT = """你是一个专业的教学出题专家。根据用户提供的知识点，生成高质量的练习题。

请遵循以下规则：
1. 题目类型包括：选择题、填空题、判断题、简答题
2. 题目难度分为：简单、中等、困难
3. 每道题必须附带答案和解析
4. 题目应贴近实际教学场景
5. 输出格式清晰，便于阅读

请用 JSON 格式输出，结构如下：
{
  "exercises": [
    {
      "type": "选择题|填空题|判断题|简答题",
      "difficulty": "简单|中等|困难",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", ...],  // 选择题才有
      "answer": "正确答案",
      "explanation": "解题思路和答案解析"
    }
  ]
}"""


def exercise_node(state: AgentState) -> AgentState:
    """
    Exercise Agent 节点：生成习题

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_message = state["user_message"]
    logger.info(f"[Exercise] 生成习题: {user_message[:50]}...")

    # 解析用户请求，提取知识点和难度
    knowledge_point, difficulty = _parse_request(user_message)

    # 调用 LLM 生成习题
    llm = get_llm()

    prompt = f"""请为以下知识点生成练习题：

知识点：{knowledge_point}
难度：{difficulty}
题目数量：5道

请包含不同类型的选择题、填空题、判断题和简答题。"""

    messages = [
        SystemMessage(content=EXERCISE_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    exercises_text = response.content

    # 格式化输出
    answer = _format_exercises(exercises_text, knowledge_point, difficulty)

    logger.info(f"[Exercise] 生成习题完成")

    return {
        "agent_output": answer,
        "sources": [],
    }


def _parse_request(message: str) -> tuple[str, str]:
    """解析用户请求，提取知识点和难度"""
    # 简单的关键词匹配
    difficulty = "中等"  # 默认难度

    if "简单" in message or "基础" in message:
        difficulty = "简单"
    elif "困难" in message or "挑战" in message or "进阶" in message:
        difficulty = "困难"

    # 提取知识点（去除难度关键词）
    knowledge_point = message
    for word in ["简单", "中等", "困难", "基础", "挑战", "进阶", "出题", "习题", "练习", "测验", "考试"]:
        knowledge_point = knowledge_point.replace(word, "")

    knowledge_point = knowledge_point.strip()
    if not knowledge_point:
        knowledge_point = "综合知识"

    return knowledge_point, difficulty


def _format_exercises(text: str, knowledge_point: str, difficulty: str) -> str:
    """格式化习题输出"""
    import json

    try:
        # 尝试解析 JSON
        # 找到 JSON 部分
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)

            exercises = data.get("exercises", [])

            # 格式化输出
            result = f"##  {knowledge_point} 练习题\n\n"
            result += f"**难度**: {difficulty} | **题目数量**: {len(exercises)}\n\n"
            result += "---\n\n"

            for i, ex in enumerate(exercises, 1):
                result += f"### 第 {i} 题 ({ex.get('type', '未知')})\n\n"
                result += f"{ex.get('question', '')}\n\n"

                if ex.get('options'):
                    for opt in ex['options']:
                        result += f"- {opt}\n"
                    result += "\n"

                result += f"**答案**: {ex.get('answer', '')}\n\n"
                result += f"**解析**: {ex.get('explanation', '')}\n\n"
                result += "---\n\n"

            return result

    except json.JSONDecodeError:
        pass

    # 如果解析失败，返回原始文本
    return f"##  {knowledge_point} 练习题\n\n**难度**: {difficulty}\n\n{text}"
