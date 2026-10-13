import os
import re
import shutil
import sqlite3
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DATA_DIR = BASE_DIR / "data"

BANGLADESH_DIVISIONS = [
    "Dhaka", "Chittagong", "Chattogram", "Rajshahi", "Khulna",
    "Barisal", "Barishal", "Sylhet", "Rangpur", "Mymensingh"
]

def clean_string(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    return val_str if val_str else None

def extract_city_from_address(addr):
    if not addr or pd.isna(addr):
        return None
    addr_str = str(addr)
    # Check for major divisions/cities
    for city in BANGLADESH_DIVISIONS:
        if re.search(rf"\b{city}\b", addr_str, re.IGNORECASE):
            return "Chattogram" if city.lower() == "chittagong" else ("Barishal" if city.lower() == "barisal" else city)
    # Fallback: check parts separated by comma before 'Bangladesh'
    parts = [p.strip() for p in addr_str.split(",") if p.strip()]
    if len(parts) >= 2:
        last = parts[-1].strip()
        if "bangladesh" in last.lower() and len(parts) >= 2:
            candidate = parts[-2].strip()
            # remove postal codes if present
            candidate = re.sub(r"\d+", "", candidate).strip()
            if candidate:
                return candidate
    return None

def build_institutions_db():
    csv_path = RAW_DIR / "institutions.csv"
    db_path = DATA_DIR / "institutions.db"
    logger.info(f"Building {db_path.name} from {csv_path.name}...")

    df = pd.read_csv(csv_path, dtype=str)
    
    # Clean whitespace and strip strings
    for col in df.columns:
        df[col] = df[col].apply(clean_string)

    # Column mapping to clean, meaningful English names
    rename_map = {
        "INSTITUTE NAME": "name",
        "EIIN": "eiin",
        "INSTITUTE_TYPE": "type",
        "DIVISION_ID": "division_id",
        "DIVISION": "division",
        "DISTRICT_ID": "district_id",
        "DISTRICT": "district",
        "THANA_ID": "thana_id",
        "THANA": "thana",
        "UNION_ID": "union_id",
        "UNION_NAME": "union_name",
        "MAUZA_ID": "mauza_id",
        "MAUZA_NAME": "mauza_name",
        "AREA_STATUS": "area_status",
        "GEOGRPYCAL_STATUS": "geographical_status",
        "ADDRESS": "address",
        "POST": "post_office",
        "MANAGEMENT_TYPE": "management_type",
        "MOBILE": "mobile",
        "STUDENT_TYPE": "student_type",
        "EDUCATION_LEVEL": "education_level",
        "AFFILIATION": "affiliation",
        "MPO_STATUS": "mpo_status"
    }
    df = df.rename(columns=rename_map)

    # Clean numeric types
    df["eiin"] = pd.to_numeric(df["eiin"], errors="coerce").astype("Int64")
    df["division_id"] = pd.to_numeric(df["division_id"], errors="coerce").astype("Int64")
    df["district_id"] = pd.to_numeric(df["district_id"], errors="coerce").astype("Int64")
    df["thana_id"] = pd.to_numeric(df["thana_id"], errors="coerce").astype("Int64")
    df["union_id"] = pd.to_numeric(df["union_id"], errors="coerce").astype("Int64")
    df["mauza_id"] = pd.to_numeric(df["mauza_id"], errors="coerce").astype("Int64")

    # Connect to SQLite
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE institutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            eiin INTEGER,
            type TEXT,
            division_id INTEGER,
            division TEXT,
            district_id INTEGER,
            district TEXT,
            thana_id INTEGER,
            thana TEXT,
            union_id INTEGER,
            union_name TEXT,
            mauza_id INTEGER,
            mauza_name TEXT,
            area_status TEXT,
            geographical_status TEXT,
            address TEXT,
            post_office TEXT,
            management_type TEXT,
            mobile TEXT,
            student_type TEXT,
            education_level TEXT,
            affiliation TEXT,
            mpo_status TEXT
        )
    """)

    insert_cols = [
        "name", "eiin", "type", "division_id", "division", "district_id", "district",
        "thana_id", "thana", "union_id", "union_name", "mauza_id", "mauza_name",
        "area_status", "geographical_status", "address", "post_office", "management_type",
        "mobile", "student_type", "education_level", "affiliation", "mpo_status"
    ]

    records = [
        tuple(None if pd.isna(row[c]) else row[c] for c in insert_cols)
        for _, row in df.iterrows()
    ]

    cur.executemany(
        f"INSERT INTO institutions ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
        records
    )

    # Indexes for high performance
    cur.execute("CREATE INDEX idx_institutions_name ON institutions(name)")
    cur.execute("CREATE INDEX idx_institutions_type ON institutions(type)")
    cur.execute("CREATE INDEX idx_institutions_division ON institutions(division)")
    cur.execute("CREATE INDEX idx_institutions_district ON institutions(district)")
    cur.execute("CREATE INDEX idx_institutions_education_level ON institutions(education_level)")
    cur.execute("CREATE INDEX idx_institutions_management_type ON institutions(management_type)")

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
    conn.close()
    logger.info(f"Built institutions.db successfully: {count} rows loaded.")

def build_hospitals_db():
    csv_path = RAW_DIR / "hospitals.csv"
    db_path = DATA_DIR / "hospitals.db"
    logger.info(f"Building {db_path.name} from {csv_path.name}...")

    df = pd.read_csv(csv_path)

    # String cleaning
    str_cols = ["Name", "Name (Bangla)", "Agency", "Type", "Division", "District", 
                "City Corporation", "Upazila", "Paurasava", "Union"]
    for col in str_cols:
        df[col] = df[col].apply(clean_string)

    rename_map = {
        "Id": "id",
        "Name": "name",
        "Name (Bangla)": "name_bn",
        "Code": "code",
        "Agency": "agency",
        "Type": "type",
        "Division": "division",
        "District": "district",
        "City Corporation": "city_corporation",
        "Upazila": "upazila",
        "Paurasava": "paurasava",
        "Union": "union_name",
        "Private": "is_private"
    }
    df = df.rename(columns=rename_map)

    # Extract bed capacity from Name or Type where mentioned (e.g. '250 Bed', '50-bed')
    def parse_bed_capacity(name_val, type_val):
        text = f"{name_val or ''} {type_val or ''}"
        match = re.search(r"(\d+)\s*[- ]?[Bb]ed", text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    df["bed_capacity"] = [
        parse_bed_capacity(r["name"], r["type"]) for _, r in df.iterrows()
    ]

    # Convert types
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["code"] = pd.to_numeric(df["code"], errors="coerce").astype("Int64")
    df["is_private"] = pd.to_numeric(df["is_private"], errors="coerce").fillna(0).astype(int)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            name_bn TEXT,
            code INTEGER,
            agency TEXT,
            type TEXT,
            division TEXT,
            district TEXT,
            city_corporation TEXT,
            upazila TEXT,
            paurasava TEXT,
            union_name TEXT,
            bed_capacity INTEGER,
            is_private INTEGER NOT NULL DEFAULT 0
        )
    """)

    insert_cols = [
        "id", "name", "name_bn", "code", "agency", "type", "division", "district",
        "city_corporation", "upazila", "paurasava", "union_name", "bed_capacity", "is_private"
    ]

    records = [
        tuple(None if pd.isna(row[c]) else row[c] for c in insert_cols)
        for _, row in df.iterrows()
    ]

    cur.executemany(
        f"INSERT INTO hospitals ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
        records
    )

    # Performance indexes
    cur.execute("CREATE INDEX idx_hospitals_name ON hospitals(name)")
    cur.execute("CREATE INDEX idx_hospitals_type ON hospitals(type)")
    cur.execute("CREATE INDEX idx_hospitals_agency ON hospitals(agency)")
    cur.execute("CREATE INDEX idx_hospitals_division ON hospitals(division)")
    cur.execute("CREATE INDEX idx_hospitals_district ON hospitals(district)")
    cur.execute("CREATE INDEX idx_hospitals_is_private ON hospitals(is_private)")

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    conn.close()
    logger.info(f"Built hospitals.db successfully: {count} rows loaded.")

def build_restaurants_db():
    csv_path = RAW_DIR / "restaurants.csv"
    db_path = DATA_DIR / "restaurants.db"
    logger.info(f"Building {db_path.name} from {csv_path.name}...")

    df = pd.read_csv(csv_path)

    # Drop exact duplicates
    df = df.drop_duplicates()

    # Clean strings
    df["place_id"] = df["place_id"].apply(clean_string)
    df["name"] = df["name"].apply(clean_string)
    df["address"] = df["address"].apply(clean_string)

    rename_map = {
        "number_of_reviews": "reviews_count",
        "affluence": "price_level"
    }
    df = df.rename(columns=rename_map)

    # Numeric conversion
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce").fillna(0).astype(int)
    df["price_level"] = pd.to_numeric(df["price_level"], errors="coerce").astype("Int64")

    # Extract location / city
    df["location"] = df["address"].apply(extract_city_from_address)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            rating REAL,
            reviews_count INTEGER,
            price_level INTEGER,
            location TEXT,
            address TEXT
        )
    """)

    insert_cols = [
        "place_id", "name", "latitude", "longitude", "rating",
        "reviews_count", "price_level", "location", "address"
    ]

    records = [
        tuple(None if pd.isna(row[c]) else row[c] for c in insert_cols)
        for _, row in df.iterrows()
    ]

    cur.executemany(
        f"INSERT INTO restaurants ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})",
        records
    )

    # Indexes
    cur.execute("CREATE INDEX idx_restaurants_name ON restaurants(name)")
    cur.execute("CREATE INDEX idx_restaurants_rating ON restaurants(rating)")
    cur.execute("CREATE INDEX idx_restaurants_reviews ON restaurants(reviews_count)")
    cur.execute("CREATE INDEX idx_restaurants_location ON restaurants(location)")

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
    conn.close()
    logger.info(f"Built restaurants.db successfully: {count} rows loaded.")

def sync_root_databases():
    """Copy database files to the repository root for root-level access convenience."""
    for db_name in ["institutions.db", "hospitals.db", "restaurants.db"]:
        src = DATA_DIR / db_name
        dest = BASE_DIR / db_name
        if src.exists():
            shutil.copy2(src, dest)
            logger.info(f"Synchronized database to root: {dest.name}")

if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    build_institutions_db()
    build_hospitals_db()
    build_restaurants_db()
    sync_root_databases()
    logger.info("All databases built and synchronized successfully.")
