from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent.db import get_db
from agent.models import User
from agent.auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from agent.redis_client import redis_client

router = APIRouter()


@router.post("/login")
async def login(data: dict, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(User).where(
            User.email == data["email"]
        )
    )

    user = result.scalar()

    if not user:
        raise HTTPException(401)

    if not verify_password(
        data["password"],
        user.password_hash,
    ):
        raise HTTPException(401)

    # MFA would happen here

    access_token = create_access_token(user)

    refresh_token = create_refresh_token()

    await redis_client.setex(
        f"refresh:{refresh_token}",
        60 * 60 * 24 * 7,
        str(user.id),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@router.post("/refresh")
async def refresh(data: dict):

    refresh_token = data["refresh_token"]

    user_id = await redis_client.get(
        f"refresh:{refresh_token}"
    )

    if not user_id:
        raise HTTPException(401)

    # lookup user from postgres
    # issue new access token

    return {
        "access_token": "NEW_TOKEN"
    }

@router.post("/logout")
async def logout(data: dict):

    refresh_token = data["refresh_token"]

    await redis_client.delete(
        f"refresh:{refresh_token}"
    )

    return {
        "message": "Logged out"
    }