from fastapi import FastAPI
from app.routers import portfolios

app = FastAPI(title="Stock Portfolio Tracker")



app.include_router(portfolios.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stock Portfolio Tracker API!"}