import os
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.modules.advisory import models
from . import schemas, prompts, tools
from app.modules.agents.skill_loader import get_skill_context

MAX_TOOL_ITERATIONS = 5

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.7,
    google_api_key=settings.GOOGLE_API_KEY,
)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=settings.GOOGLE_API_KEY,
)


def retrieve_context(query: str, company_id: str, k: int = 3) -> List[models.AdvisoryKnowledgeBase]:
    """Retrieve relevant documents using vector similarity."""
    db: Session = SessionLocal()
    try:
        query_embedding = embeddings.embed_query(query)
        results = (
            db.query(models.AdvisoryKnowledgeBase)
            .filter(models.AdvisoryKnowledgeBase.company_id == company_id)
            .order_by(models.AdvisoryKnowledgeBase.embedding.l2_distance(query_embedding))
            .limit(k)
            .all()
        )
        return results
    except Exception as e:
        print(f"Error in RAG retrieval: {e}")
        return []
    finally:
        db.close()


def _build_system_prompt(agent_id: str, context_text: str) -> str:
    persona = prompts.get_persona(agent_id)
    skill = get_skill_context(agent_id)
    return f"""{persona}{skill}

You have access to tools that read live business data for this company. Use them when the user asks
about metrics, runway, campaigns, roadmap, or customer health. Combine tool results with your expertise.

To propose changes (campaigns, roadmap, transactions), use propose_write_action — writes require human HI-C approval.

Use the following knowledge base context when relevant:
{context_text or "No additional context available."}

If you don't know something and tools don't have the data, say so clearly.
"""


async def _run_tool_loop(
    agent_id: str,
    company_id: Optional[str],
    user_message: str,
    context_text: str,
) -> tuple[str, List[str]]:
    """Run LLM with tool-calling loop. Returns (response_text, tools_used)."""
    agent_tools = tools.build_tools(company_id or "", agent_id)
    tools_used: List[str] = []

    if not agent_tools:
        chain = llm
        response = await chain.ainvoke([
            SystemMessage(content=_build_system_prompt(agent_id, context_text)),
            HumanMessage(content=user_message),
        ])
        return response.content, tools_used

    tool_map = {t.name: t for t in agent_tools}
    llm_with_tools = llm.bind_tools(agent_tools)

    messages = [
        SystemMessage(content=_build_system_prompt(agent_id, context_text)),
        HumanMessage(content=user_message),
    ]

    response_text = ""
    for _ in range(MAX_TOOL_ITERATIONS):
        response = await llm_with_tools.ainvoke(messages)
        if not getattr(response, "tool_calls", None):
            response_text = response.content or ""
            break

        messages.append(response)
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tools_used.append(tool_name)
            tool_fn = tool_map.get(tool_name)
            try:
                result = tool_fn.invoke(tool_call.get("args") or {}) if tool_fn else "Tool not found"
            except Exception as e:
                result = f"Tool error: {e}"
            messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_call["id"])
            )
    else:
        response_text = response.content or "Limite de iterações de tools atingido."

    return response_text, tools_used


async def run_agent(
    request: schemas.ChatRequest,
    user_context: dict = None,
) -> schemas.AdvisoryResponse:
    company_id = request.company_id
    if not company_id and user_context:
        company_id = user_context.get("company_id")

    agent_id = (request.agent_id or "cfo").lower()

    context_docs = []
    if company_id:
        try:
            context_docs = retrieve_context(request.user_message, str(company_id))
        except Exception:
            context_docs = []

    context_text = "\n\n".join(
        f"Source: {doc.source_title}\nContent: {doc.content}" for doc in context_docs
    )

    try:
        response_text, tools_used = await _run_tool_loop(
            agent_id=agent_id,
            company_id=company_id,
            user_message=request.user_message,
            context_text=context_text,
        )
    except Exception as e:
        response_text = f"Desculpe, ocorreu um erro ao processar sua solicitação: {e}"
        tools_used = []

    sources = [doc.source_title for doc in context_docs]
    if tools_used:
        sources.extend([f"tool:{t}" for t in tools_used])

    return schemas.AdvisoryResponse(
        response=response_text,
        session_id=request.session_id or "new_session",
        sources=sources,
        agent_id=agent_id,
        tools_used=tools_used,
    )
