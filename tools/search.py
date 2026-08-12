"""Tavily wrapper — free tier, needs an email-signup API key.
Get your key at https://tavily.com
"""
import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


def tavily_search(query: str, max_results: int = 5) -> list:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise EnvironmentError("TAVILY_API_KEY missing from .env")

    client = TavilyClient(api_key=key)
    results = client.search(query, max_results=max_results)
    return [r["content"] for r in results.get("results", [])]


if __name__ == "__main__":
    print(tavily_search("best things to do in Jaipur"))
