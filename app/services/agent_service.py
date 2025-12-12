import json
from typing import Literal, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from ..core.config import settings
from ..domain.agent_state import AgentState
from .google_maps import maps_api_search


llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE
)


@tool
def google_search_for_weather(query: str, location: str) -> str:
    """Finds weather or current facts."""
    try:
        # Use the configured LLM directly for the search
        response = llm.invoke(f"Answer briefly in bullet points: {query} near {location}")
        return response.content
    except Exception as e:
        return f"Search failed: {e}"


tools = [google_search_for_weather, maps_api_search]
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState):
    """The main agent function for decision making."""
    messages = state["messages"]
    user_loc = state["user_location"]

    system_msg = SystemMessage(content=(
        "You are CompassGenie, an AI map assistant. "
        f"User Location: Lat: {user_loc.get('lat')}, Lng: {user_loc.get('lng')}. "
        "**CRITICAL ROUTING INSTRUCTIONS:** "
        "1. **Route Planning:** If the user specifies a starting location other than their current location, "
        "pass that address to the 'origin_override' parameter of 'maps_api_search'. "
        "2. **Destination:** Pass the endpoint to the 'search_term' parameter. "
        "3. **General Search:** If no route is requested, use 'search_term' for the place query. "
        "4. **Formatting:** Always format lists as Markdown bullet points."
    ))

    response = llm_with_tools.invoke([system_msg] + messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Conditional edge to determine if tools should be called."""
    if state["messages"][-1].tool_calls:
        return "tools"
    return "end"


def setup_agent_graph():
    """Initializes and compiles the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")

    # Using in-memory checkpointing for simplicity
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


app_graph = setup_agent_graph()


def invoke_agent_service(query: str, location: Dict[str, float]) -> dict:
    """
    The main callable function to run the LangGraph agent.
    Returns the final AI text response and map data.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API Key missing")

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "user_location": location
    }
    config = {"configurable": {"thread_id": "unique_user_session_id"}}  # Thread ID for checkpointing
    final_state = app_graph.invoke(initial_state, config=config)

    last_message = final_state["messages"][-1]
    response_text = last_message.content
    map_data = None

    # Search for the latest ToolMessage containing map_data
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, HumanMessage): break
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if "map_data" in data and (data["map_data"].get("points") or data["map_data"].get("routes")):
                    map_data = data["map_data"]
                    break
            except:
                continue

    return {"response_text": response_text, "map_data": map_data}
