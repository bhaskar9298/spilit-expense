# client/langgraph_service.py

from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
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
# SCHEMA FIX (CRITICAL for Gemini compatibility)
# =========================================================

def fix_schema_dict(schema: dict, tool_name: str):
    if not isinstance(schema, dict):
        return {"type": "string"}

    schema_type = schema.get("type")

    if schema_type == "array":
        if "items" not in schema:
            print(f"⚠️ Fixing array items for {tool_name}")
            schema["items"] = {"type": "string"}
        else:
            schema["items"] = fix_schema_dict(schema["items"], tool_name)

    elif schema_type == "object":
        props = schema.get("properties", {})
        for key, val in props.items():
            props[key] = fix_schema_dict(val, f"{tool_name}.{key}")

    if "type" not in schema:
        schema["type"] = "string"

    return schema


def fix_tool_schema(tool):
    try:
        if isinstance(tool.args_schema, dict):
            tool.args_schema = fix_schema_dict(tool.args_schema, tool.name)
            return tool
        elif hasattr(tool.args_schema, "model_json_schema"):
            original_fn = tool.args_schema.model_json_schema
            def patched():
                return fix_schema_dict(original_fn(), tool.name)
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
# SECURE TOOL NODE — hard-injects user_id from state
# =========================================================

class SecureToolNode:
    """
    Wraps tool execution to hard-overwrite user_id on every tool call.
    The LLM never controls which user_id is used — it's always pulled
    from the verified JWT state set by the FastAPI gateway.
    """

    def __init__(self, tools: list):
        self.tools_by_name = {tool.name: tool for tool in tools}

    async def __call__(self, state: ChatState) -> dict:
        user_id = state["user_id"]
        messages = state["messages"]

        # Find the last AIMessage that contains tool_calls
        last_ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                last_ai_message = msg
                break

        if not last_ai_message:
            return {"messages": []}

        tool_results = []

        for tool_call in last_ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])  # copy to avoid mutation

            # 🔒 SECURITY: Force user_id regardless of what LLM provided
            if "user_id" in tool_args or tool_name not in ("setup_database",):
                tool_args["user_id"] = user_id
                print(f"🔒 Injected user_id={user_id} into tool '{tool_name}'")

            tool = self.tools_by_name.get(tool_name)
            if not tool:
                result_content = json.dumps({"status": "error", "message": f"Tool '{tool_name}' not found"})
            else:
                try:
                    result = await tool.ainvoke(tool_args)
                    result_content = json.dumps(result) if not isinstance(result, str) else result
                except Exception as e:
                    result_content = json.dumps({"status": "error", "message": str(e)})

            tool_results.append(
                ToolMessage(
                    content=result_content,
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )

        return {"messages": tool_results}


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

        tools = validate_tool_schema(tools)

        llm_with_tools = llm.bind_tools(tools)

        # =================================================
        # GRAPH
        # =================================================

        async def chat_node(state: ChatState) -> dict:
            messages = state["messages"]
            last = messages[-1]

            # Only enhance the initial human message (not tool results looping back)
            if isinstance(last, HumanMessage):
                enhanced_content = (
                    f"You are an expense tracking assistant.\n"
                    f"Today's date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
                    f"User request: \"{last.content}\"\n\n"
                    f"Instructions:\n"
                    f"- Do NOT include or guess user_id — it is injected automatically\n"
                    f"- Convert relative dates (today, yesterday, this month) to YYYY-MM-DD\n"
                    f"- Use the correct tool for the request\n"
                    f"- Respond naturally after tool results"
                )
                messages = messages[:-1] + [HumanMessage(content=enhanced_content)]

            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        secure_tool_node = SecureToolNode(tools)

        graph = StateGraph(ChatState)
        graph.add_node("chat_node", chat_node)
        graph.add_node("tools", secure_tool_node)

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

        state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "context": context or {}
        }

        result = await chatbot.ainvoke(state)
        return extract_response(result["messages"])

    except Exception as e:
        traceback.print_exc()
        raise Exception(f"LangGraph processing failed: {str(e)}")


# =========================================================
# RESPONSE PARSER (unchanged — Fix #5 is next)
# =========================================================

def extract_response(messages):
    # Return the last AIMessage — it has already synthesized the tool results
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return {"type": "assistant", "data": msg.content}

    # Fallback: if no AI synthesis, return the last tool result raw
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                return {"type": "tool_result", "data": data}
            except:
                return {"type": "tool_result", "data": {"raw": msg.content}}

    return {"type": "error", "data": "No response"}