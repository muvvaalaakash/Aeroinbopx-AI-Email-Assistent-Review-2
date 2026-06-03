from fastapi import FastAPI, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from services.gmail_service import fetch_emails, modify_message_labels

app = FastAPI(
    title="AeroInbox Gmail Microservice",
    description="Internal microservice for fetching and parsing emails from the Gmail API.",
    version="1.0.0"
)

security = HTTPBearer()

class AccountCredential(BaseModel):
    email: str
    access_token: str

class FetchEmailsRequest(BaseModel):
    accounts: List[AccountCredential]
    include_read: bool = False
    max_results: int = 15

class ModifyLabelsRequest(BaseModel):
    access_token: str
    add_labels: List[str] = []
    remove_labels: List[str] = []

@app.get("/unread")
async def get_unread(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Exposes a backward-compatible endpoint to fetch unread emails for a single token.
    """
    token = credentials.credentials
    emails = await fetch_emails(access_token=token, include_read=False)
    return emails

@app.post("/fetch")
async def fetch_multi_account_emails(payload: FetchEmailsRequest):
    """
    Fetches emails from multiple Gmail accounts in parallel.
    """
    async def fetch_one(acc: AccountCredential):
        try:
            emails = await fetch_emails(
                access_token=acc.access_token,
                include_read=payload.include_read,
                max_results=payload.max_results
            )
            for email in emails:
                email["account_email"] = acc.email
            return emails
        except Exception as e:
            # Prevent failure of one account from breaking the entire synchronization
            print(f"Error fetching emails for {acc.email}: {str(e)}")
            return []

    tasks = [fetch_one(acc) for acc in payload.accounts]
    results = await asyncio.gather(*tasks)
    
    # Flatten the list of lists
    flat_list = [email for sublist in results for email in sublist]
    
    # Sort by timestamp descending (newest first)
    flat_list.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return flat_list

@app.post("/emails/{id}/labels")
async def modify_labels(id: str, payload: ModifyLabelsRequest):
    """
    Modifies label IDs (read/unread, move to inbox/spam) for a specific email message.
    """
    return modify_message_labels(
        access_token=payload.access_token,
        msg_id=id,
        add_labels=payload.add_labels,
        remove_labels=payload.remove_labels
    )

@app.get("/health")
async def health():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy", "service": "gmail-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
