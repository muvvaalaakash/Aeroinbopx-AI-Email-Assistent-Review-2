import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config.settings import settings
from auth_deps import get_session_accounts, AccountPayload
from redis_client import redis_manager

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic schemas for request/response payloads
class GetEmailsRequest(BaseModel):
    accounts: List[AccountPayload] = []
    include_read: bool = False

class GetEmailsResponse(BaseModel):
    emails: List[dict]
    refreshed_tokens: Dict[str, str]

class MarkSafeRequest(BaseModel):
    sender_email: str

async def trigger_meeting_detection(emails: List[dict]):
    """
    Triggers meeting detection asynchronously on the meeting service in the background.
    """
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{settings.MEETING_SERVICE_URL}/meetings/detect",
                json={"emails": emails},
                timeout=15.0
            )
        except Exception as e:
            logger.error(f"Error triggering background meeting detection: {str(e)}")

async def refresh_google_token(refresh_token: str) -> Optional[str]:
    """
    Exchanges a refresh token for a new access token via Google APIs.
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data, timeout=10.0)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.error(f"Google Token refresh returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Exception refreshing Google token: {str(e)}")
    return None

@router.get("/unread")
async def get_unread_emails_legacy(
    background_tasks: BackgroundTasks,
    accounts: List[AccountPayload] = Depends(get_session_accounts),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Legacy GET endpoint for single-account backward compatibility.
    Calls the new multi-account logic under the hood with session accounts.
    """
    payload = GetEmailsRequest(
        accounts=accounts,
        include_read=False
    )
    result = await fetch_and_prioritize_emails(
        payload=payload,
        background_tasks=background_tasks,
        accounts=accounts,
        credentials=credentials
    )
    return result["emails"]

@router.post("/unread", response_model=GetEmailsResponse)
async def fetch_and_prioritize_emails(
    payload: GetEmailsRequest,
    background_tasks: BackgroundTasks,
    accounts: List[AccountPayload] = Depends(get_session_accounts),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Primary endpoint that fetches emails for multiple accounts, refreshes expired tokens,
    runs the rules engine & AI on unread messages, calculates hybrid priorities, and returns them.
    """
    session_id = credentials.credentials
    refreshed_tokens = {}
    all_emails = []
    
    # Overwrite the request accounts with validated credentials from the Redis session
    payload.accounts = accounts

    # 1. Fetch raw emails for each account in parallel
    async def process_account(acc: AccountPayload):
        nonlocal refreshed_tokens
        access_token = acc.access_token
        
        async with httpx.AsyncClient() as client:
            try:
                fetch_body = {
                    "accounts": [{"email": acc.email, "access_token": access_token}],
                    "include_read": payload.include_read,
                    "max_results": 15
                }
                response = await client.post(
                    f"{settings.GMAIL_SERVICE_URL}/fetch",
                    json=fetch_body,
                    timeout=30.0
                )
                
                # Check for unauthorized (token expired)
                if response.status_code == 401 and acc.refresh_token:
                    logger.info(f"Access token expired for {acc.email}. Refreshing...")
                    new_token = await refresh_google_token(acc.refresh_token)
                    if new_token:
                        refreshed_tokens[acc.email] = new_token
                        # Update token in active local copy
                        access_token = new_token
                        
                        # Update in Redis session
                        if session_id:
                            try:
                                redis_client = await redis_manager.get_client()
                                session_key = f"session:{session_id}"
                                session_data = await redis_client.get(session_key)
                                if session_data:
                                    sess_accs = json.loads(session_data)
                                    for sa in sess_accs:
                                        if sa.get("email") == acc.email:
                                            sa["access_token"] = new_token
                                    await redis_client.setex(session_key, 3600, json.dumps(sess_accs))
                                    logger.info(f"Refreshed token updated in Redis session for {acc.email}")
                            except Exception as ex:
                                logger.error(f"Failed to update session token in Redis: {str(ex)}")

                        # Retry the request with the new access token
                        fetch_body["accounts"][0]["access_token"] = access_token
                        response = await client.post(
                            f"{settings.GMAIL_SERVICE_URL}/fetch",
                            json=fetch_body,
                            timeout=30.0
                        )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Gmail Service returned {response.status_code} for {acc.email}: {response.text}")
                    return []
            except Exception as e:
                logger.error(f"Orchestrator error fetching emails for {acc.email}: {str(e)}")
                return []
                 
    tasks = [process_account(acc) for acc in payload.accounts]
    accounts_emails = await asyncio.gather(*tasks)
    
    # Flatten emails
    for emails_list in accounts_emails:
        all_emails.extend(emails_list)
        
    if all_emails:
        background_tasks.add_task(trigger_meeting_detection, all_emails)
        
    if not all_emails:
        return GetEmailsResponse(emails=[], refreshed_tokens=refreshed_tokens)
        
    # 2. Separate unread and read emails
    unread_emails = [e for e in all_emails if e.get("read_status") == "unread"]
    read_emails = [e for e in all_emails if e.get("read_status") == "read"]
    
    # 3. Analyze unread emails (rules engine + AI)
    if unread_emails:
        async with httpx.AsyncClient() as client:
            rule_task = client.post(
                f"{settings.RULE_ENGINE_SERVICE_URL}/evaluate/bulk",
                json=unread_emails,
                timeout=15.0
            )
            ai_task = client.post(
                f"{settings.AI_SERVICE_URL}/process/bulk",
                json={"emails": unread_emails},
                timeout=45.0
            )
            
            try:
                rule_res, ai_res = await asyncio.gather(rule_task, ai_task, return_exceptions=True)
                
                # Parse Rules Engine results
                rule_data = {}
                if isinstance(rule_res, httpx.Response) and rule_res.status_code == 200:
                    rule_data = rule_res.json()
                else:
                    logger.error(f"Rule Engine call failed: {rule_res}")
                    
                # Parse AI Service results
                ai_data = {}
                if isinstance(ai_res, httpx.Response) and ai_res.status_code == 200:
                    ai_data = ai_res.json()
                else:
                    logger.error(f"AI Service call failed: {ai_res}")
                    
                # 4. Compute hybrid priority for each unread email
                for email in unread_emails:
                    email_id = email.get("id")
                    
                    r_info = rule_data.get(email_id, {"rule_score": 0, "matched_rules": []})
                    email["rule_analysis"] = {
                        "rule_score": r_info.get("rule_score", 0),
                        "matched_rules": r_info.get("matched_rules", [])
                    }
                    
                    ai_info = ai_data.get(email_id)
                    if ai_info:
                        email["ai_analysis"] = {
                            "summary": ai_info.get("summary"),
                            "priority": ai_info.get("priority"),
                            "reply": ai_info.get("reply"),
                            "is_spam_false_positive": ai_info.get("is_spam_false_positive", False),
                            "spam_analysis_reason": ai_info.get("spam_analysis_reason", ""),
                            "is_meeting_request": ai_info.get("is_meeting_request", False),
                            "has_deadline": ai_info.get("has_deadline", False),
                            "deadline_date": ai_info.get("deadline_date", "")
                        }
                    else:
                        email["ai_analysis"] = None
                        
                    # Calculate Scores:
                    # AI Score: Critical/High=30, Medium=15, Low=0. Boost meeting (+10), deadline (+10)
                    ai_score = 0
                    if email["ai_analysis"]:
                        ai_priority = email["ai_analysis"].get("priority", "Low")
                        if ai_priority == "High" or ai_priority == "Critical":
                            ai_score = 30
                        elif ai_priority == "Medium":
                            ai_score = 15
                            
                        if email["ai_analysis"].get("is_meeting_request"):
                            ai_score += 10
                        if email["ai_analysis"].get("has_deadline"):
                            ai_score += 10
                            
                    rule_score = email["rule_analysis"].get("rule_score", 0)
                    preference_score = 0
                    
                    # Spam folder penalty/adjustment
                    if email.get("folder") == "SPAM":
                        if email["ai_analysis"] and email["ai_analysis"].get("is_spam_false_positive"):
                            preference_score += 10
                        else:
                            ai_score = 0
                            rule_score = 0
                            
                    final_score = ai_score + rule_score + preference_score
                    
                    if final_score >= 70:
                        email["final_priority"] = "Critical"
                    elif final_score >= 45:
                        email["final_priority"] = "High"
                    elif final_score >= 20:
                        email["final_priority"] = "Medium"
                    else:
                        email["final_priority"] = "Low"
                        
                    email["final_score"] = final_score
            except Exception as e:
                logger.error(f"Error during orchestrator batch evaluation: {str(e)}")
                for email in unread_emails:
                    email["rule_analysis"] = None
                    email["ai_analysis"] = None
                    email["final_priority"] = "Low"
                    email["final_score"] = 0
                    
    # 5. Process read emails (exclude from active prioritization)
    for email in read_emails:
        email["rule_analysis"] = None
        email["ai_analysis"] = None
        email["final_priority"] = None
        email["final_score"] = 0
        
    priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, None: 0}
    unread_emails.sort(key=lambda x: (priority_order.get(x.get("final_priority")), x.get("timestamp", 0)), reverse=True)
    read_emails.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    sorted_emails = unread_emails + read_emails
    return GetEmailsResponse(emails=sorted_emails, refreshed_tokens=refreshed_tokens)

async def perform_gmail_action(
    id: str,
    action_type: str, # "read", "unread", "move-to-inbox"
    accounts: List[AccountPayload],
    target_email: Optional[str] = None
):
    candidate_accounts = accounts
    if target_email:
        candidate_accounts = [acc for acc in accounts if acc.email == target_email]
        if not candidate_accounts:
            raise HTTPException(status_code=403, detail="Requested email account not in session.")

    last_error = None
    for acc in candidate_accounts:
        async with httpx.AsyncClient() as client:
            try:
                body = {"access_token": acc.access_token}
                if action_type == "read":
                    body["remove_labels"] = ["UNREAD"]
                elif action_type == "unread":
                    body["add_labels"] = ["UNREAD"]
                elif action_type == "move-to-inbox":
                    body["add_labels"] = ["INBOX"]
                    body["remove_labels"] = ["SPAM"]
                
                response = await client.post(
                    f"{settings.GMAIL_SERVICE_URL}/emails/{id}/labels",
                    json=body,
                    timeout=15.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    last_error = HTTPException(status_code=response.status_code, detail=response.text)
            except httpx.HTTPError as e:
                last_error = HTTPException(status_code=502, detail=f"Failed to contact Gmail service: {str(e)}")
    
    if last_error:
        raise last_error
    raise HTTPException(status_code=400, detail="No active accounts to perform action.")

# Label Management Endpoints
@router.post("/{id}/read")
async def mark_read(
    id: str,
    email: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Removes the UNREAD label from a message.
    """
    return await perform_gmail_action(id, "read", accounts, email)

@router.post("/{id}/unread")
async def mark_unread(
    id: str,
    email: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Adds the UNREAD label back to a message.
    """
    return await perform_gmail_action(id, "unread", accounts, email)

@router.post("/{id}/move-to-inbox")
async def move_to_inbox(
    id: str,
    email: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Moves an email from Spam back to the Inbox.
    """
    return await perform_gmail_action(id, "move-to-inbox", accounts, email)

@router.post("/{id}/mark-safe")
async def mark_safe(
    id: str,
    payload: MarkSafeRequest,
    email: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Marks the sender of a spam email as safe (adds to VIP rules) and moves the email to Inbox.
    """
    target_emails = [acc.email for acc in accounts]
    if email:
        if email not in target_emails:
            raise HTTPException(status_code=403, detail="Requested email account not in session.")
        target_emails = [email]

    async with httpx.AsyncClient() as client:
        for u_id in target_emails:
            try:
                rules_resp = await client.get(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", params={"user_id": u_id})
                if rules_resp.status_code == 200:
                    rules = rules_resp.json()
                    custom_senders = rules.get("custom_senders", [])
                    if payload.sender_email not in custom_senders:
                        custom_senders.append(payload.sender_email)
                        rules["custom_senders"] = custom_senders
                        await client.post(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", params={"user_id": u_id}, json=rules)
            except Exception as e:
                logger.error(f"Safe sender registration failed for {u_id}: {str(e)}")
                
    return await perform_gmail_action(id, "move-to-inbox", accounts, email)

# Proxy endpoints for rules configuration
@router.get("/config/rules")
async def get_rules_proxy(
    user_id: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Proxies GET rules request to rule engine.
    """
    if not user_id:
        user_id = accounts[0].email if accounts else "default"
    else:
        if not any(acc.email == user_id for acc in accounts):
            raise HTTPException(status_code=403, detail="Access denied. Account not in session.")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", params={"user_id": user_id}, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Rule Engine: {str(e)}")

@router.post("/config/rules")
async def update_rules_proxy(
    rules: dict,
    user_id: Optional[str] = None,
    accounts: List[AccountPayload] = Depends(get_session_accounts)
):
    """
    Proxies POST rules request to rule engine.
    """
    if not user_id:
        user_id = accounts[0].email if accounts else "default"
    else:
        if not any(acc.email == user_id for acc in accounts):
            raise HTTPException(status_code=403, detail="Access denied. Account not in session.")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", params={"user_id": user_id}, json=rules, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Rule Engine: {str(e)}")
