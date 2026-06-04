import httpx
from fastapi import APIRouter, HTTPException, Query
from config.settings import settings

router = APIRouter()

@router.get("")
async def get_meetings(user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MEETING_SERVICE_URL}/meetings",
                params={"user_id": user_id},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.get("/pending")
async def get_pending_meetings(user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MEETING_SERVICE_URL}/meetings/pending",
                params={"user_id": user_id},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.post("/{id}/confirm")
async def confirm_meeting(id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.MEETING_SERVICE_URL}/meetings/{id}/confirm",
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.post("/{id}/dismiss")
async def dismiss_meeting(id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.MEETING_SERVICE_URL}/meetings/{id}/dismiss",
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.post("/{id}/accept-update")
async def accept_update(id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.MEETING_SERVICE_URL}/meetings/{id}/accept-update",
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.post("/{id}/remove")
async def remove_meeting(id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.MEETING_SERVICE_URL}/meetings/{id}/remove",
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.get("/upcoming")
async def get_upcoming_meetings(user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MEETING_SERVICE_URL}/meetings/upcoming",
                params={"user_id": user_id},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")

@router.get("/dashboard")
async def get_dashboard(user_id: str = Query(...)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.MEETING_SERVICE_URL}/meetings/dashboard",
                params={"user_id": user_id},
                timeout=15.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Failed to communicate with Meeting Service: {str(e)}")
