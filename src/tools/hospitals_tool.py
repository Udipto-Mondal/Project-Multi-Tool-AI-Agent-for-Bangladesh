import re
from pathlib import Path
from typing import Any, Optional
from src.config import HOSPITALS_DB_PATH
from src.tools.base_db_tool import BaseDatabaseTool

HOSPITALS_SCHEMA = """
TABLE: hospitals
COLUMNS:
- id: INTEGER PRIMARY KEY
- name: TEXT (Healthcare facility name)
- name_bn: TEXT (Bengali name)
- code: INTEGER (Facility code)
- agency: TEXT (e.g., 'DGHS', 'DGFP')
- type: TEXT (e.g., 'Community Clinic', 'Private Hospital / Clinic', 'District/General Hospital', 'Upazila Health Complex', 'Medical College')
- division: TEXT (e.g., 'Dhaka', 'Chittagong', 'Chattogram', 'Rajshahi', 'Khulna', 'Barishal', 'Sylhet', 'Rangpur', 'Mymensingh')
- district: TEXT (e.g., 'Dhaka', 'Gazipur', 'Chittagong', 'Sylhet')
- city_corporation: TEXT
- upazila: TEXT
- bed_capacity: INTEGER (Bed count when explicitly recorded, e.g., 250, 100, 50, 20)
- is_private: INTEGER (0 for public/government facilities, 1 for private facilities)
"""

DIVISIONS = ["Dhaka", "Chittagong", "Chattogram", "Rajshahi", "Khulna", "Barisal", "Barishal", "Sylhet", "Rangpur", "Mymensingh"]

class HospitalsDBTool(BaseDatabaseTool):
    """LangChain tool for querying information about Bangladeshi hospitals and healthcare facilities."""

    name: str = "HospitalsDBTool"
    description: str = (
        "Queries hospitals, healthcare clinics, diagnostic centers, bed capacity, "
        "medical colleges, DGHS facilities, and public vs private health services in Bangladesh."
    )
    table_name: str = "hospitals"
    schema_description: str = HOSPITALS_SCHEMA
    db_path: Path = HOSPITALS_DB_PATH

    def __init__(self, db_path: Optional[Path] = None, llm: Optional[Any] = None, **kwargs):
        path = db_path or HOSPITALS_DB_PATH
        super().__init__(
            db_path=path,
            table_name="hospitals",
            schema_description=HOSPITALS_SCHEMA,
            llm=llm,
            **kwargs
        )

    def rule_based_sql(self, user_query: str) -> str:
        q = user_query.lower()
        is_count = any(k in q for k in ["how many", "count", "number of", "total"])

        conditions = []

        # Division / District match
        for div in DIVISIONS:
            if div.lower() in q:
                conditions.append(f"(LOWER(division) LIKE '%{div.lower()}%' OR LOWER(district) LIKE '%{div.lower()}%')")
                break

        # Public vs Private
        if "private" in q:
            conditions.append("is_private = 1")
        elif "government" in q or "govt" in q or "public" in q:
            conditions.append("is_private = 0")

        # Agency match (e.g. DGHS)
        if "dghs" in q:
            conditions.append("UPPER(agency) = 'DGHS'")

        # Type match
        if "clinic" in q or "community clinic" in q:
            conditions.append("LOWER(type) LIKE '%clinic%'")
        elif "medical college" in q:
            conditions.append("LOWER(type) LIKE '%medical college%'")
        elif "upazila health complex" in q:
            conditions.append("LOWER(type) LIKE '%upazila health complex%'")
        elif "diagnostic" in q:
            conditions.append("LOWER(type) LIKE '%diagnostic%'")

        # Bed capacity match
        bed_match = re.search(r"(\d+)\s*[- ]?bed", q)
        if bed_match:
            beds = int(bed_match.group(1))
            conditions.append(f"(bed_capacity >= {beds} OR LOWER(name) LIKE '%{beds}%bed%')")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        if is_count:
            return f"SELECT COUNT(*) AS total_hospitals FROM hospitals{where_clause}"

        return f"SELECT name, type, agency, division, district, is_private, bed_capacity FROM hospitals{where_clause} LIMIT 10"
