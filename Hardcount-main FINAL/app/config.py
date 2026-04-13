import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')

    # PostgreSQL connection
    DB_HOST     = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT     = os.getenv('DB_PORT', '5432')
    DB_USER     = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME     = os.getenv('DB_NAME', 'hardcount')