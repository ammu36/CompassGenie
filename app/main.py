import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.endpoints import router as api_router

# --- Application Setup ---

app = FastAPI(title=settings.APP_NAME)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router)

# --- Entry Point ---

if __name__ == "__main__":
    # You would typically run this via 'uvicorn app.main:app --reload'
    # This block is for direct execution
    uvicorn.run(app, host="0.0.0.0", port=8000)