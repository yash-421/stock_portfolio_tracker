
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    def __init__(self):
        self.debug = True
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yash123")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "stock_tracker")
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

settings = Settings()