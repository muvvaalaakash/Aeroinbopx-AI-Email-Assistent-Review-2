from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field
from fastapi import HTTPException
from config.settings import settings

class EmailAnalysis(BaseModel):
    summary: str = Field(description="A concise executive summary of the email, highlighting the sender's main request and deadlines. Maximum 2-3 sentences.")
    priority: str = Field(description="Priority classification of the email. Allowed values: 'High', 'Medium', 'Low'.")
    reply: str = Field(description="A professional, polite, and concise reply suggestion written from the executive's perspective. Maximum 2 paragraphs.")

def analyze_email_content(email_content: str) -> EmailAnalysis:
    """
    Sends the email content to OpenAI's gpt-4o-mini model using Structured Outputs.
    Returns a validated EmailAnalysis Pydantic model containing summary, priority, and reply.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_"):
        raise HTTPException(
            status_code=500,
            detail="OpenAI API Key is not configured on the server."
        )

    # Initialize OpenAI client
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_instruction = (
        "You are an elite, executive-level Chief of Staff AI assistant. "
        "Your goal is to parse incoming emails for CEOs, founders, and busy managers. "
        "Provide: "
        "1. Summary: Action-oriented, highlighting the main request and deadlines. Keep it brief (under 3 sentences).\n"
        "2. Priority:\n"
        "   - 'High': Actions needing immediate executive decisions, high-value client issues, or tight deadlines.\n"
        "   - 'Medium': Routine updates, non-urgent client followups, or scheduling requests.\n"
        "   - 'Low': Informational newsletters, internal FYI messages, or generic promotional emails.\n"
        "3. Reply: A concise, polished draft of a response. It must sound executive-grade (brief, polite, clear, and action-oriented). "
        "Ensure placeholders like [Your Name] are left only where absolutely necessary, but prioritize phrasing it clearly."
    )

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Analyze the following email content:\n\n{email_content}"}
            ],
            response_format=EmailAnalysis
        )
        parsed_result = completion.choices[0].message.parsed
        if not parsed_result:
            raise HTTPException(status_code=500, detail="OpenAI failed to return parsed JSON response.")
        return parsed_result
    except OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API invocation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during AI analysis: {str(e)}")
