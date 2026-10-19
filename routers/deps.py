from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from agent.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def require_role(required_role: str):

    async def checker(
        token: str = Depends(oauth2_scheme)
    ):

        payload = decode_token(token)

        if not payload:
            raise HTTPException(401)

        role = payload.get("role")

        if role != required_role:
            raise HTTPException(403)

        return payload

    return checker