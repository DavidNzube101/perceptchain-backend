import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    DUNE_API_KEY = os.getenv("DUNE_API_KEY", "")
    DUNE_API_BASE = "https://api.dune.com/api"
    ECHO_API_BASE = f"{DUNE_API_BASE}/echo/beta"
    V1_API_BASE = f"{DUNE_API_BASE}/v1"
    
class DevelopmentConfig(Config):
    DEBUG = True
