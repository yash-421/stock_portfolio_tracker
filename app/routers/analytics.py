
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.service import format_holdings, get_portfolio_performance, get_response, porfolio_exist_or_not, portfolio_summary_data
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Portfolio, Stock, Transaction, User, TransactionType
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/analytics", tags=["portfolios"])


@router.get("/{portfolio_id}/holdings")
async def get_holdings(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compute current holdings for a portfolio by aggregating transactions.
    """

    try:
        
        exist,portfolio=await porfolio_exist_or_not(portfolio_id,db,current_user.user_id)


        if not exist:
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )

        query=(
            select(
                Stock.symbol,
                Stock.name,
                func.sum(Transaction.balance).label("net_shares"),
                func.avg(Transaction.price).label("avg_price")
            ).join(
                Stock,
                Stock.stock_id==Transaction.stock_id
            ).where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.balance > 0,
                Transaction.type == TransactionType.buy,
                Transaction.enabled == True,
            ).group_by(
                Stock.symbol,
                Stock.name,
            )
        )
        
        result = await db.execute(query)
        rows = result.all()

        # Format response
        holdings = format_holdings(rows)
        
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(holdings),
            message="Holdings retrieved successfully."
        )
       
    except Exception as e:
        await db.rollback()
        logger.exception("Error retrieving holdings for portfolio %s", portfolio_id)
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=None,
            message="An error occurred while retrieving the portfolio."
        )


@router.get('/{portfolio_id}/summary')
async def portfolio_summary(
    portfolio_id:int,
    db:AsyncSession=Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        found,portfolio= await porfolio_exist_or_not(portfolio_id,db,current_user.user_id)
        
        if not found:
            
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )
            
        
        found_data, performance_data = await portfolio_summary_data(portfolio_id,db)
        if not found_data:
            return get_response(status.HTTP_404_NOT_FOUND, None, "No summary data available")

        return get_response(200, performance_data, "Portfolio summary")
    except Exception as e :
        await db.rollback()
        logger.exception("Error building portfolio summary for %s", portfolio_id)
        return get_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            None,
            "An error occurred while retrieving holdings."
        )

@router.get("/{portfolio_id}/performance")
async def get_performance(
    portfolio_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        is_exist, portfolio = await porfolio_exist_or_not(
            portfolio_id, db, current_user.user_id
        )

        if not is_exist:
            
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )

        data_found,performance = await get_portfolio_performance(portfolio_id,db)
        
        if not data_found:
            return get_response(
                status.HTTP_406_NOT_ACCEPTABLE,
                None,
                "Portfolio not found"
            )        

        return get_response(
            200,
            jsonable_encoder(performance),
            "Portfolio value per day",
        )

    except Exception as e:
        logger.exception("Performance error for portfolio %s", portfolio_id)
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=None,
            message="An error occurred while retrieving the portfolio."
        )

