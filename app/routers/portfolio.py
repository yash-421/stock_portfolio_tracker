from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas import PortfolioCreate, PortfolioOut, TransactionCreate, TransactionOut, HoldingOut

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# In-memory sample data (replace with DB calls later)
SAMPLE_PORTFOLIOS = [
    {"id": 1, "name": "Long-term", "symbol": "AAPL", "shares": 50},
    {"id": 2, "name": "Short-term", "symbol": "GOOGL", "shares": 10},
    {"id": 3, "name": "Dividend", "symbol": "MSFT", "shares": 20},
]


@router.get("/portfolios", response_model=List[dict])
async def get_portfolios():
    """Return all portfolios (in-memory)."""
    return SAMPLE_PORTFOLIOS


@router.get("/portfolios/{id}", response_model=dict)
async def get_portfolio_by_id(id: int):
    """Return a portfolio by id or 404."""
    for p in SAMPLE_PORTFOLIOS:
        if p["id"] == id:
            return p
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio entry not found.")


@router.post(
    "/portfolios",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def add_to_portfolio(portfolio: PortfolioCreate):
    """Create a new portfolio (in-memory)."""
    if getattr(portfolio, "shares", 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of shares must be positive.",
        )
    # Create a new id (simple in-memory approach)
    new_id = max([p["id"] for p in SAMPLE_PORTFOLIOS], default=0) + 1
    new_portfolio = {
        "id": new_id,
        "name": getattr(portfolio, "name", f"portfolio-{new_id}"),
        "symbol": getattr(portfolio, "symbol", ""),
        "shares": getattr(portfolio, "shares", 0),
    }
    SAMPLE_PORTFOLIOS.append(new_portfolio)
    return {"message": f"Added {new_portfolio['shares']} shares of {new_portfolio['symbol']} to portfolio.", "portfolio": new_portfolio}


@router.delete("/portfolios/{id}", status_code=status.HTTP_200_OK)
async def remove_from_portfolio(id: int):
    """Delete a portfolio (in-memory)."""
    for i, p in enumerate(SAMPLE_PORTFOLIOS):
        if p["id"] == id:
            SAMPLE_PORTFOLIOS.pop(i)
            return {"message": f"Removed portfolio entry {id}."}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio entry not found.")


@router.post("/portfolios/{id}/transactions", status_code=status.HTTP_201_CREATED)
async def add_transaction(id: int, transaction: TransactionCreate):
    """
    Record a buy/sell transaction for the given portfolio id.
    Validation is basic here — replace with DB logic and business rules later.
    """
    # Ensure portfolio exists
    portfolio = next((p for p in SAMPLE_PORTFOLIOS if p["id"] == id), None)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio entry not found.")

    if transaction.shares <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of shares must be positive.")

    tx_type = transaction.type.lower()
    if tx_type not in ("buy", "sell"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction type must be 'buy' or 'sell'.")

    # In-memory: just return a success message (persist to DB later)
    return {
        "message": f"Recorded {tx_type} of {transaction.shares} shares for portfolio entry {id}.",
        "transaction": {
            "portfolio_id": id,
            "symbol": getattr(transaction, "symbol", portfolio.get("symbol")),
            "shares": transaction.shares,
            "price": getattr(transaction, "price", None),
            "type": tx_type,
        },
    }


@router.get("/portfolios/{id}/holdings", response_model=List[dict])
async def get_holdings(id: int):
    """
    Compute holdings for a portfolio.
    Right now returns a sample response — replace with actual aggregation of transactions from DB.
    """
    portfolio = next((p for p in SAMPLE_PORTFOLIOS if p["id"] == id), None)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio entry not found.")

    # Sample computed holdings (replace with real calculation)
    holdings = [
        {"symbol": portfolio["symbol"], "quantity": portfolio["shares"], "avg_price": 150.0, "current_price": 175.0},
    ]
    return holdings
