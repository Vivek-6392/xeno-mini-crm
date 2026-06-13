"""
CRM Agent Graph
===============
A LangGraph ReAct agent that drives the CRM on behalf of the marketer.
The graph is compiled once at startup and reused across requests.
"""
from __future__ import annotations

import logging
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import ALL_TOOLS
from app.config import settings

logger = logging.getLogger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def _build_graph():
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,
    ).bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def call_model(state: AgentState) -> AgentState:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once — thread-safe for concurrent requests
crm_graph = _build_graph()


# ── Public helpers ────────────────────────────────────────────────────────────

def run_agent(user_message: str, history: list[dict]) -> str:
    from langchain_core.messages import AIMessage

    messages = []

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    try:
        result = crm_graph.invoke({
            "messages": messages
        })

        last = result["messages"][-1]

        return (
            last.content
            if isinstance(last.content, str)
            else str(last.content)
        )

    except Exception as e:
        logger.exception("Agent execution failed")

        return (
            f"Agent execution failed: {str(e)}"
        )
