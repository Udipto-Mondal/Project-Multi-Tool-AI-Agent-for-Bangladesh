import pytest
from src.tools import InstitutionsDBTool, HospitalsDBTool, RestaurantsDBTool
from src.tools.base_db_tool import BaseDatabaseTool

def test_sql_safety_guard():
    # Valid SELECT and WITH queries
    assert BaseDatabaseTool.is_safe_sql("SELECT * FROM institutions") is True
    assert BaseDatabaseTool.is_safe_sql("SELECT COUNT(*) FROM hospitals WHERE division = 'Dhaka'") is True
    assert BaseDatabaseTool.is_safe_sql("WITH ranked AS (SELECT * FROM restaurants) SELECT * FROM ranked") is True

    # Dangerous / Mutating statements must be rejected
    assert BaseDatabaseTool.is_safe_sql("DROP TABLE institutions") is False
    assert BaseDatabaseTool.is_safe_sql("DELETE FROM hospitals") is False
    assert BaseDatabaseTool.is_safe_sql("UPDATE restaurants SET rating = 5") is False
    assert BaseDatabaseTool.is_safe_sql("INSERT INTO institutions VALUES (1, 'Test')") is False
    assert BaseDatabaseTool.is_safe_sql("ALTER TABLE hospitals ADD COLUMN test TEXT") is False
    assert BaseDatabaseTool.is_safe_sql("SELECT * FROM institutions; DROP TABLE institutions;") is False

def test_institutions_tool_execution():
    tool = InstitutionsDBTool()
    assert tool.name == "InstitutionsDBTool"
    assert "institutions" in tool.description.lower()

    # Query count
    result_count = tool.run("How many colleges are in Dhaka?")
    assert isinstance(result_count, str)
    assert "total" in result_count.lower() or "count" in result_count.lower() or "found" in result_count.lower()

    # Query listings
    result_list = tool.run("List government institutions in Rajshahi")
    assert isinstance(result_list, str)
    assert len(result_list) > 0

    # Direct SQL passthrough
    direct_sql_res = tool.run("SELECT name, division FROM institutions LIMIT 3")
    assert "1." in direct_sql_res or "name:" in direct_sql_res.lower()

def test_hospitals_tool_execution():
    tool = HospitalsDBTool()
    assert tool.name == "HospitalsDBTool"
    assert "hospitals" in tool.description.lower()

    # Query count
    res_count = tool.run("How many hospitals are in Dhaka?")
    assert isinstance(res_count, str)
    assert "total" in res_count.lower() or "count" in res_count.lower() or "found" in res_count.lower()

    # Query specific agency
    res_dghs = tool.run("Find DGHS facilities in Sylhet")
    assert isinstance(res_dghs, str)
    assert len(res_dghs) > 0

    # Query private vs public
    res_private = tool.run("List private hospitals in Dhaka")
    assert isinstance(res_private, str)
    assert len(res_private) > 0

def test_restaurants_tool_execution():
    tool = RestaurantsDBTool()
    assert tool.name == "RestaurantsDBTool"
    assert "restaurants" in tool.description.lower()

    # Top rated query
    res_top = tool.run("Top rated restaurants in Dhaka")
    assert isinstance(res_top, str)
    assert len(res_top) > 0

    # Review count / cuisine query
    res_biryani = tool.run("Find biryani restaurants")
    assert isinstance(res_biryani, str)
    assert len(res_biryani) > 0

    # Location count
    res_count = tool.run("How many restaurants are in Chattogram?")
    assert isinstance(res_count, str)
    assert "total" in res_count.lower() or "count" in res_count.lower() or "found" in res_count.lower()
