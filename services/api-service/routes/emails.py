import httpx
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config.settings import settings

router = APIRouter()
security = HTTPBearer()

# Pydantic schemas for request/response payloads
class AccountPayload(BaseModel):
    email: str
    access_token: str
    refresh_token: Optional[str] = None

class GetEmailsRequest(BaseModel):
    accounts: List[AccountPayload]
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
            print(f"Error triggering background meeting detection: {str(e)}")

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
                print(f"Google Token refresh returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Exception refreshing Google token: {str(e)}")
    return None

@router.get("/unread")
async def get_unread_emails_legacy(
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Legacy GET endpoint for single-account backward compatibility.
    Calls the new multi-account logic under the hood with a single token.
    """
    token = credentials.credentials
    # Get user email
    email = "legacy@gmail.com"
    async with httpx.AsyncClient() as client:
        try:
            userinfo = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if userinfo.status_code == 200:
                email = userinfo.json().get("email", email)
        except Exception:
            pass
            
    payload = GetEmailsRequest(
        accounts=[AccountPayload(email=email, access_token=token)],
        include_read=False
    )
    result = await fetch_and_prioritize_emails(payload, background_tasks)
    return result["emails"]

@router.post("/unread", response_model=GetEmailsResponse)
async def fetch_and_prioritize_emails(payload: GetEmailsRequest, background_tasks: BackgroundTasks):
    """
    Primary endpoint that fetches emails for multiple accounts, refreshes expired tokens,
    runs the rules engine & AI on unread messages, calculates hybrid priorities, and returns them.
    """
    refreshed_tokens = {}
    all_emails = []
    
    # 1. Fetch raw emails for each account in parallel
    async def process_account(acc: AccountPayload):
        nonlocal refreshed_tokens
        access_token = acc.access_token
        
        async with httpx.AsyncClient() as client:
            try:
                # Call Gmail Service fetch endpoint
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
                    print(f"Access token expired for {acc.email}. Refreshing...")
                    new_token = await refresh_google_token(acc.refresh_token)
                    if new_token:
                        refreshed_tokens[acc.email] = new_token
                        # Retry the request with the new access token
                        fetch_body["accounts"][0]["access_token"] = new_token
                        response = await client.post(
                            f"{settings.GMAIL_SERVICE_URL}/fetch",
                            json=fetch_body,
                            timeout=30.0
                        )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Gmail Service returned {response.status_code} for {acc.email}: {response.text}")
                    return []
            except Exception as e:
                print(f"Orchestrator error fetching emails for {acc.email}: {str(e)}")
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
            # Parallel call to Rule Engine and AI Service
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
                    print(f"Rule Engine call failed: {rule_res}")
                    
                # Parse AI Service results
                ai_data = {}
                if isinstance(ai_res, httpx.Response) and ai_res.status_code == 200:
                    ai_data = ai_res.json()
                else:
                    print(f"AI Service call failed: {ai_res}")
                    
                # 4. Compute hybrid priority for each unread email
                for email in unread_emails:
                    email_id = email.get("id")
                    
                    # Rule evaluations
                    r_info = rule_data.get(email_id, {"rule_score": 0, "matched_rules": []})
                    email["rule_analysis"] = {
                        "rule_score": r_info.get("rule_score", 0),
                        "matched_rules": r_info.get("matched_rules", [])
                    }
                    
                    # AI evaluations
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
                    # - AI Score mapping: Critical/High=30, Medium=15, Low=0. Boost meeting (+10), deadline (+10)
                    ai_score = 0
                    if email["ai_analysis"]:
                        ai_priority = email["ai_analysis"].get("priority", "Low")
                        if ai_priority == "High":
                            ai_score = 30
                        elif ai_priority == "Medium":
                            ai_score = 15
                            
                        # Boosts
                        if email["ai_analysis"].get("is_meeting_request"):
                            ai_score += 10
                        if email["ai_analysis"].get("has_deadline"):
                            ai_score += 10
                            
                    rule_score = email["rule_analysis"].get("rule_score", 0)
                    preference_score = 0 # Future customizable user boost settings
                    
                    # Spam folder penalty/adjustment
                    if email.get("folder") == "SPAM":
                        # If AI marks it as false positive, we treat it normal, otherwise penalize
                        if email["ai_analysis"] and email["ai_analysis"].get("is_spam_false_positive"):
                            # Legit email in spam gets a slight boost to surface it
                            preference_score += 10
                        else:
                            # Not false positive? Keep score 0 (it is spam)
                            ai_score = 0
                            rule_score = 0
                            
                    final_score = ai_score + rule_score + preference_score
                    
                    # Output Priority Categories
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
                print(f"Error during orchestrator batch evaluation: {str(e)}")
                # Graceful fallback: return emails without insights
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
        
    # Combine back and sort
    # Unread priority order: Critical first, then High, then Medium, then Low
    priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, None: 0}
    unread_emails.sort(key=lambda x: (priority_order.get(x.get("final_priority")), x.get("timestamp", 0)), reverse=True)
    read_emails.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    sorted_emails = unread_emails + read_emails
    return GetEmailsResponse(emails=sorted_emails, refreshed_tokens=refreshed_tokens)

# Label Management Endpoints
@router.post("/{id}/read")
async def mark_read(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Removes the UNREAD label from a message.
    """
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.GMAIL_SERVICE_URL}/emails/{id}/labels",
                json={"access_token": token, "remove_labels": ["UNREAD"]},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Gmail service: {str(e)}")

@router.post("/{id}/unread")
async def mark_unread(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Adds the UNREAD label back to a message.
    """
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.GMAIL_SERVICE_URL}/emails/{id}/labels",
                json={"access_token": token, "add_labels": ["UNREAD"]},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Gmail service: {str(e)}")

@router.post("/{id}/move-to-inbox")
async def move_to_inbox(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Moves an email from Spam back to the Inbox.
    """
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.GMAIL_SERVICE_URL}/emails/{id}/labels",
                json={"access_token": token, "add_labels": ["INBOX"], "remove_labels": ["SPAM"]},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Gmail service: {str(e)}")

@router.post("/{id}/mark-safe")
async def mark_safe(id: str, payload: MarkSafeRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Marks the sender of a spam email as safe (adds to VIP rules) and moves the email to Inbox.
    """
    token = credentials.credentials
    
    # 1. Add email address to custom VIP senders list in rule engine
    async with httpx.AsyncClient() as client:
        try:
            # Get current rules
            rules_resp = await client.get(f"{settings.RULE_ENGINE_SERVICE_URL}/rules")
            if rules_resp.status_code == 200:
                rules = rules_resp.json()
                custom_senders = rules.get("custom_senders", [])
                
                # Check if already there
                if payload.sender_email not in custom_senders:
                    custom_senders.append(payload.sender_email)
                    rules["custom_senders"] = custom_senders
                    # Save rules back
                    await client.post(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", json=rules)
        except Exception as e:
            print(f"Safe sender registration failed: {str(e)}")
            # Do not block the label modification if rule updating fails
            
        # 2. Modify labels via Gmail service
        try:
            response = await client.post(
                f"{settings.GMAIL_SERVICE_URL}/emails/{id}/labels",
                json={"access_token": token, "add_labels": ["INBOX"], "remove_labels": ["SPAM"]},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Gmail service: {str(e)}")

# Proxy endpoints for rules configuration
@router.get("/config/rules")
async def get_rules_proxy():
    """
    Proxies GET rules request to rule engine.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Rule Engine: {str(e)}")

@router.post("/config/rules")
async def update_rules_proxy(rules: dict):
    """
    Proxies POST rules request to rule engine.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.RULE_ENGINE_SERVICE_URL}/rules", json=rules, timeout=10.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to contact Rule Engine: {str(e)}")
