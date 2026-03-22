"""Web crawling and scraping tools."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

HEADERS = {
    "User-Agent": "Vision1M-Scorecard-Bot/1.0 (research; University of Waterloo)"
}


@tool
def fetch_page(url: str) -> str:
    """Fetch a webpage and return its text content (HTML tags stripped).
    Use this to scrape data from government websites, municipal portals, and reports.
    Returns cleaned text content from the page (max 8000 chars).
    """
    resp = httpx.get(url, timeout=30, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text[:8000]


@tool
def fetch_tables(url: str) -> str:
    """Fetch a webpage and extract all HTML tables as text.
    Use this when the data you need is in an HTML table on a webpage.
    Returns tables formatted as pipe-separated rows.
    """
    resp = httpx.get(url, timeout=30, follow_redirects=True, headers=HEADERS)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")

    if not tables:
        return "No tables found on this page."

    parts = []
    for i, table in enumerate(tables):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            parts.append(f"=== Table {i+1} ===\n" + "\n".join(rows))

    return "\n\n".join(parts)[:8000] if parts else "Tables found but empty."


@tool
def check_url(url: str) -> str:
    """Check if a URL is accessible and returns a valid response.
    Use this to verify that a data source URL is live before attempting extraction.
    Returns status code and content type.
    """
    try:
        resp = httpx.head(url, timeout=15, follow_redirects=True, headers=HEADERS)
        content_type = resp.headers.get("content-type", "unknown")
        return f"Status: {resp.status_code}, Content-Type: {content_type}"
    except httpx.HTTPError as e:
        return f"Error: {e}"
