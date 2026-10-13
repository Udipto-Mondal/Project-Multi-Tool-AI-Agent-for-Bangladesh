import os
import re
import logging
from typing import Any, Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

try:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
    except ImportError:
        AgentExecutor = None
        create_tool_calling_agent = None

from src.tools import (
    InstitutionsDBTool,
    HospitalsDBTool,
    RestaurantsDBTool,
    WebSearchTool,
)

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are the Multi-Tool AI Agent for Bangladesh, an expert assistant that provides accurate information about Bangladesh using both dedicated offline databases and live web search.

You have access to the following 4 tools:
1. InstitutionsDBTool: Use this tool for data and statistics queries regarding educational and governmental institutions in Bangladesh (schools, colleges, universities, madrasahs, EIIN numbers, management types, education levels, divisions, districts).
2. HospitalsDBTool: Use this tool for data and statistics queries regarding healthcare facilities, hospitals, clinics, diagnostic centers, agencies (e.g., DGHS), bed capacity, and public vs. private facilities in Bangladesh.
3. RestaurantsDBTool: Use this tool for queries regarding restaurants, cafes, ratings, customer review counts, price tiers, specific cuisines, and city/district locations across Bangladesh.
4. WebSearchTool: Use this tool for general knowledge, definitions, history, government policies, regulations, and cultural context about Bangladesh (e.g., "What is the healthcare policy in Bangladesh?", "What is the role of DGHS in Bangladesh?").

ROUTING RULES:
- If the question is about specific data, statistics, counts, or locations in the provided datasets (hospitals, schools/universities, restaurants), ALWAYS query the respective database tool.
  Example: "How many hospitals are in Dhaka?" -> HospitalsDBTool
  Example: "List top rated restaurants in Chittagong" -> RestaurantsDBTool
  Example: "How many government colleges are in Rajshahi?" -> InstitutionsDBTool
- If the question asks about broader policies, government roles, definitions, cultural context, or live information not stored in the relational databases, ALWAYS query WebSearchTool.
  Example: "What is the healthcare policy in Bangladesh?" -> WebSearchTool
  Example: "What is the role of DGHS in Bangladesh?" -> WebSearchTool

Respond clearly, concisely, and professionally in English.
"""

class BangladeshAIAgent:
    """Main Multi-Tool AI Agent for Bangladesh powered by LangChain."""

    def __init__(
        self,
        llm: Optional[Any] = None,
        api_key: Optional[str] = None,
        verbose: bool = True
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.verbose = verbose
        self.llm = llm

        # If LLM not explicitly passed, attempt to instantiate Gemini
        if self.llm is None and self.api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=self.api_key,
                    temperature=0.1
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatGoogleGenerativeAI: {e}")
                self.llm = None

        # Instantiate all 4 tools
        self.institutions_tool = InstitutionsDBTool(llm=self.llm)
        self.hospitals_tool = HospitalsDBTool(llm=self.llm)
        self.restaurants_tool = RestaurantsDBTool(llm=self.llm)
        self.search_tool = WebSearchTool(llm=self.llm)

        self.tools: List[BaseTool] = [
            self.institutions_tool,
            self.hospitals_tool,
            self.restaurants_tool,
            self.search_tool,
        ]

        self.tools_map: Dict[str, BaseTool] = {
            t.name.lower(): t for t in self.tools
        }

        # Initialize LangChain AgentExecutor if LLM is available
        self.agent_executor: Optional[Any] = None
        if self.llm and AgentExecutor and create_tool_calling_agent:
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", AGENT_SYSTEM_PROMPT),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ])
                agent = create_tool_calling_agent(self.llm, self.tools, prompt)
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=self.verbose,
                    handle_parsing_errors=True
                )
            except Exception as e:
                logger.warning(f"Failed to create LangChain AgentExecutor: {e}")
                self.agent_executor = None

    def route_query_offline(self, query: str) -> str:
        """Determines the appropriate tool name based on semantic intent rules."""
        q = query.lower()

        # Check for general knowledge / policy questions first
        policy_patterns = [
            r"\bpolicy\b", r"\brole of\b", r"\bwhat is the role\b", r"\bdefinition\b",
            r"\bdefine\b", r"\bexplain\b", r"\bhistory\b", r"\bculture\b",
            r"\bconstitution\b", r"\bguideline\b", r"\bfunction of\b"
        ]
        if any(re.search(pat, q) for pat in policy_patterns):
            return "websearchtool"

        # Hospitals / Healthcare facility queries
        hospital_patterns = [
            r"\bhospital", r"\bclinic", r"\bbed", r"\bdoctor", r"\bhealth complex\b",
            r"\bhealthcare\b", r"\bmedical college", r"\bdiagnostic\b", r"\bdghs facility\b",
            r"\bcommunity clinic\b"
        ]
        if any(re.search(pat, q) for pat in hospital_patterns):
            return "hospitalsdbtool"

        # Institutions / Education queries
        institution_patterns = [
            r"\binstitution", r"\buniversit", r"\bcollege", r"\bschool",
            r"\bmadrasha", r"\bmadrasah", r"\beiin\b", r"\beducation\b",
            r"\bmpo\b", r"\bstudent"
        ]
        if any(re.search(pat, q) for pat in institution_patterns):
            return "institutionsdbtool"

        # Restaurant / Food queries
        restaurant_patterns = [
            r"\brestaurant", r"\bfood\b", r"\bcafe\b", r"\bcuisine\b", r"\brating",
            r"\breview", r"\bbiryani\b", r"\bdine\b", r"\bdining\b",
            r"\bprice level\b", r"\baffluence\b", r"\bkacchi\b"
        ]
        if any(re.search(pat, q) for pat in restaurant_patterns):
            return "restaurantsdbtool"

        # Default fallback to web search for open-ended queries
        return "websearchtool"

    def run(self, query: str) -> str:
        """Execute the agent on a user query."""
        if not query or not query.strip():
            return "Please provide a query or question."

        # If LLM and AgentExecutor are configured, run the full agent workflow
        if self.agent_executor:
            try:
                result = self.agent_executor.invoke({"input": query})
                return result.get("output", str(result))
            except Exception as e:
                logger.warning(f"AgentExecutor execution encountered error: {e}. Falling back to router.")

        # Fallback intelligent routing
        selected_tool_name = self.route_query_offline(query)
        tool = self.tools_map.get(selected_tool_name, self.search_tool)
        logger.info(f"Routed query to tool: {tool.name}")
        return tool.run(query)

def create_bangladesh_agent(api_key: Optional[str] = None, verbose: bool = False) -> BangladeshAIAgent:
    """Factory helper to construct BangladeshAIAgent."""
    return BangladeshAIAgent(api_key=api_key, verbose=verbose)
