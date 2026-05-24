from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routes.auth import router as auth_router
from routes.emails import router as emails_router
from routes.ai import router as ai_router

app = FastAPI(
    title="AI-Powered Executive Email Assistant API",
    description="Backend API for email summarization, priority detection, and automated replies.",
    version="1.0.0"
)

# Configure CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(emails_router, prefix="/emails", tags=["Emails"])
app.include_router(ai_router, prefix="/ai", tags=["AI Processing"])

@app.get("/", tags=["General"])
async def root():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "AI Executive Email Assistant API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
