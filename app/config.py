
import os


class Settings:
    def __init__(self):
        self.debug = True
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yash123")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "stock_tracker")

settings = Settings()