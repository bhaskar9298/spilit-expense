# client/langgraph_service.py

from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
mcp_server_url = os.getenv("MCP_SERVER_URL")

# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0.1
)

_mcp_client = None
_chatbot = None


# =========================================================
# STATE
# =========================================================

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    context: dict


# =========================================================
# 🔥 SCHEMA FIX (CRITICAL)
# =========================================================

def fix_schema_dict(schema: dict, tool_name: str):
    """Recursively fix schema for Gemini compatibility"""

    if not isinstance(schema, dict):
        return {"type": "string"}

    schema_type = schema.get("type")

    # Fix arrays
    if schema_type == "array":
        if "items" not in schema:
            print(f"⚠️ Fixing array items for {tool_name}")
            schema["items"] = {"type": "string"}
        else:
            schema["items"] = fix_schema_dict(schema["items"], tool_name)

    # Fix objects
    elif schema_type == "object":
        props = schema.get("properties", {})
        for key, val in props.items():
            props[key] = fix_schema_dict(val, f"{tool_name}.{key}")

    # Ensure type exists
    if "type" not in schema:
        schema["type"] = "string"

    return schema


def fix_tool_schema(tool):
    """Handle MCP dict schemas + Pydantic schemas"""

    try:
        # ✅ MCP tools (dict schema)
        if isinstance(tool.args_schema, dict):
            schema = tool.args_schema
            tool.args_schema = fix_schema_dict(schema, tool.name)
            return tool

        # ✅ Pydantic schema (fallback)
        elif hasattr(tool.args_schema, "model_json_schema"):
            original_fn = tool.args_schema.model_json_schema

            def patched():
                schema = original_fn()
                return fix_schema_dict(schema, tool.name)

            tool.args_schema.model_json_schema = patched

    except Exception as e:
        print(f"⚠️ Schema fix failed for {tool.name}: {e}")

    return tool


def validate_tool_schema(tools):
    fixed = []
    for tool in tools:
        try:
            fixed.append(fix_tool_schema(tool))
            print(f"✓ Tool validated: {tool.name}")
        except Exception as e:
            print(f"✗ Tool failed: {tool.name} -> {e}")
    return fixed


# =========================================================
# MCP INIT
# =========================================================

async def initialize_client():
    global _mcp_client, _chatbot

    if _chatbot:
        return _chatbot

    try:
        print(f"🔌 Connecting to MCP server: {mcp_server_url}")

        _mcp_client = MultiServerMCPClient({
            "expense_tracker": {
                "transport": "streamable_http",
                "url": mcp_server_url
            }
        })

        tools = await _mcp_client.get_tools()
        print(f"📦 Tools loaded: {len(tools)}")

        # 🔥 Fix schemas BEFORE binding
        tools = validate_tool_schema(tools)

        llm_with_tools = llm.bind_tools(tools)

        # =================================================
        # GRAPH
        # =================================================

        async def chat_node(state: ChatState):
            messages = state["messages"]
            user_id = state.get("user_id", "unknown")

            last = messages[-1]

            if isinstance(last, HumanMessage):
                enhanced = f"""
You are an expense tracking assistant.

User ID: {user_id}
Date: {datetime.now().strftime('%Y-%m-%d')}

User request:
"{last.content}"

Instructions:
- Always include user_id in tool calls
- Convert dates properly
- Use correct tool
"""
                messages = messages[:-1] + [HumanMessage(content=enhanced)]

            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        tool_node = ToolNode(tools)

        graph = StateGraph(ChatState)
        graph.add_node("chat_node", chat_node)
        graph.add_node("tools", tool_node)

        graph.add_edge(START, "chat_node")
        graph.add_conditional_edges("chat_node", tools_condition)
        graph.add_edge("tools", "chat_node")

        _chatbot = graph.compile()

        print("✅ Chatbot ready")
        return _chatbot

    except Exception as e:
        print(f"❌ Init failed: {e}")
        traceback.print_exc()
        raise


# =========================================================
# PROCESS MESSAGE
# =========================================================

async def process_user_message(message: str, user_id: str, context: dict = None):
    try:
        chatbot = await initialize_client()

        if context is None:
            context = {}

        state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "context": context
        }

        result = await chatbot.ainvoke(state)

        return extract_response(result["messages"])

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"LangGraph processing failed: {str(e)}")


# =========================================================
# RESPONSE PARSER
# =========================================================

def extract_response(messages):
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                return {"type": "tool_result", "data": data}
            except:
                return {"type": "tool_result", "data": {"raw": msg.content}}

    for msg in reversed(messages):
        if hasattr(msg, "content"):
            return {"type": "assistant", "data": msg.content}

    return {"type": "error", "data": "No response"}