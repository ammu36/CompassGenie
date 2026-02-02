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
from .aqi_services import get_aqi


llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
    thinking_level=settings.LLM_THINKING_LEVEL
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


tools = [google_search_for_weather, maps_api_search, get_aqi]
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState):
    """The main agent function for decision making."""
    messages = state["messages"]
    user_loc = state["user_location"]

    system_msg = SystemMessage(content=(
        "You are CompassGenie, an AI map assistant. "
        f"User Location: Lat: {user_loc.get('lat')}, Lng: {user_loc.get('lng')}. "
        "**CRITICAL ROUTING INSTRUCTIONS:** "
        "1. For ANY route request or UPDATE (e.g., 'go via...', 'change destination'), "
        "you MUST call 'maps_api_search' with search_type='route'. "
        "2. If the user says 'via [Location]', pass that location to the 'waypoints' parameter. "
        "3. NEVER explain a route in text without also triggering the map tool. "
        "The map and chat must always stay synchronized. "
        "4. If an image is provided, identify the place and use it as the destination."
        "**AQI INSTRUCTIONS:** "
        "1. If the user asks about air quality 'here' or 'nearby', call 'get_aqi' using the lat/lng provided above. "
        "2. If the user mentions a specific city (e.g., 'AQI in Paris'), call 'get_aqi' with the 'location_name' "
        "parameter. "
        "Avoid saying mentioning any other apps name"
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


def invoke_agent_service(query: str, location: Dict[str, float], image_b64: str = None) -> dict:
    """
    The main callable function to run the LangGraph agent.
    Returns the final AI text response and map data.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API Key missing")

    # 1. Prepare Multimodal Content
    # Start with the user's text query
    content = [{"type": "text", "text": query}]

    # Append the image if provided
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
        })

    # 2. Setup initial state with the multimodal message
    initial_state = {
        "messages": [HumanMessage(content=content)],
        "user_location": location
    }

    config = {"configurable": {"thread_id": "unique_user_session_id"}}

    # 3. Run the Graph
    final_state = app_graph.invoke(initial_state, config=config)

    # --- POST-PROCESSING ---
    last_message = final_state["messages"][-1]
    response_text = ""

    if isinstance(last_message.content, str):
        response_text = last_message.content
    elif isinstance(last_message.content, list):
        content_parts = []
        for part in last_message.content:
            if isinstance(part, dict) and part.get('type') == 'text':
                content_parts.append(part.get('text', ''))
        response_text = "\n".join(content_parts)

    map_data = None
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, HumanMessage):
            break
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if "map_data" in data and (data["map_data"].get("points") or data["map_data"].get("routes")):
                    map_data = data["map_data"]
                    break
            except Exception:
                continue

    return {"response_text": response_text, "map_data": map_data}
