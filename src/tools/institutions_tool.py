import re
from pathlib import Path
from typing import Any, Optional
from src.config import INSTITUTIONS_DB_PATH
from src.tools.base_db_tool import BaseDatabaseTool

INSTITUTIONS_SCHEMA = """
TABLE: institutions
COLUMNS:
- id: INTEGER PRIMARY KEY
- name: TEXT (Institution name)
- eiin: INTEGER (Educational Institute Identification Number)
- type: TEXT (e.g., 'College', 'School', 'Madrasha', 'School and College')
- division: TEXT (e.g., 'DHAKA', 'CHITTAGONG', 'RAJSHAHI', 'KHULNA', 'BARISAL', 'SYLHET', 'RANGPUR', 'MYMENSINGH')
- district: TEXT (e.g., 'DHAKA', 'COMILLA', 'CHITTAGONG', 'SYLHET', 'BOGRA')
- thana: TEXT (Upazila or Thana)
- management_type: TEXT ('GOVERNMENT' or 'NON-GOVERNMENT')
- student_type: TEXT ('CO-EDUCATION JOINT', 'FEMALE', 'BOYS')
- education_level: TEXT (e.g., 'Higher Secondary', 'Secondary', 'Degree')
- mpo_status: TEXT ('YES' or 'NO')
"""

DIVISIONS = ["DHAKA", "CHITTAGONG", "CHATTOGRAM", "RAJSHAHI", "KHULNA", "BARISAL", "BARISHAL", "SYLHET", "RANGPUR", "MYMENSINGH"]

class InstitutionsDBTool(BaseDatabaseTool):
    """LangChain tool for querying information about Bangladeshi institutions."""

    name: str = "InstitutionsDBTool"
    description: str = (
        "Queries educational and governmental institutions in Bangladesh, "
        "including schools, colleges, universities, madrasahs, EIIN numbers, "
        "districts, divisions, and management types (government/non-government)."
    )
    table_name: str = "institutions"
    schema_description: str = INSTITUTIONS_SCHEMA
    db_path: Path = INSTITUTIONS_DB_PATH

    def __init__(self, db_path: Optional[Path] = None, llm: Optional[Any] = None, **kwargs):
        path = db_path or INSTITUTIONS_DB_PATH
        super().__init__(
            db_path=path,
            table_name="institutions",
            schema_description=INSTITUTIONS_SCHEMA,
            llm=llm,
            **kwargs
        )

    def rule_based_sql(self, user_query: str) -> str:
        q = user_query.lower()
        is_count = any(k in q for k in ["how many", "count", "number of", "total"])
        
        conditions = []
        
        # Division / District match
        for div in DIVISIONS:
            div_clean = "CHITTAGONG" if div in ["CHITTAGONG", "CHATTOGRAM"] else ("BARISAL" if div in ["BARISAL", "BARISHAL"] else div)
            if div.lower() in q:
                conditions.append(f"(UPPER(division) LIKE '%{div_clean}%' OR UPPER(district) LIKE '%{div_clean}%')")
                break

        # Type match
        if "college" in q:
            conditions.append("UPPER(type) LIKE '%COLLEGE%'")
        elif "madrasha" in q or "madrasah" in q:
            conditions.append("UPPER(type) LIKE '%MADRASHA%'")
        elif "school" in q:
            conditions.append("UPPER(type) LIKE '%SCHOOL%'")
        elif "university" in q:
            conditions.append("(UPPER(name) LIKE '%UNIVERSITY%' OR UPPER(type) LIKE '%UNIVERSITY%')")

        # Management match
        if "government" in q or "govt" in q:
            conditions.append("UPPER(management_type) = 'GOVERNMENT'")
        elif "non-government" in q or "private" in q:
            conditions.append("UPPER(management_type) = 'NON-GOVERNMENT'")

        # MPO match
        if "mpo" in q:
            conditions.append("UPPER(mpo_status) = 'YES'")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        if is_count:
            return f"SELECT COUNT(*) AS total_institutions FROM institutions{where_clause}"
        
        return f"SELECT name, type, division, district, management_type FROM institutions{where_clause} LIMIT 10"
