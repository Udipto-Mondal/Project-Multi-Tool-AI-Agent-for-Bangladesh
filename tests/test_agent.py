import pytest
from src.agent import BangladeshAIAgent, create_bangladesh_agent

def test_agent_initialization():
    agent = create_bangladesh_agent(verbose=False)
    assert len(agent.tools) == 4
    tool_names = [t.name.lower() for t in agent.tools]
    assert "institutionsdbtool" in tool_names
    assert "hospitalsdbtool" in tool_names
    assert "restaurantsdbtool" in tool_names
    assert "websearchtool" in tool_names

def test_query_routing():
    agent = BangladeshAIAgent(verbose=False)

    # Database routes
    assert agent.route_query_offline("How many hospitals are in Dhaka?") == "hospitalsdbtool"
    assert agent.route_query_offline("Find 250-bed hospitals in Sylhet") == "hospitalsdbtool"
    assert agent.route_query_offline("How many colleges are in Rajshahi?") == "institutionsdbtool"
    assert agent.route_query_offline("List government universities in Dhaka") == "institutionsdbtool"
    assert agent.route_query_offline("Top rated restaurants in Dhaka") == "restaurantsdbtool"
    assert agent.route_query_offline("Find biryani restaurants in Chittagong") == "restaurantsdbtool"

    # Web search routes
    assert agent.route_query_offline("What is the role of DGHS in Bangladesh?") == "websearchtool"
    assert agent.route_query_offline("What is the healthcare policy in Bangladesh?") == "websearchtool"

def test_agent_execution_hospitals():
    agent = BangladeshAIAgent(verbose=False)
    response = agent.run("How many hospitals are in Dhaka?")
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert ("count" in response.lower() or "total" in response.lower() or "9876" in response)

def test_agent_execution_institutions():
    agent = BangladeshAIAgent(verbose=False)
    response = agent.run("How many colleges are in Dhaka?")
    assert isinstance(response, str)
    assert len(response.strip()) > 0

def test_agent_execution_restaurants():
    agent = BangladeshAIAgent(verbose=False)
    response = agent.run("Top rated restaurants in Dhaka")
    assert isinstance(response, str)
    assert len(response.strip()) > 0

def test_agent_execution_web_search():
    agent = BangladeshAIAgent(verbose=False)
    response = agent.run("What is the role of DGHS in Bangladesh?")
    assert isinstance(response, str)
    assert len(response.strip()) > 0
    assert ("dghs" in response.lower() or "health" in response.lower() or "directorate" in response.lower())

def test_agent_empty_query():
    agent = BangladeshAIAgent(verbose=False)
    response = agent.run("")
    assert "provide a query" in response.lower()
