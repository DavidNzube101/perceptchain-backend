import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # API key validation
    HELIUS_API_KEY = os.environ.get('HELIUS_API_KEY')
    if not HELIUS_API_KEY:
        raise ValueError("HELIUS_API_KEY not found in environment variables")
    
    # Helius RPC URL
    try:
        HELIUS_RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    except:
        HELIUS_API_URL = os.environ.get('HELIUS_API_URL')
    
    # Flask configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Request timeout settings
    DEFAULT_TIMEOUT = 20000