import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional
import google.generativeai as genai
from pydantic import BaseModel, Field
from fastapi import HTTPException

db_path = os.getenv("CACHE_DATABASE_PATH", "ai_cache.db")

def init_cache_db():
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_cache (
                content_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_cache (
                content_hash TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
    except Exception as e:
        print(f"Error initializing cache database: {e}")
    finally:
        conn.close()

# Initialize database at import time
init_cache_db()

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def get_cached_email(content_hash: str) -> Optional[str]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT response_json FROM email_cache WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        conn.close()

def set_cached_email(content_hash: str, response_json: str):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO email_cache (content_hash, response_json, created_at) VALUES (?, ?, ?)",
            (content_hash, response_json, datetime.utcnow().isoformat())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

def get_cached_meeting(content_hash: str) -> Optional[str]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT response_json FROM meeting_cache WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        conn.close()

def set_cached_meeting(content_hash: str, response_json: str):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO meeting_cache (content_hash, response_json, created_at) VALUES (?, ?, ?)",
            (content_hash, response_json, datetime.utcnow().isoformat())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

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

class MeetingParticipantItem(BaseModel):
    email: str = Field(description="Email address of the participant.")
    name: str = Field(description="Name or display name of the participant if mentioned, otherwise empty string.")

class MeetingExtractionResponse(BaseModel):
    is_meeting: bool = Field(description="True if the text contains a meeting request/invitation, reschedule/update, or cancellation. Otherwise False.")
    action_type: str = Field(description="Type of action. Allowed values: 'create' (for new meetings), 'update' (for reschedules or timing updates), or 'cancel' (for cancellations).")
    meeting_title: str = Field(description="Title of the meeting. E.g. 'Sprint Planning'.")
    meeting_platform: str = Field(description="Platform for the meeting. Allowed values: 'Google Meet', 'Microsoft Teams', 'Zoom', or 'Other'.")
    meeting_url: str = Field(description="URL for joining the meeting if specified, otherwise empty string.")
    organizer: str = Field(description="The organizer's email address or name.")
    participants: list[MeetingParticipantItem] = Field(description="List of meeting participants (their email addresses or names if mentioned).")
    start_date: str = Field(description="Start date of the meeting in YYYY-MM-DD format. Resolve relative expressions relative to the current reference date context.")
    start_time: str = Field(description="Start time of the meeting in HH:MM format (24-hour).")
    end_date: str = Field(description="End date of the meeting in YYYY-MM-DD format.")
    end_time: str = Field(description="End time of the meeting in HH:MM format (24-hour). If not mentioned, set to 30 minutes after start_time.")

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
    h = get_hash(email_content)
    cached_val = get_cached_email(h)
    if cached_val:
        try:
            return EmailAnalysis.model_validate_json(cached_val)
        except Exception:
            pass

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
        
        try:
            set_cached_email(h, response.text)
        except Exception:
            pass
            
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

    results = {}
    emails_to_analyze = []
    
    for email in emails:
        email_id = email.get("id")
        body_snippet = (email.get("body") or email.get("snippet") or "")[:1200]
        content_str = f"{email.get('sender')}|{email.get('subject')}|{body_snippet}"
        h = get_hash(content_str)
        
        cached_val = get_cached_email(h)
        if cached_val:
            try:
                cached_data = json.loads(cached_val)
                cached_data["id"] = email_id
                results[email_id] = EmailAnalysisItem(**cached_data)
            except Exception:
                emails_to_analyze.append(email)
        else:
            emails_to_analyze.append(email)

    if not emails_to_analyze:
        return results

    api_key = get_api_key()
    genai.configure(api_key=api_key)

    email_prompts = []
    for email in emails_to_analyze:
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
        
        for item in bulk_data.analyses:
            orig_email = next((e for e in emails_to_analyze if e.get("id") == item.id), None)
            if orig_email:
                body_snippet = (orig_email.get("body") or orig_email.get("snippet") or "")[:1200]
                content_str = f"{orig_email.get('sender')}|{orig_email.get('subject')}|{body_snippet}"
                h = get_hash(content_str)
                try:
                    set_cached_email(h, json.dumps(item.model_dump()))
                except Exception:
                    pass
            results[item.id] = item
            
        return results

    except Exception as e:
        raise Exception(f"Bulk Gemini analysis failed: {str(e)}")

def extract_meeting_from_text(email_content: str, current_date_context: str) -> MeetingExtractionResponse:
    """
    Analyzes an email to extract structured meeting information, resolve relative dates, and classify action type.
    """
    content_str = f"{email_content}|{current_date_context}"
    h = get_hash(content_str)
    
    cached_val = get_cached_meeting(h)
    if cached_val:
        try:
            return MeetingExtractionResponse.model_validate_json(cached_val)
        except Exception:
            pass

    api_key = get_api_key()
    genai.configure(api_key=api_key)

    system_instruction = (
        "You are an expert Chief of Staff AI assistant specializing in calendar scheduling and email parsing. "
        "Your task is to analyze the email content and extract structured meeting details if the email mentions a meeting request, rescheduling, or cancellation. "
        f"The current reference date is {current_date_context}. Use this date to resolve relative date expressions like 'tomorrow', 'next Monday', etc. "
        "Rules:\n"
        "1. Identify if this email refers to a meeting request/invitation, reschedule, or cancellation. If so, set is_meeting=True. If not, set is_meeting=False.\n"
        "2. Determine the action_type: 'create' (for new meetings), 'update' (for reschedules or timing updates), or 'cancel' (for cancellations).\n"
        "3. Extract the meeting title (e.g., 'Sprint Review', 'Catch up'). If not clear, generate a professional title based on the context.\n"
        "4. Identify the platform ('Google Meet', 'Microsoft Teams', 'Zoom', or 'Other').\n"
        "5. Extract the join URL if present in the text.\n"
        "6. Extract the organizer (name and/or email address).\n"
        "7. Extract the list of participants (email and name if available).\n"
        "8. Resolve start_date and end_date in YYYY-MM-DD format. Resolve start_time and end_time in HH:MM format (24-hour). "
        "If the end time is not mentioned, make it 30 or 60 minutes after start_time.\n"
        "9. If is_meeting is False, you MUST still return the JSON structure; populate empty strings, false, or empty lists as appropriate."
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            system_instruction=system_instruction
        )

        response = model.generate_content(
            f"Analyze the following email content and extract meeting details:\n\n{email_content}",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=MeetingExtractionResponse
            )
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="Gemini failed to return meeting extraction response.")

        parsed_result = MeetingExtractionResponse.model_validate_json(response.text)
        
        try:
            set_cached_meeting(h, response.text)
        except Exception:
            pass
            
        return parsed_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini meeting extraction failed: {str(e)}")
