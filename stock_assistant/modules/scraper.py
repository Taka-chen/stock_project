# -*- coding: utf-8 -*-
"""
News scraper module.
Fetches news from Google News RSS and Bing News for given stock queries.
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 12


def _clean_text(text: str) -> str:
    """Strip HTML tags and extra whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300]


def _parse_rss_date(date_str: str) -> str:
    """Convert RSS date string to readable format."""
    if not date_str:
        return ""
    try:
        for fmt in (
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%SZ",
        ):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                continue
    except Exception:
        pass
    return date_str[:16]


# ── Google News ──────────────────────────────────────────────────────────────

def fetch_google_news(query: str, market: str = "TW") -> list:
    """
    Fetch news articles from Google News RSS feed.
    Returns list of article dicts.
    """
    if market == "TW":
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote(query)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        )
    else:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        )

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return _parse_rss(resp.content, source_tag="Google News")
    except requests.RequestException as e:
        print(f"[Google News] Request failed: {e}")
        return []
    except Exception as e:
        print(f"[Google News] Parse error: {e}")
        return []


def _parse_rss(content: bytes, source_tag: str = "RSS") -> list:
    """Parse RSS XML content and return article list."""
    articles = []
    try:
        root = ET.fromstring(content)
        # Handle both RSS 2.0 and Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")

        for item in items[:10]:
            title = _clean_text(item.findtext("title", ""))
            link = item.findtext("link", "").strip()
            pub = _parse_rss_date(item.findtext("pubDate", ""))
            desc = _clean_text(item.findtext("description", ""))
            # Source from <source> sub-element
            src_el = item.find("source")
            source = src_el.text.strip() if src_el is not None and src_el.text else source_tag

            if title and link:
                articles.append({
                    "title": title,
                    "link": link,
                    "published": pub,
                    "summary": desc,
                    "source": source,
                })
    except ET.ParseError as e:
        print(f"[RSS] XML parse error: {e}")

    return articles


# ── Bing News ─────────────────────────────────────────────────────────────────

def fetch_bing_news(query: str, market: str = "TW") -> list:
    """
    Fetch news from Bing News.
    First tries RSS feed; falls back to HTML scraping.
    """
    articles = _fetch_bing_rss(query, market)
    if articles:
        return articles
    return _scrape_bing_news(query, market)


def _fetch_bing_rss(query: str, market: str) -> list:
    """Try Bing News RSS endpoint."""
    if market == "TW":
        url = (
            f"https://www.bing.com/news/search"
            f"?q={quote(query)}&format=RSS&setmkt=zh-TW&setlang=zh-TW"
        )
    else:
        url = (
            f"https://www.bing.com/news/search"
            f"?q={quote(query)}&format=RSS&setmkt=en-US"
        )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200 and b"<rss" in resp.content[:200]:
            return _parse_rss(resp.content, source_tag="Bing News")
    except Exception:
        pass
    return []


def _scrape_bing_news(query: str, market: str) -> list:
    """Scrape Bing News search results page."""
    if market == "TW":
        url = (
            f"https://www.bing.com/news/search"
            f"?q={quote(query)}&setmkt=zh-TW&setlang=zh-TW"
        )
    else:
        url = f"https://www.bing.com/news/search?q={quote(query)}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")
        articles = []

        # Bing News card selectors (multiple fallbacks)
        cards = (
            soup.select("div.news-card")
            or soup.select("div[class*='NewsCard']")
            or soup.select("div[data-tag='news']")
            or soup.select("article")
        )

        for card in cards[:10]:
            # Title + link
            link_el = (
                card.select_one("a.title")
                or card.select_one("a[class*='title']")
                or card.select_one("h3 > a")
                or card.select_one("h4 > a")
                or card.select_one("a")
            )
            if not link_el:
                continue

            title = _clean_text(link_el.get_text())
            link = link_el.get("href", "")
            if link.startswith("/"):
                link = "https://www.bing.com" + link

            # Snippet
            snippet_el = (
                card.select_one(".snippet")
                or card.select_one("div[class*='snippet']")
                or card.select_one("p")
            )
            summary = _clean_text(snippet_el.get_text()) if snippet_el else ""

            # Source / date
            source_el = (
                card.select_one(".source")
                or card.select_one("[class*='source']")
                or card.select_one("cite")
            )
            source = _clean_text(source_el.get_text()) if source_el else "Bing News"

            time_el = card.select_one("time") or card.select_one("[class*='time']")
            pub = time_el.get("datetime", time_el.get_text()) if time_el else ""
            pub = _parse_rss_date(pub) or pub[:16]

            if title and len(title) > 5:
                articles.append({
                    "title": title,
                    "link": link,
                    "published": pub,
                    "summary": summary,
                    "source": source,
                })

        return articles

    except requests.RequestException as e:
        print(f"[Bing scrape] Request failed: {e}")
        return []
    except Exception as e:
        print(f"[Bing scrape] Error: {e}")
        return []


# ── Prompt Generator ──────────────────────────────────────────────────────────

def build_claude_prompt(
    ticker: str,
    name: str,
    market: str,
    google_articles: list,
    bing_articles: list,
) -> str:
    """
    Build an optimized Claude prompt for news summarization.
    """
    market_label = "台股" if market == "TW" else "美股"

    def fmt_articles(articles: list, label: str) -> str:
        if not articles:
            return f"【{label}】\n（無法取得新聞，請稍後再試）\n"
        lines = [f"【{label}】"]
        for i, a in enumerate(articles[:6], 1):
            lines.append(f"{i}. {a['title']}")
            if a.get("published"):
                lines.append(f"   時間：{a['published']}")
            if a.get("source"):
                lines.append(f"   來源：{a['source']}")
            if a.get("summary"):
                lines.append(f"   摘要：{a['summary'][:150]}")
            lines.append("")
        return "\n".join(lines)

    google_section = fmt_articles(google_articles, "Google 新聞")
    bing_section = fmt_articles(bing_articles, "Bing 新聞")

    prompt = f"""你是一位專業的股票分析師助手。以下是關於 {name}（{ticker}，{market_label}）的最新新聞資料，請協助整理分析。

{google_section}
{bing_section}

請根據以上新聞，提供以下分析（請使用繁體中文，格式清晰）：

## 📌 重要市場動態（3-5點）
列出最關鍵的市場消息與事件。

## 📈 股價影響評估
分析這些消息對股價的可能影響：
- 正面因素：
- 負面因素：
- 整體傾向：（正面 / 負面 / 中性）

## ⚠️ 投資人需關注的風險
列出 2-3 個主要風險因素。

## 💡 短期操作參考方向
（聲明：以下僅供參考，不構成實際投資建議）

---
請盡量根據新聞內容回答，若新聞資訊不足，請說明。
"""
    return prompt.strip()
