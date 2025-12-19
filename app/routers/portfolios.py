from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.service import format_holdings, get_response, porfolio_exist_or_not
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Portfolio, Stock, Transaction, User
from app.schemas import Pagination, PortfolioCreate, PortfolioOut, TransactionCreate, TransactionOut, HoldingOut, TransactionType
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


@router.get("/")
async def get_portfolios(
    pagination:Pagination=Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Return all portfolios for the current user."""
    try:
        portfolios=(
             select(Portfolio).where(
                Portfolio.user_id == current_user.user_id,
                Portfolio.enabled == True
            ).order_by(desc(Portfolio.created_at))
        )
        portfolio_count=await db.scalar(select(func.count()).select_from(portfolios.subquery()))
        portfolios=await db.execute(portfolios.limit(pagination.record_count).offset((pagination.page_no-1)*pagination.record_count))
        
        
        data=dict(
            data=jsonable_encoder(portfolios.scalars().all()),
            total_records=jsonable_encoder(portfolio_count.scalar_one_or_none()),
            page_no=pagination.page_no,
            record_count=pagination.record_count,
        )
        
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=data,
            message="Portfolios retrieved successfully."
        )

    except Exception as e:
        print(e)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while retrieving portfolios."
            }
        )


@router.get("/{portfolio_id}")
async def get_portfolio_by_id(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Return a portfolio by portfolio_id or 404."""
    try:
        portfolio = await db.execute(
            select(Portfolio).where(
                Portfolio.portfolio_id == portfolio_id,
                Portfolio.user_id == current_user.user_id,
                Portfolio.enabled == True
            )
        )

        portfolio = portfolio.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "Portfolio not found."
                }
            )
        
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(portfolio),
            message="Portfolio retrieved successfully."
        )


    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while retrieving the portfolio."
            }
        )


@router.post("/create_porfolio")
async def add_portfolio(
    portfolio: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio."""
    try:
        # Validate user owns this portfolio creation request
        if portfolio.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create portfolio for another user"
            )

        new_portfolio = Portfolio(
            user_id=portfolio.user_id,
            name=portfolio.name,
            description=portfolio.description
        )
        db.add(new_portfolio)
        await db.commit()
        await db.refresh(new_portfolio)

        return get_response(
            status_code_enum=status.HTTP_201_CREATED,
            data=jsonable_encoder(new_portfolio),
            message="Portfolio created successfully."
        )


    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while creating the portfolio."
            }
        )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a portfolio."""

    try:
        portfolio = await db.execute(
            select(Portfolio).where(
                Portfolio.portfolio_id == portfolio_id,
                Portfolio.user_id == current_user.user_id,
                Portfolio.enabled == True
            )
        )
        portfolio = portfolio.scalars().first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found."
            )
        
        db.delete(portfolio)
        await db.commit()
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(portfolio),
            message="Portfolio deleted successfully."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while deleting the portfolio."
            }
        )


@router.post("/{portfolio_id}/transactions")
async def add_transaction(
    portfolio_id: int,
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a transaction to a portfolio."""
    try:
        # Check portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.portfolio_id == portfolio_id,
                Portfolio.user_id == current_user.user_id,
                Portfolio.enabled == True
            )
        )
        portfolio = result.scalars().first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Check stock exists
        stock_result = await db.execute(
            select(Stock).where(
                Stock.stock_id == transaction.stock_id,
                Stock.enabled == True
            )
        )
        stock = stock_result.scalars.first()
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stock not found"
            )
        
        new_transaction = Transaction(
            portfolio_id=portfolio_id,
            stock_id=transaction.stock_id,
            shares=transaction.shares,
            price=transaction.price,
            type=transaction.type,
            timestamp=transaction.timestamp
        )
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        return get_response(
            status_code_enum=status.HTTP_201_CREATED,
            data=jsonable_encoder(new_transaction),
            message="Transaction added successfully."
        )
    except HTTPException:
        raise
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while adding the transaction."
            }
        )


@router.get("/{portfolio_id}/holdings")
async def get_holdings(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compute current holdings for a portfolio by aggregating transactions.
    """

    try:
        # Check portfolio exists and belongs to user
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.portfolio_id == portfolio_id,
                Portfolio.user_id == current_user.user_id,
                Portfolio.enabled == True
            )
        )
        portfolio = result.scalars().first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        # BUY aggregation (quantity + value)
        buy_subq = (
            select(
                Transaction.stock_id,
                func.sum(Transaction.shares).label("buy_qty"),
                func.sum(Transaction.shares * Transaction.price).label("buy_value")
            )
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == TransactionType.buy,
                Transaction.enabled == True
            )
            .group_by(Transaction.stock_id)
            .subquery()
        )

        # SELL aggregation (quantity only)
        sell_subq = (
            select(
                Transaction.stock_id,
                func.sum(Transaction.shares).label("sell_qty")
            )
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == TransactionType.sell,
                Transaction.enabled == True
            )
            .group_by(Transaction.stock_id)
            .subquery()
        )

        # Final holdings query
        holdings_stmt = (
            select(
                Stock.symbol,
                Stock.name,
                (
                    func.coalesce(buy_subq.c.buy_qty, 0) -
                    func.coalesce(sell_subq.c.sell_qty, 0)
                ).label("net_shares"),
                (
                    buy_subq.c.buy_value /
                    func.nullif(buy_subq.c.buy_qty, 0)
                ).label("avg_price")
            )
            .join(buy_subq, buy_subq.c.stock_id == Stock.stock_id)
            .outerjoin(sell_subq, sell_subq.c.stock_id == Stock.stock_id)
            .where(
                (func.coalesce(buy_subq.c.buy_qty, 0) -
                func.coalesce(sell_subq.c.sell_qty, 0)) > 0,
                Stock.enabled == True
            )
        ).order_by(desc(Transaction.transaction_id))

        result = await db.execute(holdings_stmt)
        rows = result.all()

        # Format response
        holdings = format_holdings(rows)
        
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(holdings),
            message="Holdings retrieved successfully."
        )
    except HTTPException:
        raise        
    except Exception as e:
        await db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": str(e),
                "message": "An error occurred while retrieving holdings."
            }
        )


# ✅ GET /{portfolio_id}/summary

# @router.get('/{portfolio_id}/summary')
# async def portfolio_summary(
#     portfolio_id:int,
#     db:AsyncSession=Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     try:
#         found,portfolio=porfolio_exist_or_not(portfolio_id,db)
#         if not found:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Portfolio not found"
#             )
        
        

                        
        
    
#     except HTTPException:
#         raise
#     except Exception as e :
#         await db.rollback()
#         print(e)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={
#                 "status": "error",
#                 "data": str(e),
#                 "message": "An error occurred while retrieving holdings."
#             }
#         )




# ✅ GET /{portfolio_id}/transactions

# ✅ PATCH /transactions/{id}

# ✅ GET /stocks

# ✅ GET /{portfolio_id}/performance