from fastapi import APIRouter, HTTPException
from ..domain.agent_state import ChatRequest, ChatResponse, MapData
from ..services.agent_service import invoke_agent_service
import requests
from ..core.config import settings

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Processes a user's geographical query using the LangGraph agent.
    """
    try:
        # Call the core logic in the service layer
        result = invoke_agent_service(request.query, request.location)

        # Convert the raw map_data dictionary into the Pydantic MapData model
        final_map_data = MapData(**result["map_data"]) if result["map_data"] else None

        return ChatResponse(
            response_text=result["response_text"],
            map_data=final_map_data
        )
    except ValueError as ve:
        # To catch explicit validation errors (e.g., missing API key)
        raise HTTPException(status_code=503, detail=str(ve))
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/health")
async def health_check():
    """
    Standard health check for orchestration (Docker/K8s).
    Checks connectivity to external dependencies.
    """
    health_status = {
        "status": "healthy",
        "dependencies": {
            "google_maps_api": "unknown",
            "gemini_api": "ok" if settings.GEMINI_API_KEY else "missing"
        }
    }

    try:
        res = requests.get("https://maps.googleapis.com/maps/api/staticmap", timeout=2)
        health_status["dependencies"]["google_maps_api"] = "reachable" if res.status_code == 200 else "error"
    except Exception:
        health_status["dependencies"]["google_maps_api"] = "unreachable"

    if health_status["dependencies"]["google_maps_api"] == "unreachable" or not settings.GEMINI_API_KEY:
        health_status["status"] = "unhealthy"
        # We return a 503 so Docker knows the service is degraded
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
