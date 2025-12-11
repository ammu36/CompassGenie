from fastapi import APIRouter, HTTPException
from ..domain.agent_state import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Processes a user's geographical query using the LangGraph agent.
    """
    try:
        result = {}
        result['response_text'] = "to be added"
        final_map_data = ""

        return ChatResponse(
            response_text=result["response_text"],
            map_data=final_map_data
        )
    except ValueError as ve:
        # Catch explicit validation errors (e.g., missing API key)
        raise HTTPException(status_code=503, detail=str(ve))
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")