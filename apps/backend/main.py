from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
from openai_client import get_openai_client
from pydantic import BaseModel, ValidationError
from generate_module import generate_router
from validate_module import validate_router
from failure_labeling_module import failure_labeling_router

load_dotenv()

client = get_openai_client()

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Repair DIY AI Backend",
    description="Backend API for Repair DIY AI application",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api", tags=["generate"])
app.include_router(validate_router, prefix="/api", tags=["validate"])
app.include_router(failure_labeling_router, prefix="/api", tags=["failure-labeling"])

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="success", message="Repair DIY AI Backend is running")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="success", message="Backend is healthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)