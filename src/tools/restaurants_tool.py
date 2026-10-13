import re
from pathlib import Path
from typing import Any, Optional
from src.config import RESTAURANTS_DB_PATH
from src.tools.base_db_tool import BaseDatabaseTool

RESTAURANTS_SCHEMA = """
TABLE: restaurants
COLUMNS:
- id: INTEGER PRIMARY KEY
- place_id: TEXT (Google Places ID)
- name: TEXT (Restaurant name)
- latitude: REAL
- longitude: REAL
- rating: REAL (Average rating between 0.0 and 5.0)
- reviews_count: INTEGER (Total customer reviews)
- price_level: INTEGER (Affluence/pricing tier from 1 to 4)
- location: TEXT (City or area, e.g. 'Dhaka', 'Chattogram', 'Sylhet')
- address: TEXT (Full street address)
"""

CITIES = ["Dhaka", "Chattogram", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barishal", "Barisal", "Cox's Bazar", "Cumilla"]

class RestaurantsDBTool(BaseDatabaseTool):
    """LangChain tool for querying information about Bangladeshi restaurants."""

    name: str = "RestaurantsDBTool"
    description: str = (
        "Queries restaurants, cafes, ratings, reviews count, price levels, "
        "and locations across Bangladesh."
    )
    table_name: str = "restaurants"
    schema_description: str = RESTAURANTS_SCHEMA
    db_path: Path = RESTAURANTS_DB_PATH

    def __init__(self, db_path: Optional[Path] = None, llm: Optional[Any] = None, **kwargs):
        path = db_path or RESTAURANTS_DB_PATH
        super().__init__(
            db_path=path,
            table_name="restaurants",
            schema_description=RESTAURANTS_SCHEMA,
            llm=llm,
            **kwargs
        )

    def rule_based_sql(self, user_query: str) -> str:
        q = user_query.lower()
        is_count = any(k in q for k in ["how many", "count", "number of", "total"])

        conditions = []

        # Location matching
        for city in CITIES:
            if city.lower() in q:
                city_clean = "Chattogram" if city.lower() in ["chittagong", "chattogram"] else city
                conditions.append(f"(LOWER(location) LIKE '%{city.lower()}%' OR LOWER(address) LIKE '%{city.lower()}%')")
                break

        # Rating filtering
        rating_match = re.search(r"rating\s*(?:>=|>|above|over)?\s*(\d+(?:\.\d+)?)", q)
        if rating_match:
            min_rating = float(rating_match.group(1))
            conditions.append(f"rating >= {min_rating}")
        elif any(k in q for k in ["top rated", "best", "highest rated"]):
            conditions.append("rating >= 4.0")

        # Specific food / cuisine / name keywords
        food_terms = ["biryani", "kacchi", "burger", "pizza", "cafe", "coffee", "chinese", "bakery", "sweet"]
        for term in food_terms:
            if term in q:
                conditions.append(f"LOWER(name) LIKE '%{term}%'")
                break

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        if is_count:
            return f"SELECT COUNT(*) AS total_restaurants FROM restaurants{where_clause}"

        order_by = " ORDER BY rating DESC, reviews_count DESC" if any(k in q for k in ["top", "best", "highest", "popular"]) else " ORDER BY reviews_count DESC"
        return f"SELECT name, rating, reviews_count, location, address FROM restaurants{where_clause}{order_by} LIMIT 10"
