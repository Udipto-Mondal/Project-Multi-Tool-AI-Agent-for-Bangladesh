import os
import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class SearchQueryInput(BaseModel):
    query: str = Field(description="The general knowledge question or topic to search on the web")

class WebSearchTool(BaseTool):
    """Tool for answering general knowledge, policy, and contextual queries via web search."""

    name: str = "WebSearchTool"
    description: str = (
        "Useful for general knowledge queries, government policies, definitions, "
        "history, regulations, and cultural context about Bangladesh (e.g. healthcare policies, "
        "role of government agencies, economic updates). Do NOT use for data queries stored in the local databases."
    )
    args_schema: Type[BaseModel] = SearchQueryInput
    llm: Optional[Any] = None
    tavily_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None

    def __init__(
        self,
        llm: Optional[Any] = None,
        tavily_api_key: Optional[str] = None,
        serpapi_api_key: Optional[str] = None,
        **kwargs
    ):
        t_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        s_key = serpapi_api_key or os.getenv("SERPAPI_API_KEY")
        super().__init__(
            llm=llm,
            tavily_api_key=t_key,
            serpapi_api_key=s_key,
            **kwargs
        )

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search using DuckDuckGo via ddgs library."""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                formatted = []
                for r in results:
                    formatted.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "") or r.get("snippet", ""),
                        "url": r.get("href", "") or r.get("link", "")
                    })
                return formatted
        except Exception as e:
            logger.warning(f"DDGS direct search failed: {e}, attempting langchain wrapper fallback")

        # Fallback to langchain DuckDuckGoSearchRun
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            runner = DuckDuckGoSearchRun()
            text_result = runner.run(query)
            if text_result:
                return [{"title": "Web Search Result", "snippet": text_result, "url": "https://duckduckgo.com"}]
        except Exception as e2:
            logger.error(f"DuckDuckGo search fallback failed: {e2}")

        return []

    def _search_tavily(self, query: str) -> List[Dict[str, str]]:
        """Search using Tavily API if key is present."""
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            tavily_tool = TavilySearchResults(api_key=self.tavily_api_key, max_results=5)
            raw = tavily_tool.run(query)
            if isinstance(raw, list):
                return [
                    {
                        "title": item.get("title", "Tavily Result"),
                        "snippet": item.get("content", ""),
                        "url": item.get("url", "")
                    }
                    for item in raw if isinstance(item, dict)
                ]
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
        return []

    def perform_search(self, query: str) -> List[Dict[str, str]]:
        """Perform search trying preferred providers with automatic fallback."""
        if self.tavily_api_key:
            results = self._search_tavily(query)
            if results:
                return results

        return self._search_duckduckgo(query)

    def format_search_results(self, query: str, search_items: List[Dict[str, str]]) -> str:
        """Format search results into natural language response."""
        if not search_items:
            return f"No relevant web search results found for query: '{query}'."

        if self.llm:
            try:
                snippets_text = "\n\n".join(
                    f"[{i+1}] Title: {item['title']}\nSnippet: {item['snippet']}\nSource: {item['url']}"
                    for i, item in enumerate(search_items[:5])
                )
                prompt = (
                    f"You are an AI research assistant. Synthesize a concise, factual, and clear answer "
                    f"to the user's question using the provided web search results. Cite relevant sources if applicable.\n\n"
                    f"User Question: {query}\n\n"
                    f"Search Findings:\n{snippets_text}\n\n"
                    f"Answer:"
                )
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.warning(f"LLM search synthesis failed, using formatted snippets: {e}")

        # Deterministic summary if LLM not present
        output_lines = [f"Web search findings for '{query}':\n"]
        for i, item in enumerate(search_items[:4], start=1):
            title = item.get("title", "Reference")
            snippet = item.get("snippet", "").strip()
            url = item.get("url", "")
            output_lines.append(f"{i}. **{title}**\n   {snippet}\n   Source: {url}\n")

        return "\n".join(output_lines)

    def _run(self, query: str) -> str:
        """Execute web search tool."""
        try:
            items = self.perform_search(query)
            return self.format_search_results(query, items)
        except Exception as e:
            logger.error(f"WebSearchTool failed for query '{query}': {e}")
            return f"An error occurred while performing web search: {str(e)}"
