import re
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class QueryInput(BaseModel):
    query: str = Field(description="The question or search query to run against the database")

class BaseDatabaseTool(BaseTool):
    """Base tool for querying SQLite databases safely and generating natural language answers."""

    db_path: Path
    table_name: str
    schema_description: str
    llm: Optional[Any] = None
    args_schema: Type[BaseModel] = QueryInput

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def is_safe_sql(sql: str) -> bool:
        """Validate that the SQL query is strictly read-only."""
        cleaned = sql.strip().strip(";")
        # Remove comments
        cleaned = re.sub(r"--.*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL).strip()

        # Disallow multiple semicolon-delimited statements
        if ";" in cleaned:
            return False

        upper = cleaned.upper()
        if not (upper.startswith("SELECT") or upper.startswith("WITH")):
            return False

        forbidden = [
            r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
            r"\bALTER\b", r"\bTRUNCATE\b", r"\bATTACH\b", r"\bDETACH\b",
            r"\bPRAGMA\b", r"\bCREATE\b", r"\bREPLACE\b"
        ]
        for pattern in forbidden:
            if re.search(pattern, upper):
                return False

        return True

    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Safely execute a SQL SELECT query and return list of dictionaries."""
        if not self.is_safe_sql(sql):
            raise ValueError(f"Unsafe or non-SELECT SQL query rejected: {sql}")

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def generate_sql(self, user_query: str) -> str:
        """Generate a valid SQL SELECT statement using LLM or structured rules."""
        # Direct SQL passthrough if user already provided valid SELECT
        cleaned = user_query.strip().strip(";")
        if cleaned.upper().startswith("SELECT") and self.is_safe_sql(cleaned):
            return cleaned

        if self.llm:
            try:
                prompt = (
                    f"You are a SQLite database expert. Write a single SQLite SELECT query to answer the user question.\n"
                    f"Table schema for `{self.table_name}`:\n"
                    f"{self.schema_description}\n\n"
                    f"Rules:\n"
                    f"1. Output ONLY the raw SQL query, with no markdown, backticks, or extra explanation.\n"
                    f"2. Use LIKE with lowercase or UPPER for case-insensitive text matching.\n"
                    f"3. Limit result rows to 10 unless the user specifically asks for COUNT or a different limit.\n\n"
                    f"User question: {user_query}\n"
                    f"SQL:"
                )
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                # Clean possible markdown fencing
                cleaned_sql = re.sub(r"^```(sql)?", "", content.strip(), flags=re.IGNORECASE)
                cleaned_sql = re.sub(r"```$", "", cleaned_sql).strip()
                if self.is_safe_sql(cleaned_sql):
                    return cleaned_sql
            except Exception as e:
                logger.warning(f"LLM SQL generation failed, falling back to rule-based parser: {e}")

        return self.rule_based_sql(user_query)

    def rule_based_sql(self, user_query: str) -> str:
        """Fallback rule-based SQL generator for common query intents."""
        # Subclasses can override with specific domain logic
        return f"SELECT * FROM {self.table_name} LIMIT 5"

    def format_results(self, user_query: str, sql: str, rows: List[Dict[str, Any]]) -> str:
        """Format query results into a natural language response."""
        if not rows:
            return f"No records found in {self.table_name} matching: '{user_query}'."

        if self.llm:
            try:
                sample_data = str(rows[:10])
                prompt = (
                    f"Answer the following user question in clear, natural English using the database query results.\n"
                    f"Question: {user_query}\n"
                    f"Database results: {sample_data}\n"
                    f"Total rows retrieved: {len(rows)}\n"
                    f"Answer:"
                )
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.warning(f"LLM formatting failed, using deterministic format: {e}")

        # Deterministic natural language formatting
        if len(rows) == 1 and len(rows[0]) == 1:
            key, val = list(rows[0].items())[0]
            return f"The total count for '{user_query}' is {val}."

        formatted_rows = []
        for i, row in enumerate(rows[:10], start=1):
            details = ", ".join(f"{k}: {v}" for k, v in row.items() if v is not None)
            formatted_rows.append(f"{i}. {details}")

        count_header = f"Found {len(rows)} matching record(s) in {self.table_name}:"
        return f"{count_header}\n" + "\n".join(formatted_rows)

    def _run(self, query: str) -> str:
        """Execute the tool workflow: generate SQL, run query, format response."""
        try:
            sql = self.generate_sql(query)
            rows = self.execute_sql(sql)
            return self.format_results(query, sql, rows)
        except Exception as e:
            logger.error(f"Error querying {self.table_name}: {e}")
            return f"Error executing query on {self.table_name}: {str(e)}"
