import enum
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import String,Enum, ForeignKey, Float
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    enabled: Mapped[bool] = mapped_column(default=True)

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.user_id} email={self.email}>"


class TransactionType(enum.Enum):
    buy = "buy"
    sell = "sell"

class ExchangeType(enum.Enum):
    bse = "bse"
    nse = "nse"


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)

    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.stock_id", ondelete="CASCADE"),
        index=True, 
        nullable=False
    )
    shares: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.transaction_id} stock_id={self.stock_id} "
            f"type={self.type.value} shares={self.shares}>"
        )

class Portfolio(Base):
    __tablename__ = "portfolios"

    portfolio_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Portfolio id={self.portfolio_id} name={self.name}>"

class Stock(Base):
    __tablename__ = "stocks"

    stock_id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[ExchangeType] = mapped_column(
        Enum(ExchangeType, name="exchange_type"),
        nullable=False
    )
    sector: Mapped[str | None] = mapped_column(String(50))

    def __repr__(self):
        return f"<Stock symbol={self.symbol} name={self.name}  >"
