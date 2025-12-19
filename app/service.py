from typing import Any
from fastapi.responses import JSONResponse
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Portfolio



def get_response(status_code_enum: int, data: Any, message: str) -> dict:
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

def portfolio_summary():
    pass

async def porfolio_exist_or_not(portfolio_id:int,db:AsyncSession):
    try:
        portfolio_query= await db.execute(
            select(Portfolio).where(Portfolio.portfolio_id==portfolio_id)
        )
        portfolio=await portfolio_query.scalar_one_or_none()
        
        if portfolio:
            return True,portfolio
        return False,None
    except Exception as e:
        print(e)
        return False,None
        