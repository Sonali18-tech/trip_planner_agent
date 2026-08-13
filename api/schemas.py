from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class TripRequest(BaseModel):
    destination: str
    num_days: int = Field(gt=0, le=14)
    start_date: Optional[date] = None  # if omitted, defaults to today
    budget: float = Field(gt=0)
    currency: str = "INR"
    travel_style: str = "cultural"
    group_size: int = 1
    interests: list = []
    origin: str = "a major nearby city"


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
