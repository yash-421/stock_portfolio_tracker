from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.service import get_response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Stock
from app.schemas import StockCreate
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["portfolios"])





@router.get("/")
async def get_stocks(
    stock_name:str=None,
    current_user=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    try:
        query=(
            select(Stock)
        )
        if stock_name :
            query=query.where(or_(
                Stock.name.ilike(f"%{stock_name}%"),
                Stock.symbol.ilike(f"%{stock_name}%"),
            ))

        stock_list=await db.execute(query)
        stocks=stock_list.all()
        
        return get_response(
            200,
            jsonable_encoder(stocks),
            "Stock list fetched."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error retrieving stocks")
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving stocks."
        )
        
@router.post("/")
async def add_stock(stock:StockCreate,current_user=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    try:
        stock_entry=Stock(
            symbol=stock.symbol,
            name=stock.name,
            exchange=stock.exchange
        )
        db.add(stock_entry)
        await db.commit()
        await db.refresh(stock_entry)
        
        return get_response(
            200,
            stock_entry,
            "Added stock successfully"
        )
    
    except Exception as e:
        await db.rollback()
        logger.exception("Error adding stock %s", getattr(stock, 'symbol', None))
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )
