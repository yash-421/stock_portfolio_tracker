from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.service import get_response, get_transaction, porfolio_exist_or_not
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Portfolio, Stock, Transaction, User
from app.schemas import Pagination, TransactionCreate, TransactionType
from app.dependencies.auth import get_current_user
from datetime import date
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/transactions", tags=["portfolios"])



@router.post("/{portfolio_id}")
async def add_transaction(
    portfolio_id: int,
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a transaction to a portfolio."""
    try:
        # Check portfolio exists and belongs to user
        exist,result = await porfolio_exist_or_not(portfolio_id,db,current_user.user_id) 
        
        if not exist:
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )
            
        if transaction.type==TransactionType.sell:
            exist,transaction_data=await get_transaction(transaction.transaction_id,db)
            if not exist:
                return get_response(
                    status_code=404,
                    message="Transaction not found",
                    data=None
                )            
            if transaction_data.balance<transaction.shares:
                
                return get_response(
                    status_code=422,
                    message="Insufficient shares to sell",
                    data=None
                )
                            
            transaction_data.balance-=transaction.shares

        # Check stock exists
        stock_result = await db.execute(
            select(Stock).where(
                Stock.stock_id == transaction.stock_id,
                Stock.enabled == True
            )
        )
        stock = stock_result.first()
        
        if not stock:
            
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Stock not found"
            )
            
        transaction_dict=dict(
            portfolio_id=portfolio_id,
            stock_id=transaction.stock_id,
            shares=transaction.shares,
            price=transaction.price,
            type=transaction.type,
            parent_id=transaction.parent_id,
            timestamp=transaction.timestamp
        )
                
        if transaction.type==TransactionType.buy:
            transaction_dict['balance'] = transaction.shares 

        new_transaction = Transaction(
            **transaction_dict
        )
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        return get_response(
            status_code_enum=status.HTTP_201_CREATED,
            data=jsonable_encoder(new_transaction),
            message="Transaction added successfully."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error adding transaction to portfolio %s", portfolio_id)
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )


@router.get('/{portfolio_id}/transactions')
async def get_transactions(pagination:Pagination,portfolio_id:int,symbol:Optional[str]=None,type:Optional[TransactionType]=None,from_date:Optional[date]=None,to_date:Optional[date]=None, current_user=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    try:
        is_exist,data = await porfolio_exist_or_not(portfolio_id,db,current_user.user_id)
        
        if not is_exist:
            return get_response(
                status_code_enum=status.HTTP_404_NOT_FOUND,
                message="Portfolio dosen't exist",
                data=None
            )
        
        transaction_query=(
            select(
                Transaction.balance,
                Transaction.shares,
                Transaction.price,
                Transaction.type,
                func.date(Transaction.timestamp).label("trade_date"),
                User.full_name,
                Stock.name,
                Stock.exchange,
                Stock.symbol
            )
            .join(
                Portfolio,
                Portfolio.portfolio_id==portfolio_id
            ).join(
                User,
                User.user_id==Portfolio.user_id
            ).join(
                Stock,
                Stock.stock_id==Transaction.stock_id
            ).filter(
                Portfolio.portfolio_id==portfolio_id,
                Portfolio.user_id==current_user.user_id
            ).order_by(
                desc(Transaction.created_at)
            )
        )
        
        if symbol:
            transaction_query=transaction_query.where(
                Stock.symbol.ilike(f"%{symbol}%")
            )
            
        if type:
            transaction_query=transaction_query.where(
                Transaction.type==type
            )
        
        if from_date:
            transaction_query=transaction_query.where(
                Transaction.timestamp>=from_date
            )
        
        if to_date:
            transaction_query=transaction_query.where(
                Transaction.timestamp<=to_date
            )
        
        if pagination:
            transaction_query=transaction_query.limit(pagination.record_count).offset((pagination.page_no-1)*pagination.record_count)
        
        transactions = await db.execute(transaction_query).all()
        
        return get_response(
            200,
            jsonable_encoder(transactions),
            "Fecthed records sucessfully"
        )
        
    except Exception as e:
        await db.rollback()
        logger.exception("Error fetching transactions for portfolio %s", portfolio_id)

        return get_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            None,
            "An error occurred while fetching transactions."
        )
        
  
@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id:int,
    current_user=Depends(get_current_user),
    db:AsyncSession=Depends(get_db)
):
    try:
        query = (
            select(Transaction)
            .join(Portfolio, Portfolio.portfolio_id == Transaction.portfolio_id)
            .where(
                Transaction.transaction_id == transaction_id,
                Portfolio.user_id == current_user.user_id,
                Transaction.enabled == True
            )
        )
        result = await db.execute(query)

        transaction = result.scalar_one_or_none()
        
        if not transaction:
            
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Transaction not found"
            )
        
        transaction.enabled=False
        
        await db.commit()
        await db.refresh(transaction)
        
        return get_response(
            200,
            transaction,
            "Deleted sucessfully"
        )
         

    except Exception as e:
        await db.rollback()
        logger.exception("Error deleting transaction %s", transaction_id)
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )

     
