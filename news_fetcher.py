"""
news_fetcher.py - Parallel fetching + HBR articles + rotating fallbacks
"""

import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

# ── Harvard Business Review RSS Feeds ─────────────────────
HBR_FEEDS = {
    "ai":                 "https://hbr.org/rss/topic/ai",
    "project_management": "https://hbr.org/rss/topic/project-management",
    "technology":         "https://hbr.org/rss/topic/technology",
    "leadership":         "https://hbr.org/rss/topic/leadership",
    "operations":         "https://hbr.org/rss/topic/operations-strategy",
    "change_management":  "https://hbr.org/rss/topic/change-management",
}

# ── MIT Sloan RSS (backup for HBR) ────────────────────────
MIT_SLOAN_FEED = "https://sloanreview.mit.edu/rss/article/"

# ── NewsAPI Queries ────────────────────────────────────────
NEWS_QUERIES = {
    "regulatory":         "RBI India banking regulation",
    "rca_fmea":           "quality management banking India",
    "lean_excellence":    "Lean Six Sigma India",
    "pmo_genai":          "AI banking India",
    "personal_excellence":"leadership banking India",
    "industry_trends":    "Indian banking sector",
    "any":                "RBI India banking",
}

# ── Rotating Fallback Topics (30 evergreen — never repeats) ──
FALLBACK_ROTATION = [
    {"title":"RBI's Fair Practice Code — Embedding Compliance into Operations","pillar":"regulatory"},
    {"title":"Why Most Banks Fix Symptoms Instead of Root Causes","pillar":"rca_fmea"},
    {"title":"DMAIC in Banking — Reducing TAT Without Adding Headcount","pillar":"lean_excellence"},
    {"title":"GenAI Adoption in Indian BFSI — 2025 Update","pillar":"pmo_genai"},
    {"title":"PPG Framework Governance — The Bajaj Finance Approach","pillar":"regulatory"},
    {"title":"5 Whys in NBFC Complaint Resolution — A Practitioner Guide","pillar":"rca_fmea"},
    {"title":"Kaizen Blitz Events — How Indian Banks Cut TAT by 40%","pillar":"lean_excellence"},
    {"title":"PRINCE2 in BFSI — Making Projects Delivery-Ready","pillar":"pmo_genai"},
    {"title":"KYC Compliance — Moving From Checklist to Customer Experience","pillar":"regulatory"},
    {"title":"FMEA in Banking — Preventing Failures Before They Happen","pillar":"rca_fmea"},
    {"title":"Value Stream Mapping in Loan Processing — Real Results","pillar":"lean_excellence"},
    {"title":"AI-Powered Audit Readiness — The Future of NBFC Compliance","pillar":"pmo_genai"},
    {"title":"RBI Inspection Readiness — 90 Days to Zero Observations","pillar":"regulatory"},
    {"title":"Building India's First RCA Governance Unit in BFSI","pillar":"rca_fmea"},
    {"title":"5S Implementation in Service Branches — Before and After","pillar":"lean_excellence"},
    {"title":"Change Management in NBFC Digital Transformation","pillar":"pmo_genai"},
    {"title":"NPA Prevention Through Early Warning Systems — RCA Approach","pillar":"rca_fmea"},
    {"title":"SOP Lifecycle Governance — Beyond Documentation","pillar":"regulatory"},
    {"title":"Lean Six Sigma Black Belt Projects in Indian Banking","pillar":"lean_excellence"},
    {"title":"Board-Level Compliance Reporting — Making Data Tell a Story","pillar":"regulatory"},
    {"title":"Customer Complaint Reduction — From 300 to Under 10 Monthly","pillar":"rca_fmea"},
    {"title":"Business Continuity Planning — COVID Lessons for NBFC Leaders","pillar":"pmo_genai"},
    {"title":"Process Reengineering in Loan Origination — A DMAIC Journey","pillar":"lean_excellence"},
    {"title":"Digital KYC — Achieving 100% Paperless Sourcing","pillar":"pmo_genai"},
    {"title":"Fishbone Analysis for EMI Debit Errors — Step by Step","pillar":"rca_fmea"},
    {"title":"RBI's Revised NBFC Framework — What Compliance Teams Must Do","pillar":"regulatory"},
    {"title":"Operational Excellence Awards — What Separates Winners","pillar":"lean_excellence"},
    {"title":"GenAI for Compliance Monitoring — Practical BFSI Use Cases","pillar":"pmo_genai"},
    {"title":"Zero Critical Audit Observations — A Framework That Works","pillar":"regulatory"},
    {"title":"Mentoring Green Belt Projects — Lessons From 20+ Projects","pillar":"lean_excellence"},
]

_fallback_index = 0

def get_next_fallback(pillar: str = None) -> dict:
    """Get next fallback topic — rotates through 30 topics, never repeats."""
    global _fallback_index
    topics = FALLBACK_ROTATION
    if pillar:
        pillar_topics = [t for t in topics if t["pillar"] == pillar]
        if pillar_topics:
            topics = pillar_topics

    topic = topics[_fallback_index % len(topics)]
    _fallback_index += 1
    return {
        "title":       topic["title"],
        "description": f"Deep-dive into {topic['title']}",
        "source":      "Evergreen Topic",
        "url":         "",
        "pillar":      topic["pillar"],
        "is_fallback": True,
    }


# ── Harvard Business Review Fetcher ───────────────────────

def fetch_hbr_articles(topics: list = None, max_items: int = 3) -> list[dict]:
    """
    Fetch HBR-style articles on AI and project management.
    Uses NewsAPI with trusted sources since HBR blocks direct RSS.
    """
    if not config.NEWS_API_KEY:
        return []

    articles = []
    queries  = [
        "Harvard Business Review AI project management",
        "artificial intelligence project management 2025",
        "AI leadership digital transformation management",
        "generative AI business strategy management",
        "project management AI automation 2025",
    ]

    for query in queries:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "language": "en",
                    "pageSize": 3,
                    "sortBy":   "relevancy",
                    "apiKey":   config.NEWS_API_KEY,
                },
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get("articles", [])
            for a in items:
                if a.get("title") and "[Removed]" not in a.get("title",""):
                    articles.append({
                        "title":       a.get("title",""),
                        "description": a.get("description","")[:300],
                        "url":         a.get("url",""),
                        "source":      a.get("source",{}).get("name","Management Review"),
                        "pillar":      "pmo_genai",
                        "image_url":   a.get("urlToImage",""),
                        "is_hbr":      True,
                    })
            if len(articles) >= max_items:
                break
        except Exception as e:
            print(f"[HBR/NewsAPI] {query[:30]} error: {e}")

    print(f"[HBR] Fetched {len(articles[:max_items])} articles")
    return articles[:max_items]


def _extract_hbr_image(url: str, headers: dict) -> str:
    """Try to extract the main image from an HBR article page."""
    if not url:
        return ""
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Try Open Graph image first (most reliable)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        # Try article hero image
        img = soup.find("img", class_=lambda c: c and "hero" in c.lower() if c else False)
        if img and img.get("src"):
            return img["src"]

    except Exception as e:
        print(f"[HBR] Image extract error: {e}")
    return ""


def fetch_mit_sloan(max_items: int = 2) -> list[dict]:
    """Fetch MIT Sloan Management Review articles as HBR backup."""
    articles = []
    try:
        feed = feedparser.parse(MIT_SLOAN_FEED)
        for entry in feed.entries[:max_items]:
            # Filter for AI/PM related articles
            title = entry.get("title","").lower()
            if any(kw in title for kw in ["ai","artificial","project","management","digital","technology","lean","agile"]):
                articles.append({
                    "title":       entry.get("title",""),
                    "description": entry.get("summary","")[:300],
                    "url":         entry.get("link",""),
                    "source":      "MIT Sloan Management Review",
                    "pillar":      "pmo_genai",
                    "image_url":   "",
                    "is_hbr":      True,
                })
    except Exception as e:
        print(f"[MIT Sloan] Error: {e}")
    return articles


# ── NewsAPI Fetcher ────────────────────────────────────────

def fetch_newsapi(pillar: str, max_articles: int = 4) -> list[dict]:
    if not config.NEWS_API_KEY:
        return []
    query     = NEWS_QUERIES.get(pillar, "RBI India banking")
    yesterday = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        query,
                "from":     yesterday,
                "sortBy":   "relevancy",
                "language": "en",
                "pageSize": max_articles,
                "apiKey":   config.NEWS_API_KEY,
            },
            timeout=8,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles",[])
        return [
            {
                "title":       a.get("title",""),
                "description": a.get("description",""),
                "url":         a.get("url",""),
                "source":      a.get("source",{}).get("name","NewsAPI"),
                "pillar":      pillar,
                "image_url":   a.get("urlToImage",""),
                "is_hbr":      False,
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title","")
        ]
    except Exception as e:
        print(f"[NewsAPI] {pillar} error: {e}")
        return []


# ── RBI Scraper ────────────────────────────────────────────

def fetch_rbi_website() -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0"}
    items   = []
    sources = [
        ("https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx","RBI Press Release"),
        ("https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx","RBI Circular"),
    ]
    for url, label in sources:
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            soup = BeautifulSoup(resp.text,"html.parser")
            for row in soup.select("table tr")[:15]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    date_text  = cells[0].get_text(strip=True)
                    title_text = cells[1].get_text(strip=True)
                    link_tag   = cells[1].find("a")
                    href = ("https://www.rbi.org.in"+link_tag["href"]) if link_tag and link_tag.get("href") else url
                    if title_text and len(title_text) > 15:
                        items.append({
                            "title":       title_text,
                            "description": f"{label} issued on {date_text}",
                            "url":         href,
                            "source":      label,
                            "pillar":      "regulatory",
                            "image_url":   "",
                            "is_hbr":      False,
                        })
                    if len(items) >= 3:
                        break
        except Exception as e:
            print(f"[RBI] {label}: {e}")
    return items


# ── PARALLEL Main Fetcher ──────────────────────────────────

def get_news_for_pillar(
    pillar: str,
    recent_topics: list = None,
    include_hbr: bool = False
) -> list[dict]:
    """
    Fetch news in PARALLEL for speed.
    RBI scraper + NewsAPI run simultaneously.
    Returns deduplicated list.
    """
    recent_topics = recent_topics or []

    # Run fetchers in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        if pillar in ("regulatory","any"):
            futures[executor.submit(fetch_rbi_website)] = "rbi"

        futures[executor.submit(fetch_newsapi, pillar, 5)] = "newsapi"

        if include_hbr or pillar == "pmo_genai":
            futures[executor.submit(fetch_hbr_articles, ["ai","project_management"])] = "hbr"

        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"[Fetch] {key} error: {e}")
                results[key] = []

    # Merge results — RBI first (most authoritative)
    combined = (
        results.get("rbi",[]) +
        results.get("newsapi",[]) +
        results.get("hbr",[])
    )

    # Deduplicate
    seen, unique = set(), []
    for item in combined:
        key = item["title"].lower()[:50]
        if key not in seen and item["title"]:
            seen.add(key)
            unique.append(item)

    # Filter recently used topics
    if recent_topics:
        filtered = [
            i for i in unique
            if not any(
                rt in i["title"].lower()
                for rt in recent_topics[:10]
                if len(rt) > 6
            )
        ]
        unique = filtered if filtered else unique

    # Fallback if still empty
    if not unique:
        unique = [get_next_fallback(pillar)]
        print(f"[News] Using rotating fallback for pillar: {pillar}")

    print(f"[News] {len(unique)} items fetched for pillar: {pillar}")
    return unique[:6]


def get_hbr_for_post() -> list[dict]:
    """Dedicated function to get HBR articles for standalone HBR posts."""
    articles = fetch_hbr_articles(
        topics=["ai","project_management","technology","operations","change_management"],
        max_items=4
    )
    if not articles:
        articles = fetch_mit_sloan(max_items=3)
    return articles


if __name__ == "__main__":
    print("\n── HBR Articles ──")
    for a in fetch_hbr_articles(["ai","project_management"], max_items=3):
        print(f"  [{a['source']}] {a['title'][:70]}")
        print(f"  Image: {a.get('image_url','none')[:60]}")

    print("\n── Regulatory News ──")
    for a in get_news_for_pillar("regulatory"):
        print(f"  [{a['source']}] {a['title'][:70]}")
