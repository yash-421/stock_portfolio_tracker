from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from app.service import get_response
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.connection import get_db
from app.models import Portfolio, User
from app.schemas import Pagination, PortfolioCreate
from app.dependencies.auth import get_current_user
import logging

logger = logging.getLogger(__name__)


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
        portfolio_count = await db.scalar(select(func.count()).select_from(portfolios.subquery()))
        portfolios_res = await db.execute(portfolios.limit(pagination.record_count).offset((pagination.page_no-1)*pagination.record_count))

        data = dict(
            data=jsonable_encoder(portfolios_res.scalars().all()),
            total_records=jsonable_encoder(portfolio_count),
            page_no=pagination.page_no,
            record_count=pagination.record_count,
        )
        
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=data,
            message="Portfolios retrieved successfully."
        )

    except Exception as e:
        await db.rollback()
        logger.exception("Error retrieving portfolios for user %s", getattr(current_user, 'user_id', None))

        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving portfolios."
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
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )

        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(portfolio),
            message="Portfolio retrieved successfully."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error retrieving portfolio %s for user %s", portfolio_id, getattr(current_user, 'user_id', None))

        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )


@router.post("/")
async def add_portfolio(
    portfolio: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio."""
    try:
        # Validate user owns this portfolio creation request
        if portfolio.user_id != current_user.user_id:
            return get_response(
                status.HTTP_403_FORBIDDEN,
                None,
                "You do not have permission to create a portfolio for this user."
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



    except Exception as e:
        await db.rollback()
        logger.exception("Error creating portfolio for user %s", getattr(current_user, 'user_id', None))
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
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
            return get_response(
                status.HTTP_404_NOT_FOUND,
                None,
                "Portfolio not found"
            )
        
        db.delete(portfolio)
        await db.commit()
        return get_response(
            status_code_enum=status.HTTP_200_OK,
            data=jsonable_encoder(portfolio),
            message="Portfolio deleted successfully."
        )

    except Exception as e:
        await db.rollback()
        logger.exception("Error deleting portfolio %s for user %s", portfolio_id, getattr(current_user, 'user_id', None))
        return get_response(
            status_code_enum=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data=str(e),
            message="An error occurred while retrieving the portfolio."
        )



