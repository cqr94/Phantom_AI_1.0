from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from agent.models import Role
from routers.apt_dashboard import router as dashboard_router

from agent.db import engine, Base, get_db
from agent.models import User
from agent.schemas import (
    RegisterSchema,
    LoginSchema,
    VerifyMFASchema,
)
from agent.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_totp,
)
#from dashboard.apt_dashboard import router as dashboard_router

#from graph.graph import router as graph_killchain_router
from agent.file_upload import router as pcap_router
#from best_agent.groq_api.chat_only_api import router as agent_threat_hunter_router

from best_agent.agent_api import router as agent_threat_hunter_router
#from best_agent.groq_api import router as  agent_threat_hunter_router
from routers import auth, admin
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
app = FastAPI(title="APT·HUNT v3 — Threat Intelligence & Pentest Platform", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(pcap_router)
app.include_router(dashboard_router)
#app.include_router(chat_router)
#app.include_router(models_router)
app.include_router(agent_threat_hunter_router)
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    admin.router,
    tags=["admin"],
)






@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


import pyotp
import qrcode
import io
import base64

from fastapi import HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/register")
async def register(
    data: RegisterSchema,
    db: AsyncSession = Depends(get_db)
):
    # existing user check
    existing = await db.execute(
        select(User).where(User.email == data.email)
    )

    if existing.scalar():
        raise HTTPException(400, "User already exists")

    # default role
    role_result = await db.execute(
        select(Role).where(Role.name == "user")
    )

    default_role = role_result.scalar()

    if not default_role:
        default_role = Role(name="user")
        db.add(default_role)
        await db.flush()

    # MFA secret
    mfa_secret = pyotp.random_base32()

    # create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        mfa_secret=mfa_secret,
        mfa_enabled=True,
        role_id=default_role.id,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # OTP URI
    otp_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
        name=user.email,
        issuer_name="PHANTOM AI"
    )

    # generate QR image
    qr = qrcode.make(otp_uri)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode()

    # IMPORTANT:
    # frontend expects qr_code_base64
    return {
        "success": True,
        "user_id": user.id,
        "email": user.email,
        "mfa_enabled": True,
        "qr_code_base64": qr_base64,
        "manual_code": mfa_secret,
    }

@app.post("/login")
async def login(
    data: LoginSchema,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(User).where(User.email == data.email)
    )

    user = result.scalar()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(401, "Invalid credentials")

    if user.mfa_enabled:
        return {
            "mfa_required": True,
            "message": "Verify MFA code",
        }

    token = create_access_token(
        {"sub": user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }




@app.post("/verify-mfa")
async def verify_mfa(
    data: VerifyMFASchema,
    db: AsyncSession = Depends(get_db),
):

    result = await db.execute(
        select(User).where(User.email == data.email)
    )

    user = result.scalar()

    if not user:
        raise HTTPException(404, "User not found")

    totp = get_totp(user.mfa_secret)

    valid = totp.verify(
        data.code,
        valid_window=1,
    )

    if not valid:
        raise HTTPException(401, "Invalid MFA code")

    token = create_access_token(
        {"sub": user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")