import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# SQLite database paths
INSTITUTIONS_DB_PATH = DATA_DIR / "institutions.db"
HOSPITALS_DB_PATH = DATA_DIR / "hospitals.db"
RESTAURANTS_DB_PATH = DATA_DIR / "restaurants.db"

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
