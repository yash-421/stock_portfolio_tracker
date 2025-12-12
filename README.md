# Stock Portfolio Tracker (Backend)

FastAPI backend for tracking portfolios, holdings, transactions and real-time stock prices.

## Features

- User authentication (JWT)
- Multiple portfolios per user
- Buy/Sell transactions
- Holdings calculation
- Price fetcher + caching (mock)
- PostgreSQL + SQLAlchemy

## Run Locally

pip install -r requirements.txt
uvicorn app.main:app --reload
