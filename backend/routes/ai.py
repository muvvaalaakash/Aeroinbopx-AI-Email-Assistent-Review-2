from fastapi import APIRouter
from pydantic import BaseModel
from services.openai_service import analyze_email_content, EmailAnalysis

router = APIRouter()

class EmailProcessRequest(BaseModel):
    email_content: str

@router.post("/process", response_model=EmailAnalysis)
def process_email(payload: EmailProcessRequest):
    """
    Processes a single email body using OpenAI gpt-4o-mini.
    Returns:
    - summary: Executive summary
    - priority: High, Medium, or Low
    - reply: Professional drafted response
    """
    # Simply delegate to the openai service
    analysis = analyze_email_content(payload.email_content)
    return analysis
