from pydantic import BaseModel

class RegisterSchema(BaseModel):
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class VerifyMFASchema(BaseModel):
    email: str
    code: str