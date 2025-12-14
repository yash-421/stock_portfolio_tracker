from fastapi import APIRouter, HTTPException, status, Depends, status
from fastapi.encoders import jsonable_encoder
from app.service import get_response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Portfolio, Stock, Transaction
from app.schemas import PortfolioCreate, PortfolioOut, TransactionCreate, TransactionOut, HoldingOut, TransactionType

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/portfolios")
async def get_portfolios(db: AsyncSession = Depends(get_db)):
    """Return all portfolios."""
    try:
        portfolios = await db.execute(
            select(Portfolio)
        )
        response=get_response(
            status="success",
            data=jsonable_encoder(portfolios.scalars().all()),
            message="Portfolios retrieved successfully."
        )
        return HTTPException(status_code=status.HTTP_200_OK, detail=response)

    except Exception as e:
        print(e)
        await db.rollback()
        response= get_response(
            status="error",
            data=str(e),
            message="An error occurred while retrieving portfolios."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio_by_id(portfolio_id: int, db: AsyncSession = Depends(get_db)):
    """Return a portfolio by portfolio_id or 404."""
    try:
        portfolio = await db.execute(
            select(Portfolio).where(Portfolio.portfolio_id == portfolio_id)
        )

        portfolio = portfolio.scalars().first()
        
        if not portfolio:
            response=get_response(
                status="error",
                data=None,
                message="Portfolio not found."
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response)
        
        response= get_response(
            status="success",
            data=jsonable_encoder(portfolio),
            message="Portfolio retrieved successfully."
        )

        return HTTPException(status_code=status.HTTP_200_OK, detail=response)

    
    except Exception as e:
        await db.rollback()
        print(e)

        response= get_response(
            status="error",
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)


@router.post("/portfolios")
async def add_to_portfolio(portfolio: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    """Create a new portfolio (in-memory)."""
    try:
        new_portfolio = Portfolio(
            user_id=portfolio.user_id,
            name=portfolio.name,
            description=portfolio.description
        )
        db.add(new_portfolio)
        await db.commit()
        await db.refresh(new_portfolio)

        response= get_response(
            status="success",
            data=jsonable_encoder(new_portfolio),
            message="Portfolio created successfully."
        )

        return HTTPException(status_code=status.HTTP_201_CREATED, detail=response)

    except Exception as e:
        await db.rollback()

        response= get_response(
            status="error",
            data=str(e),
            message="An error occurred while creating the portfolio."
        )

        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)


@router.delete("/portfolios/{portfolio_id}")
async def remove_portfolio(portfolio_id: int, db=Depends(get_db)):
    """Delete a portfolio."""

    try:
        portfolio = await db.execute(
            select(Portfolio).where(Portfolio.portfolio_id == portfolio_id)
        ).scalars().first()

        if not portfolio:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio entry not found.")
        db.delete(portfolio)
        await db.commit()
        response=get_response(
            status="success",
            data=jsonable_encoder(portfolio),
            message="Portfolio deleted successfully."
        )
        return HTTPException(status_code=status.HTTP_200_OK, detail=response)
    
    except Exception as e:
        await db.rollback()
        response=get_response(
            status="error",
            data=str(e),
            message="An error occurred while deleting the portfolio."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)


@router.post("/portfolios/{portfolio_id}/transactions")
async def add_transaction(portfolio_id: int, transaction: TransactionCreate, db=Depends(get_db)):
    """
    Add a transaction to a portfolio.
    """
    try:
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

        response=get_response(
            status="success",
            data=jsonable_encoder(new_transaction),
            message="Transaction added successfully."
        )

        return HTTPException(status_code=status.HTTP_201_CREATED, detail=response)

    except Exception as e:
        await db.rollback()
        response=get_response(
            status="error",
            data=str(e),
            message="An error occurred while adding the transaction."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)

@router.get("/{portfolio_id}/holdings")
async def get_holdings(
    portfolio_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(...)
):
    """
    Compute current holdings for a portfolio by aggregating transactions.
    """

    try:


        # Check portfolio exists
        result = await db.execute(
            select(Portfolio).where(Portfolio.portfolio_id == portfolio_id)
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
                Transaction.type == TransactionType.buy
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
                Transaction.type == TransactionType.sell
            )
            .group_by(Transaction.stock_id)
            .subquery()
        )

        # Final holdings query
        holdings_stmt = (
            select(
                Stock.symbol,
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
                func.coalesce(sell_subq.c.sell_qty, 0)) > 0
            )
        )

        result = await db.execute(holdings_stmt)
        rows = result.all()

        # 5️⃣ Format response
        holdings = []
        for row in rows:
            holdings.append({
                "symbol": row.symbol,
                "net_shares": int(row.net_shares),
                "avg_price": round(row.avg_price, 2),
                "current_price": None,      # to be added later
                "realised_pl": 0.0,         # later
                "unrealised_pl": 0.0        # later
            })
        
        response=get_response(
            status="success",
            data=jsonable_encoder(holdings),
            message="Holdings retrieved successfully."
        )
        return HTTPException(status_code=status.HTTP_200_OK, detail=response)
        
    except Exception as e:
        await db.rollback()
        print(e)
        response=get_response(
            status="error",
            data=str(e),
            message="An error occurred while retrieving holdings."
        )
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response)
