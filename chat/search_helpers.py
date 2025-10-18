# chat/search_helpers.py
import requests
from bs4 import BeautifulSoup

def duckduckgo_search(query, num=5):
    """Kostenlose Websuche via DuckDuckGo HTML-Scraping"""
    try:
        url = f"https://duckduckgo.com/html/?q={query}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for a in soup.select(".result__a")[:num]:
            link = a.get("href")
            title = a.get_text()
            snippet_tag = a.find_parent("div", class_="result__snippet")
            snippet = snippet_tag.get_text() if snippet_tag else ""
            results.append({
                "title": title.strip(),
                "snippet": snippet.strip(),
                "link": link
            })
        return results
    except Exception:
        return []

def web_search(query, num=5):
    """Globale kostenlose Suche"""
    return duckduckgo_search(query, num=num)
