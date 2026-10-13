import sqlite3
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def test_institutions_database_schema_and_rows():
    db_path = DATA_DIR / "institutions.db"
    assert db_path.exists(), "institutions.db does not exist"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Verify table existence
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    assert "institutions" in table_names

    # Verify row count
    count = cur.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
    assert count == 34901, f"Expected 34901 rows, got {count}"

    # Verify column structure
    col_info = cur.execute("PRAGMA table_info(institutions)").fetchall()
    col_names = [c[1] for c in col_info]
    assert "name" in col_names
    assert "type" in col_names
    assert "division" in col_names
    assert "district" in col_names
    assert "management_type" in col_names

    # Verify sample query
    sample = cur.execute("SELECT name, type, division, district FROM institutions LIMIT 5").fetchall()
    assert len(sample) == 5

    # Test count query for Dhaka
    dhaka_count = cur.execute(
        "SELECT COUNT(*) FROM institutions WHERE UPPER(division) = 'DHAKA'"
    ).fetchone()[0]
    assert dhaka_count > 0

    conn.close()

def test_hospitals_database_schema_and_rows():
    db_path = DATA_DIR / "hospitals.db"
    assert db_path.exists(), "hospitals.db does not exist"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    assert "hospitals" in table_names

    count = cur.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    assert count == 38886, f"Expected 38886 rows, got {count}"

    col_info = cur.execute("PRAGMA table_info(hospitals)").fetchall()
    col_names = [c[1] for c in col_info]
    assert "id" in col_names
    assert "name" in col_names
    assert "type" in col_names
    assert "division" in col_names
    assert "district" in col_names
    assert "agency" in col_names
    assert "is_private" in col_names

    # Test query for DGHS agencies
    dghs_count = cur.execute(
        "SELECT COUNT(*) FROM hospitals WHERE UPPER(agency) = 'DGHS'"
    ).fetchone()[0]
    assert dghs_count > 0

    conn.close()

def test_restaurants_database_schema_and_rows():
    db_path = DATA_DIR / "restaurants.db"
    assert db_path.exists(), "restaurants.db does not exist"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t[0] for t in tables]
    assert "restaurants" in table_names

    count = cur.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0]
    assert count == 10758, f"Expected 10758 rows, got {count}"

    col_info = cur.execute("PRAGMA table_info(restaurants)").fetchall()
    col_dict = {c[1]: c[2] for c in col_info}
    assert "name" in col_dict
    assert col_dict["latitude"] == "REAL"
    assert col_dict["longitude"] == "REAL"
    assert col_dict["rating"] == "REAL"
    assert col_dict["reviews_count"] == "INTEGER"

    # Test high rated query
    top_rated = cur.execute(
        "SELECT name, rating, reviews_count FROM restaurants WHERE rating >= 4.5 ORDER BY reviews_count DESC LIMIT 5"
    ).fetchall()
    assert len(top_rated) == 5

    conn.close()
