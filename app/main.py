import logging
from fastapi import FastAPI
from app.routers import portfolios,users,analytics,stocks,transactions
from app.logger_config import setup_logging
from app.connection import get_db
app = FastAPI(title="Stock Portfolio Tracker")

setup_logging()
logger = logging.getLogger(__name__)


app.include_router(portfolios.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(stocks.router)
app.include_router(transactions.router)



@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stock Portfolio Tracker API!"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}