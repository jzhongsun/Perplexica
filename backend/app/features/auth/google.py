from typing import Optional
import httpx
from fastapi import HTTPException, status
from app.core.config import get_settings

settings = get_settings()

class GoogleOAuth2:
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.scope = "openid email profile"

    def get_authorization_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": self.scope,
            "redirect_uri": self.redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
        }
        from urllib.parse import urlencode
        return f"{self.GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def get_access_token(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token from Google"
                )
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google"
                )
            return response.json() 