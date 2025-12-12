from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str
    
class UserCreate(UserBase):
    password: str

class PortfolioCreate(BaseModel):
    symbol: str
    shares: int

class TransactionCreate(BaseModel):
    type: str  # 'buy' or 'sell'
    shares: int

class HoldingOut(BaseModel):
    symbol: str
    shares: int

class PriceOut(BaseModel):
    symbol: str
    price: float