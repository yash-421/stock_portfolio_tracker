import enum
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import BigInteger, Date, Numeric, String,Enum, ForeignKey, Float, Text, UniqueConstraint
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
    balance:Mapped[int] =mapped_column(nullable=False,default=0)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    parent_id : Mapped[int]=mapped_column(
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        nullable=True
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
    
    __table_args__=(
        UniqueConstraint("symbol", "exchange", name="uq_stock_entry"),
    )

    

    def __repr__(self):
        return f"<Stock symbol={self.symbol} name={self.name}  >"

class StockPriceHistory(Base):
    __tablename__ = "stock_price_history"
    stock_price_history_id:Mapped[int]=mapped_column(primary_key=True)
    stock_id:Mapped[int]=mapped_column(
        ForeignKey("stocks.stock_id", ondelete="CASCADE"),
        index=True, 
        nullable=False
    )
    price_date:Mapped[datetime.date]=mapped_column(
        Date,
        index=True,
        nullable=False
    )
    open_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    high_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    low_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    close_price: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    adjusted_close: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False,default="yahoo")

    __table_args__ = (
        UniqueConstraint("stock_id", "price_date", name="uq_stock_date"),
    )
    
    def __repr__(self):
        return f"<StockPriceHistory stock_id={self.stock_id} date={self.price_date}>"


