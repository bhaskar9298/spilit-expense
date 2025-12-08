# client/langgraph_service.py - LangGraph MCP Service
from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import json
import asyncio
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
mcp_server_url = os.getenv("MCP_SERVER_URL", "https://optimistic-brown-antelope.fastmcp.app/mcp")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0.1
)

# MCP client - global instance
_mcp_client = None
_chatbot = None

# State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def initialize_client():
    """Initialize MCP client and chatbot graph once"""
    global _mcp_client, _chatbot
    
    if _chatbot is not None:
        return _chatbot
    
    # Initialize MCP client
    _mcp_client = MultiServerMCPClient(
        {
            "expense": {
                "transport": "streamable_http",
                "url": mcp_server_url
            }
        }
    )
    
    # Get tools from MCP server
    tools = await _mcp_client.get_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Build graph
    async def chat_node(state: ChatState):
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {'messages': [response]}
    
    tool_node = ToolNode(tools)
    
    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    
    _chatbot = graph.compile()
    return _chatbot

async def process_tool_call(tool_name: str, args: dict, user_id: str):
    """
    Process a pre-parsed tool call (from Gemini.js) through LangGraph
    This maintains compatibility with existing frontend
    """
    try:
        # Initialize chatbot if needed
        chatbot = await initialize_client()
        
        # Inject user_id into args
        args_with_user = {
            "user_id": user_id,
            **args
        }
        
        # Convert to natural language for LLM
        if tool_name == "add_expense":
            user_input = f"Add an expense: amount={args.get('amount')}, category={args.get('category')}, date={args.get('date')}"
            if args.get('subcategory'):
                user_input += f", subcategory={args.get('subcategory')}"
            if args.get('note'):
                user_input += f", note={args.get('note')}"
        elif tool_name == "list_expenses":
            user_input = f"List expenses from {args.get('start_date')} to {args.get('end_date')}"
        elif tool_name == "summarize":
            user_input = f"Summarize expenses from {args.get('start_date')} to {args.get('end_date')}"
            if args.get('category'):
                user_input += f" for category {args.get('category')}"
        else:
            user_input = f"Call tool {tool_name} with args: {json.dumps(args)}"
        
        # Add user context
        enhanced_input = f"""User ID: {user_id}
Task: {user_input}

CRITICAL: When calling MCP tools, use these EXACT parameters:
{json.dumps(args_with_user, indent=2)}

Dates must be in YYYY-MM-DD format (no timestamps).
"""
        
        # Run the graph
        result = await chatbot.ainvoke({
            "messages": [HumanMessage(content=enhanced_input)]
        })
        
        # Extract tool result from messages
        for msg in reversed(result['messages']):
            # Look for tool message type
            if hasattr(msg, 'type') and msg.type == 'tool':
                try:
                    # Parse JSON content
                    return json.loads(msg.content)
                except json.JSONDecodeError:
                    return {"content": msg.content}
        
        # Fallback: return final message content
        final_message = result['messages'][-1]
        return {"content": final_message.content}
        
    except Exception as e:
        raise Exception(f"LangGraph processing failed: {str(e)}")

# For testing
if __name__ == '__main__':
    async def test():
        result = await process_tool_call(
            "list_expenses",
            {
                "start_date": "2025-12-01",
                "end_date": "2025-12-31"
            },
            "69340c8c3a58dfab5e887dd2"
        )
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
