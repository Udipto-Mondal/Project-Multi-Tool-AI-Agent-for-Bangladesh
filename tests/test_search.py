import pytest
from src.tools.search_tool import WebSearchTool

def test_web_search_tool_initialization():
    tool = WebSearchTool()
    assert tool.name == "WebSearchTool"
    assert "general knowledge" in tool.description.lower()
    assert tool.args_schema is not None

def test_web_search_healthcare_policy():
    tool = WebSearchTool()
    query = "What is the healthcare policy in Bangladesh?"
    result = tool.run(query)

    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert ("bangladesh" in result.lower() or "health" in result.lower() or "policy" in result.lower())

def test_web_search_dghs_role():
    tool = WebSearchTool()
    query = "What is the role of DGHS in Bangladesh?"
    result = tool.run(query)

    assert isinstance(result, str)
    assert len(result.strip()) > 0
    assert ("dghs" in result.lower() or "health" in result.lower() or "services" in result.lower() or "directorate" in result.lower())

def test_web_search_empty_handling():
    tool = WebSearchTool()
    result = tool.run("")
    assert isinstance(result, str)
