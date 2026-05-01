"""
news_fetcher.py
Fetches fresh news (last 24-48 hrs) across all 5 content pillars:
  1. RBI / Regulatory / NBFC
  2. RCA / FMEA / Complaint Governance
  3. Lean Six Sigma / Business Excellence
  4. PMO / Change Management / GenAI in BFSI
  5. RBI website direct scrape (authoritative source)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import config


NEWS_QUERIES = {
    "regulatory": [
        "RBI India banking",
        "NBFC India regulation",
        "NBFC regulation RBI India",
        "RBI inspection NBFC compliance",
        "KFS key fact statement RBI",
    ],
    "rca_fmea": [
        "root cause analysis banking India",
        "FMEA process quality BFSI",
        "complaint governance banking RBI",
        "operational risk banking India",
    ],
    "lean_excellence": [
        "Lean Six Sigma banking India",
        "process excellence BFSI India",
        "operational efficiency NBFC bank",
        "Kaizen business transformation India",
        "DMAIC process improvement banking",
    ],
    "pmo_genai": [
        "GenAI banking India 2025",
        "AI adoption BFSI India",
        "digital transformation NBFC India",
        "change management banking India",
        "paperless banking RBI India",
    ],
}


# ─────────────────────────────────────────────────────────────
# 1. NewsAPI
# ─────────────────────────────────────────────────────────────

def fetch_newsapi(pillar: str, max_articles: int = 4) -> list[dict]:
    if not config.NEWS_API_KEY:
        return []

    queries   = NEWS_QUERIES.get(pillar, NEWS_QUERIES["regulatory"])
    query_str = " OR ".join(q for q in queries[:3])
    yesterday = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        query_str,
                "from":     yesterday,
                "sortBy":   "relevancy",
                "language": "en",
                "pageSize": max_articles,
                "apiKey":   config.NEWS_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "title":       a.get("title", ""),
                "description": a.get("description", ""),
                "url":         a.get("url", ""),
                "source":      a.get("source", {}).get("name", "NewsAPI"),
                "pillar":      pillar,
            }
            for a in articles if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception as e:
        print(f"[NewsAPI] {pillar} error: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# 2. RBI Website Scraper (always fresh)
# ─────────────────────────────────────────────────────────────

def fetch_rbi_website() -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JayeshAgent/1.0)"}
    items   = []

    sources = [
        ("https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx", "RBI Press Release"),
        ("https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx", "RBI Circular"),
    ]

    for url, label in sources:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")

            rows = soup.select("table tr")
            for row in rows[:15]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    date_text  = cells[0].get_text(strip=True)
                    title_text = cells[1].get_text(strip=True)
                    link_tag   = cells[1].find("a")
                    href = ""
                    if link_tag and link_tag.get("href"):
                        href = "https://www.rbi.org.in" + link_tag["href"]

                    if title_text and len(title_text) > 15:
                        items.append({
                            "title":       title_text,
                            "description": f"{label} issued on {date_text}",
                            "url":         href or url,
                            "source":      label,
                            "pillar":      "regulatory",
                        })
                    if len(items) >= 3:
                        break
        except Exception as e:
            print(f"[RBI Scraper] {label}: {e}")

    return items


# ─────────────────────────────────────────────────────────────
# 3. Static Fallback Topics
# ─────────────────────────────────────────────────────────────

FALLBACK_TOPICS = {
    "regulatory": {
        "title":       "RBI's Fair Practice Code — What Every NBFC Must Know",
        "description": "RBI's FPC directions mandate transparent communication, fair pricing, and grievance redressal across all NBFC products.",
        "source":      "RBI Master Direction (Fallback)",
        "url":         "https://www.rbi.org.in",
        "pillar":      "regulatory",
    },
    "rca_fmea": {
        "title":       "Why Most Banks Fix Symptoms Instead of Root Causes",
        "description": "Without structured RCA frameworks like FMEA and 5 Whys, complaint recurrence remains high in BFSI operations.",
        "source":      "Process Excellence (Fallback)",
        "url":         "",
        "pillar":      "rca_fmea",
    },
    "lean_excellence": {
        "title":       "DMAIC in Banking — Reducing TAT Without Adding Headcount",
        "description": "Lean Six Sigma's DMAIC methodology has been successfully applied to reduce loan processing TAT and operational costs in Indian banks.",
        "source":      "Business Excellence (Fallback)",
        "url":         "",
        "pillar":      "lean_excellence",
    },
    "pmo_genai": {
        "title":       "GenAI Adoption in Indian BFSI — Where Are We in 2025?",
        "description": "Indian banks and NBFCs are piloting GenAI for customer service, compliance monitoring, and underwriting automation.",
        "source":      "BFSI Technology (Fallback)",
        "url":         "",
        "pillar":      "pmo_genai",
    },
    "any": {
        "title":       "Operational Excellence in BFSI — The Compliance-Quality Connect",
        "description": "Best-in-class BFSI institutions are integrating compliance governance with operational excellence frameworks for sustainable performance.",
        "source":      "BFSI Excellence (Fallback)",
        "url":         "",
        "pillar":      "regulatory",
    },
}


# ─────────────────────────────────────────────────────────────
# 4. Main entry point
# ─────────────────────────────────────────────────────────────

def get_news_for_pillar(pillar: str, recent_topics: list[str] = None) -> list[dict]:
    """
    Returns 4-6 fresh news items for a given pillar.
    Filters out topics already covered recently.
    """
    recent_topics = recent_topics or []

    # Always get RBI for regulatory pillar
    rbi_news  = fetch_rbi_website() if pillar in ("regulatory", "any") else []
    api_news  = fetch_newsapi(pillar, max_articles=5)

    combined = rbi_news + api_news

    # Deduplicate
    seen, unique = set(), []
    for item in combined:
        key = item["title"].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    # Filter recently used topics
    if recent_topics:
        filtered = [
            item for item in unique
            if not any(
                rt in item["title"].lower()
                for rt in recent_topics[:10]
                if len(rt) > 6
            )
        ]
        unique = filtered if filtered else unique  # fallback to unfiltered if all filtered out

    # Add fallback if empty
    if not unique:
        fallback = FALLBACK_TOPICS.get(pillar, FALLBACK_TOPICS["regulatory"])
        unique   = [fallback]
        print(f"[News] Using fallback for pillar: {pillar}")

    print(f"[News] {len(unique)} items fetched for pillar: {pillar}")
    return unique[:6]


if __name__ == "__main__":
    for pillar in ["regulatory", "rca_fmea", "lean_excellence", "pmo_genai"]:
        print(f"\n── {pillar.upper()} ──")
        items = get_news_for_pillar(pillar)
        for item in items:
            print(f"  [{item['source']}] {item['title'][:70]}")
