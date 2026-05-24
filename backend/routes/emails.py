from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.gmail_service import fetch_unread_emails

router = APIRouter()
security = HTTPBearer()

@router.get("/unread")
async def get_unread_emails(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fetches the unread emails from the authenticated user's Gmail account.
    Expects the Google OAuth access token as a Bearer token in the Authorization header.
    """
    token = credentials.credentials
    emails = await fetch_unread_emails(access_token=token)
    return emails
