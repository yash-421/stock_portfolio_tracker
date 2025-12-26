from typing import Any
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy import case, desc, func, select, alias
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models import Portfolio, StockPriceHistory, Transaction, TransactionType, User

logger = logging.getLogger(__name__)



def get_response(status_code_enum: int=200, data: Any=None, message: str="Successfully") -> dict:
    """Helper function to format API responses."""
    
    return JSONResponse(
        status_code=status_code_enum,
        content={
            "status": "success" if status_code_enum < 400 else "error",
            "data": data,
            "message": message
        }
    )


def calculate_portfolio_value(transactions: list[dict]) -> float:
    """Calculate the total value of a portfolio based on transactions."""
    total_value = 0.0
    for transaction in transactions:
        if transaction["type"] == "buy":
            total_value += transaction["shares"] * transaction["price"]
        elif transaction["type"] == "sell":
            total_value -= transaction["shares"] * transaction["price"]
    return total_value


def validate_portfolio_ownership(user_id: int, portfolio_user_id: int) -> bool:
    """Validate if the user owns the portfolio."""
    return user_id == portfolio_user_id

def format_holdings(holdings) -> list[dict]:
    """Format holdings data from SQLAlchemy rows for API response."""
    formatted_holdings = []
    for holding in holdings:
        # Handle SQLAlchemy Row objects
        if hasattr(holding, '_mapping'):
            holding_dict = holding._mapping
        else:
            holding_dict = holding
        
        formatted_holdings.append({
            "symbol": holding_dict.get("symbol") or holding_dict[0],
            "name": holding_dict.get("name") or holding_dict[1],
            "quantity": holding_dict.get("net_shares") or holding_dict.get("quantity"),
            "average_price": holding_dict.get("avg_price") or holding_dict.get("average_price")
        })
    return formatted_holdings

async def portfolio_summary_data(portfolio_id, db: AsyncSession):
    try:
        latest_price_query=(
            select(
                StockPriceHistory.stock_id,
                StockPriceHistory.price_date,
                StockPriceHistory.adjusted_close,
                func.row_number().over(
                    partition_by=StockPriceHistory.stock_id,
                    order_by=desc(StockPriceHistory.price_date)
                ).label("latest_price")
            )
        ).subquery()
        buy_stmt = (
            select(
                Transaction.stock_id,
                func.coalesce(latest_price_query.c.adjusted_close,func.max(Transaction.price)).label("latest_price"),
                func.sum(Transaction.balance).label("holding_qty"),
                func.sum(Transaction.balance * Transaction.price).label("invested_value"),
            ).outerjoin(
                latest_price_query,
                latest_price_query.c.stock_id == Transaction.stock_id,
                latest_price_query.c.latest_price == 1
            )
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == TransactionType.buy,
                Transaction.balance > 0,
                Transaction.enabled == True,
            )
            .group_by(Transaction.stock_id)
        )

        rows = (await db.execute(buy_stmt)).all()

        total_invested = 0.0
        portfolio_value = 0.0
        unrealised_pnl = 0.0
        total_positions = 0

        for r in rows:
            current_price = r.latest_price if r.latest_price else 0.0
            total_positions += 1
            total_invested += r.invested_value
            portfolio_value += r.holding_qty * current_price
            unrealised_pnl += (current_price * r.holding_qty) - r.invested_value

        # Realised PnL
        Buy = alias(Transaction)

        realised_stmt = (
            select(
                func.coalesce(
                    func.sum((Transaction.price - Buy.price) * Transaction.shares),
                    0
                )
            )
            .join(Buy, Transaction.parent_id == Buy.transaction_id)
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == TransactionType.sell,
                Transaction.enabled == True,
            )
        )

        realised_pnl = (await db.execute(realised_stmt)).scalar()

        return True, {
            "portfolio_value": round(portfolio_value, 2),
            "total_invested": round(total_invested, 2),
            "unrealised_pnl": round(unrealised_pnl, 2),
            "realised_pnl": round(realised_pnl, 2),
            "total_positions": total_positions,
        }

    except Exception as e:
        logger.exception("Error while calculating portfolio summary for %s", portfolio_id)
        return False, None

async def porfolio_exist(portfolio_id:int, db:AsyncSession,user_id :int=None):
    try:
        stmt = select(Portfolio).where(Portfolio.portfolio_id == portfolio_id)
        if user_id:
            stmt = stmt.where(Portfolio.user_id == user_id)

        result = await db.execute(stmt)
        portfolio = result.scalars().first()

        if portfolio:
            return True, portfolio
        return False, None
    except Exception as e:
        logger.exception("Error checking portfolio existence")
        return False, None

async def get_portfolio_performance(portfolio_id:int,db:AsyncSession):
    try:
                # 1️⃣ Convert BUY / SELL → +shares / -shares
        signed_qty = case(
            (Transaction.type == TransactionType.buy, Transaction.shares),
            else_=-Transaction.shares
        )

        # 2️⃣ Daily cumulative holdings per stock
        holdings_subquery = (
            select(
                Transaction.stock_id,
                func.date(Transaction.timestamp).label("trade_date"),
                func.sum(signed_qty)
                .over(
                    partition_by=Transaction.stock_id,
                    order_by=func.date(Transaction.timestamp)
                )
                .label("cum_shares")
            )
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.enabled == True
            )
            .subquery()
        )

        # 3️⃣ Join holdings with stored daily prices
        stmt = (
            select(
                StockPriceHistory.price_date.label("trade_date"),
                func.sum(
                    holdings_subquery.c.cum_shares
                    * StockPriceHistory.adjusted_close
                ).label("portfolio_value")
            )
            .join(
                holdings_subquery,
                holdings_subquery.c.stock_id == StockPriceHistory.stock_id
            )
            .where(
                StockPriceHistory.price_date >= holdings_subquery.c.trade_date
            )
            .group_by(StockPriceHistory.price_date)
            .order_by(StockPriceHistory.price_date)
        )

        result = await db.execute(stmt)
        performance = result.all()
        
        return True,performance
    except Exception as e:
        return False, None

async def get_transaction(transaction_id:int,db:AsyncSession):
    try:
        
        query=(
            select(Transaction)
            .where(
                Transaction.transaction_id==transaction_id,
                Transaction.type==TransactionType.buy
            ).with_for_update()
        )
        
        result=await db.execute(query)
        transaction = result.scalars().first()

        return True, transaction
        
    except Exception as e:
        logger.exception("Error fetching transaction %s", transaction_id)
        return False, None
    