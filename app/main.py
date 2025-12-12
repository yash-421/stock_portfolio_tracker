from fastapi import FastAPI


app = FastAPI(title="Stock Portfolio Tracker")



@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stock Portfolio Tracker API!"}