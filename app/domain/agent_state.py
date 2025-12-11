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


class ChatResponse(BaseModel):
    """Output model for the chat endpoint."""
    response_text: str = Field(..., description="The text response from the AI.")
    map_data: Dict[str, float]