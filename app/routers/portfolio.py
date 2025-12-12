from http.client import HTTPResponse
from fastapi import APIRouter
from schemas import  PortfolioCreate, TransactionCreate
router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/portfolios")
async def get_portfolio():
    return list(
        {"symbol": "AAPL", "shares": 50},
        {"symbol": "GOOGL", "shares": 10},
        {"symbol": "MSFT", "shares": 20},
    )

@router.get("/portfolios/{id}")
async def get_portfolio_by_id(id: int):
    try:
        if id != 1:
            return HTTPResponse(status_code=404, content={"error": "Portfolio entry not found."})
        
        
    except Exception as e:
        message = str(e)
        return HTTPResponse(status_code=500, content={"error": message})
    
    return {"id": id, "symbol": "AAPL", "shares": 50}

@router.post("/portfolios")
async def add_to_portfolio(portfolio: PortfolioCreate):
    try:
        if portfolio.shares <= 0:
            return HTTPResponse(status_code=400, content={"error": "Number of shares must be positive."})
        
        return HTTPResponse(status_code=201, content={"message": f"Added {portfolio.shares} shares of {portfolio.symbol} to portfolio."})
    except Exception as e:
        message = str(e)
        return HTTPResponse(status_code=500, content={"error": message})

@router.delete("/portfolios/{id}")
async def remove_from_portfolio(id: int):
    try:
        if id != 1:
            return HTTPResponse(status_code=404, content={"error": "Portfolio entry not found."})
        
        return HTTPResponse(status_code=200, content={"message": f"Removed portfolio entry {id}."})
    except Exception as e:
        message = str(e)
        return HTTPResponse(status_code=500, content={"error": message})
    
    

@router.post("/portfolios/{id}/transactions")
async def add_transaction(id: int, transaction: TransactionCreate):
    try:
        if transaction.shares <= 0:
            return HTTPResponse(status_code=400, content={"error": "Number of shares must be positive."})
        
        if transaction.type not in ["buy", "sell"]:
            return HTTPResponse(status_code=400, content={"error": "Transaction type must be 'buy' or 'sell'."})
        
        return HTTPResponse(status_code=201, content={"message": f"Recorded {transaction.type} of {transaction.shares} shares for portfolio entry {id}."})
    except Exception as e:
        message = str(e)
        return HTTPResponse(status_code=500, content={"error": message})
    
@router.get("/portfolios/{id}/holdings")
async def get_holdings(id: int):
    try:
        if id != 1:
            return HTTPResponse(status_code=404, content={"error": "Portfolio entry not found."})
    except Exception as e:
        message = str(e)
        return HTTPResponse(status_code=500, content={"error": message})

