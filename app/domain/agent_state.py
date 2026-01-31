from typing import Annotated, List, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    """The state of the LangGraph agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_location: Dict[str, float]

class ChatRequest(BaseModel):
    """Input model for the chat endpoint."""
    query: str = Field(..., description="The user's natural language query.")
    location: Dict[str, float] = Field(..., description="The user's current latitude and longitude.")
    image: str | None = Field(default=None, description="Optional Base64 encoded image string.")

class MapData(BaseModel):
    """Structure for map visualization data."""
    points: List[Dict[str, Any]] | None = None
    routes: List[Dict[str, Any]] | None = None

class ChatResponse(BaseModel):
    """Output model for the chat endpoint."""
    response_text: str = Field(..., description="The text response from the AI.")
    map_data: MapData | None = Field(None, description="Optional data for rendering a map.")