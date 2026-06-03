import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from fastapi import HTTPException
import json

class EmailAnalysis(BaseModel):
    summary: str = Field(description="A concise executive summary of the email, highlighting the sender's main request and deadlines. Maximum 2-3 sentences.")
    priority: str = Field(description="Priority classification of the email. Allowed values: 'High', 'Medium', 'Low'.")
    reply: str = Field(description="A professional, polite, and concise reply suggestion written from the executive's perspective. Maximum 2 paragraphs.")
    is_spam_false_positive: bool = Field(description="True if the email was in spam but is actually a legitimate business email, a client inquiry, or meeting invitation (false positive spam).")
    spam_analysis_reason: str = Field(description="If the email is a spam false positive, give a brief 1-sentence reason (e.g. 'Legitimate business query from client').")
    is_meeting_request: bool = Field(description="True if this is a calendar invite, meeting request, call scheduler, or request to meet.")
    has_deadline: bool = Field(description="True if a task deadline or urgent date is mentioned in the email.")
    deadline_date: str = Field(description="The specific deadline date/time or timeframe (e.g. 'Friday at noon', 'June 10') if present.")

class EmailAnalysisItem(BaseModel):
    id: str = Field(description="The unique message ID of the email being analyzed.")
    summary: str = Field(description="A concise executive summary of the email, highlighting the sender's main request and deadlines. Maximum 2-3 sentences.")
    priority: str = Field(description="Priority classification of the email. Allowed values: 'High', 'Medium', 'Low'.")
    reply: str = Field(description="A professional, polite, and concise reply suggestion written from the executive's perspective. Maximum 2 paragraphs.")
    is_spam_false_positive: bool = Field(description="True if the email was in spam but is actually a legitimate business email, a client inquiry, or meeting invitation (false positive spam).")
    spam_analysis_reason: str = Field(description="If the email is a spam false positive, give a brief 1-sentence reason (e.g. 'Legitimate business query from client').")
    is_meeting_request: bool = Field(description="True if this is a calendar invite, meeting request, call scheduler, or request to meet.")
    has_deadline: bool = Field(description="True if a task deadline or urgent date is mentioned in the email.")
    deadline_date: str = Field(description="The specific deadline date/time or timeframe (e.g. 'Friday at noon', 'June 10') if present.")

class BulkEmailAnalysis(BaseModel):
    analyses: list[EmailAnalysisItem] = Field(description="List of email analyses matching the input email IDs.")

def get_api_key() -> str:
    """
    Resolves the Gemini API Key from environment variables.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    api_key = gemini_key
    if not api_key or api_key.startswith("your_"):
        if openai_key and openai_key.startswith("AIza"):
            api_key = openai_key
            
    if not api_key or api_key.startswith("your_"):
        raise HTTPException(
            status_code=500,
            detail="Gemini API Key (GEMINI_API_KEY) is not configured on the AI microservice."
        )
    return api_key

def analyze_email_content(email_content: str) -> EmailAnalysis:
    """
    Sends the email content to Google's gemini-flash-latest model using Structured Outputs.
    Returns a validated EmailAnalysis Pydantic model.
    """
    api_key = get_api_key()
    genai.configure(api_key=api_key)

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
        "Ensure placeholders like [Your Name] are left only where absolutely necessary, but prioritize phrasing it clearly.\n"
        "4. is_spam_false_positive: Set to true if the email is a legitimate business email, a customer inquiry, or a meeting request (even if flagged as spam).\n"
        "5. spam_analysis_reason: A brief explanation why the email is legitimate (if it is a false positive).\n"
        "6. is_meeting_request: Set to true if the email is a meeting request, calendar invite, scheduling request, or suggestion to meet.\n"
        "7. has_deadline: Set to true if a task deadline or urgent date is mentioned.\n"
        "8. deadline_date: The specific deadline timeframe extracted if present."
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction
        )

        response = model.generate_content(
            f"Analyze the following email content:\n\n{email_content}",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=EmailAnalysis
            )
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="Gemini failed to return content response.")

        parsed_result = EmailAnalysis.model_validate_json(response.text)
        return parsed_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API invocation failed: {str(e)}")

def analyze_emails_bulk(emails: list[dict]) -> dict[str, EmailAnalysisItem]:
    """
    Sends a bulk list of emails to Gemini in a single request for fast, cost-efficient analysis.
    Returns a dict mapping message_id -> EmailAnalysisItem.
    """
    if not emails:
        return {}

    api_key = get_api_key()
    genai.configure(api_key=api_key)

    email_prompts = []
    for email in emails:
        body_snippet = (email.get("body") or email.get("snippet") or "")[:1200]
        # Pass folder context so Gemini knows if an email is in SPAM
        folder_info = f"FOLDER: {email.get('folder', 'INBOX')}\n"
        email_prompts.append(
            f"EMAIL ID: {email.get('id')}\n"
            f"FROM: {email.get('sender')}\n"
            f"SUBJECT: {email.get('subject')}\n"
            f"DATE: {email.get('date')}\n"
            f"{folder_info}"
            f"BODY:\n{body_snippet}\n"
            f"---"
        )
    
    formatted_emails = "\n\n".join(email_prompts)

    system_instruction = (
        "You are an elite, executive-level Chief of Staff AI assistant. "
        "Your task is to analyze a batch of emails and return an analysis for EACH email in the list. "
        "For each email ID, provide:\n"
        "1. Summary: Action-oriented, highlighting the main request and deadlines. Keep it brief (under 3 sentences).\n"
        "2. Priority:\n"
        "   - 'High': Actions needing immediate executive decisions, high-value client issues, or tight deadlines.\n"
        "   - 'Medium': Routine updates, non-urgent client followups, or scheduling requests.\n"
        "   - 'Low': Informational newsletters, internal FYI messages, or generic promotional emails.\n"
        "3. Reply: A concise, polished draft response written from the executive's perspective (max 2 paragraphs). "
        "Keep placeholders to a minimum, and write it in a professional, clear, action-oriented tone.\n"
        "4. is_spam_false_positive: Set to true if the email is located in the SPAM folder but contains a legitimate business query, customer/client communication, or meeting invitation.\n"
        "5. spam_analysis_reason: A brief explanation why the email is legitimate (if it is a false positive in SPAM).\n"
        "6. is_meeting_request: Set to true if the email is a calendar invitation, call scheduling request, or suggestion to meet.\n"
        "7. has_deadline: Set to true if a specific date or timeframe for a task/action is mentioned.\n"
        "8. deadline_date: The specific deadline date/time extracted if present."
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction
        )

        response = model.generate_content(
            f"Analyze the following batch of emails:\n\n{formatted_emails}",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=BulkEmailAnalysis
            )
        )

        if not response.text:
            raise Exception("Gemini returned an empty bulk response.")

        bulk_data = BulkEmailAnalysis.model_validate_json(response.text)
        result_dict = {item.id: item for item in bulk_data.analyses}
        return result_dict

    except Exception as e:
        raise Exception(f"Bulk Gemini analysis failed: {str(e)}")
