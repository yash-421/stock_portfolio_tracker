# app/schemas.py
from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, conint, PositiveFloat
from datetime import datetime


class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"


# -----------------------
# User schemas
# -----------------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)



# -----------------------
# Portfolio schemas
# -----------------------
class PortfolioCreate(BaseModel):
    user_id: int  # can be set by server
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PortfolioOut(BaseModel):
    portfolio_id: int
    name: str
    description: Optional[str]
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------
# Transaction schemas
# -----------------------
class TransactionCreate(BaseModel):
    stock_id: int
    shares: conint(strict=True, gt=0)  # positive integer shares
    price: PositiveFloat  # price per share, > 0
    type: TransactionType
    timestamp: Optional[datetime] = None  # server can fill if not provided
    note: Optional[str] = None


class TransactionOut(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    shares: int
    price: float
    type: TransactionType
    timestamp: datetime
    note: Optional[str]

    model_config = ConfigDict(from_attributes=True)



# -----------------------
# Holding / Valuation schemas
# -----------------------
class HoldingOut(BaseModel):
    symbol: str
    quantity: int
    avg_price: float
    current_price: Optional[float] = None
    realised_pl: Optional[float] = 0.0
    unrealised_pl: Optional[float] = 0.0

    model_config = ConfigDict(from_attributes=True)



# -----------------------
# Price schema
# -----------------------
class PriceOut(BaseModel):
    symbol: str
    timestamp: datetime
    price: float

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None