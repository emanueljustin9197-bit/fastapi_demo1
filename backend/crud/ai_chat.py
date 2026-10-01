import json
from typing import Annotated, TypedDict

from fastapi import HTTPException
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages

from crud import analysis as analysis_crud
from crud.ai import get_ai_model, _content_to_text, _read_json_object


class AnalysisChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    data_context: str


async def answer_question(state: AnalysisChatState):
    system_message = SystemMessage(content=f"""
你是问卷数据分析助手，只能依据下面提供的真实数据回答。
数据不足时必须明确说明，不得编造数字。
必须返回 JSON：
{{
  "answer": "回答内容",
  "evidence": [
    {{
      "sourceType": "overview、trend 或 question",
      "sourceId": "字段名、日期或题目ID",
      "text": "引用的具体统计数据"
    }}
  ]
}}

当前问卷数据：
{state["data_context"]}
""")
    try:
        response = await get_ai_model().ainvoke(
            [system_message, *state["messages"]]
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="DeepSeek 调用失败，请检查 API Key、模型名和网络",
        ) from error
    return {"messages": [response]}


builder = StateGraph(AnalysisChatState)
builder.add_node("answer", answer_question)
builder.add_edge(START, "answer")

chat_memory = InMemorySaver()
chat_graph = builder.compile(checkpointer=chat_memory)


def build_thread_id(user_id, questionnaire_id, conversation_id):
    return f"analysis:{user_id}:{questionnaire_id}:{conversation_id}"


async def clear_analysis_chat(user_id, questionnaire_id, conversation_id):
    thread_id = build_thread_id(
        user_id,
        questionnaire_id,
        conversation_id,
    )
    await chat_memory.adelete_thread(thread_id)


async def chat_with_analysis(db, payload, user_id: int):
    overview = await analysis_crud.get_overview_by_questionnaireid(
        db, payload.questionnaireId, user_id
    )
    if overview is None:
        return None

    days = 7 if payload.range == "7d" else 30
    trend = await analysis_crud.get_response_trend_by_days(
        db, payload.questionnaireId, user_id, days
    )
    questions = await analysis_crud.get_total_result_by_id(
        db, payload.questionnaireId, user_id
    )

    context = json.dumps({
        "overview": overview,
        "trend": trend,
        "questions": questions,
    }, ensure_ascii=False, default=str)

    thread_id = (
        f"analysis:{user_id}:"
        f"{payload.questionnaireId}:{payload.conversationId}"
    )

    result = await chat_graph.ainvoke(
        {
            "messages": [HumanMessage(content=payload.message)],
            "data_context": context,
        },
        {"configurable": {"thread_id": thread_id}},
    )

    raw = _content_to_text(result["messages"][-1].content)
    data = _read_json_object(raw)

    return {
        "conversationId": payload.conversationId,
        "answer": str(data.get("answer", "")).strip(),
        "evidence": data.get("evidence", []),
    }
