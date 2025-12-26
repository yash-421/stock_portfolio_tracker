# app/schemas.py
from __future__ import annotations
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, conint, PositiveFloat
from datetime import datetime

from app.models import ExchangeType


class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"


# -----------------------
# User schemas
# -----------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# -----------------------
# Portfolio schemas
# -----------------------
class PortfolioCreate(BaseModel):
    user_id: int
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
    shares: conint(strict=True, gt=0)
    price: PositiveFloat
    type: TransactionType
    timestamp: Optional[datetime] = datetime.utcnow()
    parent_id:Optional[int]=None


class TransactionOut(BaseModel):
    transaction_id: int
    portfolio_id: int
    stock_id: int
    shares: int
    price: float
    type: TransactionType
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------
# Stock schemas
# -----------------------
class StockOut(BaseModel):
    stock_id: int
    symbol: str
    name: str
    exchange: str
    sector: Optional[str]

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

class Pagination(BaseModel):
    page_no: int = Field(1, ge=1)
    record_count: int = Field(15, ge=1, le=50)

class StockCreate(BaseModel):
    symbol: str
    name: str
    exchange: ExchangeType
    sector: Optional[str] = None