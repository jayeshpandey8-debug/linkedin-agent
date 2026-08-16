"""
news_fetcher.py - Parallel fetching + HBR articles + rotating fallbacks
regulatory pillar targets actual RBI circulars/publications + Govt BFSI policy.
ai_genai pillar targets world AI news with pros/cons. pmp pillar targets PMI/PMP
practice. change_management pillar targets RCA/FMEA/Lean Six Sigma/change execution.
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

# ── NewsAPI Queries — per pillar focus ────────────────────
NEWS_QUERIES = {
    "regulatory":         "RBI master direction circular notification",
    "ai_genai":           "artificial intelligence pros cons global",
    "pmp":                "PMI PMP project management",
    "change_management":  "change management Lean Six Sigma India",
    "any":                "RBI India banking",
}

# Secondary query pools — rotated to add variety while staying anchored
# to the sharpened focus areas
REGULATORY_QUERY_POOL = [
    "RBI master direction circular",
    "RBI notification NBFC banking",
    "RBI press release",
    "Ministry of Finance BFSI policy India",
    "India government financial sector reform",
    "RBI policy implementation NBFC execution",
]

PMP_QUERY_POOL = [
    "PMI project management methodology",
    "PMP project management practice",
    "PMBOK agile waterfall project",
    "program governance stakeholder management",
]

WORLD_AI_QUERY_POOL = [
    "artificial intelligence pros cons",
    "AI regulation world global",
    "AI risks benefits debate",
    "AI safety ethics global",
    "generative AI adoption world",
]

CHANGE_MGMT_QUERY_POOL = [
    "change management India",
    "Lean Six Sigma India",
    "operational excellence India",
    "root cause analysis banking India",
    "process improvement BFSI India",
]

_reg_query_index    = 0
_pmp_query_index    = 0
_ai_query_index     = 0
_change_query_index = 0


def _next_from_pool(pool: list, counter_name: str) -> str:
    """Rotate through a query pool so consecutive runs use different angles."""
    global _reg_query_index, _pmp_query_index, _ai_query_index, _change_query_index
    if counter_name == "regulatory":
        q = pool[_reg_query_index % len(pool)]
        _reg_query_index += 1
    elif counter_name == "pmp":
        q = pool[_pmp_query_index % len(pool)]
        _pmp_query_index += 1
    elif counter_name == "change":
        q = pool[_change_query_index % len(pool)]
        _change_query_index += 1
    else:
        q = pool[_ai_query_index % len(pool)]
        _ai_query_index += 1
    return q


# ── Rotating Fallback Topics (30 evergreen — never repeats) ──
FALLBACK_ROTATION = [
    {"title":"RBI's Fair Practice Code — Embedding Compliance into Operations","pillar":"regulatory"},
    {"title":"Why Most Banks Fix Symptoms Instead of Root Causes","pillar":"change_management"},
    {"title":"DMAIC in Banking — Reducing TAT Without Adding Headcount","pillar":"change_management"},
    {"title":"PMI Practices in BFSI Project Delivery — What Actually Works","pillar":"pmp"},
    {"title":"PPG Framework Governance — The Bajaj Finance Approach","pillar":"regulatory"},
    {"title":"5 Whys in NBFC Complaint Resolution — A Practitioner Guide","pillar":"change_management"},
    {"title":"Kaizen Blitz Events — How Indian Banks Cut TAT by 40%","pillar":"change_management"},
    {"title":"PMP Methodology vs Agile — Choosing the Right Approach for BFSI Projects","pillar":"pmp"},
    {"title":"KYC Compliance — Moving From Checklist to Customer Experience","pillar":"regulatory"},
    {"title":"FMEA in Banking — Preventing Failures Before They Happen","pillar":"change_management"},
    {"title":"Value Stream Mapping in Loan Processing — Real Results","pillar":"change_management"},
    {"title":"World AI Development — Weighing the Promise Against the Risk","pillar":"ai_genai"},
    {"title":"RBI Inspection Readiness — 90 Days to Zero Observations","pillar":"regulatory"},
    {"title":"Building India's First RCA Governance Unit in BFSI","pillar":"change_management"},
    {"title":"5S Implementation in Service Branches — Before and After","pillar":"change_management"},
    {"title":"PMI Risk Register Practices — Why Most Projects Skip This Step","pillar":"pmp"},
    {"title":"NPA Prevention Through Early Warning Systems — RCA Approach","pillar":"change_management"},
    {"title":"SOP Lifecycle Governance — Beyond Documentation","pillar":"regulatory"},
    {"title":"Lean Six Sigma Black Belt Projects in Indian Banking","pillar":"change_management"},
    {"title":"Board-Level Compliance Reporting — Making Data Tell a Story","pillar":"regulatory"},
    {"title":"Customer Complaint Reduction — From 300 to Under 10 Monthly","pillar":"change_management"},
    {"title":"AI Job Displacement Debate — What the Data Actually Shows","pillar":"ai_genai"},
    {"title":"Process Reengineering in Loan Origination — A DMAIC Journey","pillar":"change_management"},
    {"title":"India's BFSI Policy Execution — From Announcement to Implementation","pillar":"regulatory"},
    {"title":"Fishbone Analysis for EMI Debit Errors — Step by Step","pillar":"change_management"},
    {"title":"RBI's Revised NBFC Framework — What Compliance Teams Must Do","pillar":"regulatory"},
    {"title":"Operational Excellence Awards — What Separates Winners","pillar":"change_management"},
    {"title":"PMBOK Earned Value Management — A Practitioner's Take","pillar":"pmp"},
    {"title":"Zero Critical Audit Observations — A Framework That Works","pillar":"regulatory"},
    {"title":"AI Agents in Enterprise Workflows — Promise vs Practical Reality","pillar":"ai_genai"},
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
        "artificial intelligence project management 2026",
        "AI leadership digital transformation management",
        "generative AI business strategy management",
        "project management AI automation 2026",
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
                        "pillar":      "ai_genai",
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
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
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
            title = entry.get("title","").lower()
            if any(kw in title for kw in ["ai","artificial","project","management","digital","technology","lean","agile"]):
                articles.append({
                    "title":       entry.get("title",""),
                    "description": entry.get("summary","")[:300],
                    "url":         entry.get("link",""),
                    "source":      "MIT Sloan Management Review",
                    "pillar":      "ai_genai",
                    "image_url":   "",
                    "is_hbr":      True,
                })
    except Exception as e:
        print(f"[MIT Sloan] Error: {e}")
    return articles


# ── NewsAPI Fetcher — SHARPENED ────────────────────────────

def fetch_newsapi(pillar: str, max_articles: int = 4) -> list[dict]:
    """
    Fetch news for a pillar.
    For 'regulatory' — rotates through RBI circular/policy-execution queries.
    For 'ai_genai' — rotates through world-AI-pros/cons queries.
    For 'pmp' — rotates through PMI/PMP practice queries.
    For 'change_management' — rotates through change/RCA/Lean queries.
    """
    if not config.NEWS_API_KEY:
        return []

    yesterday = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")

    def _call(query, page_size):
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "from":     yesterday,
                    "sortBy":   "relevancy",
                    "language": "en",
                    "pageSize": page_size,
                    "apiKey":   config.NEWS_API_KEY,
                },
                timeout=8,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
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
            print(f"[NewsAPI] '{query[:40]}' error: {e}")
            return []

    if pillar == "regulatory":
        query = _next_from_pool(REGULATORY_QUERY_POOL, "regulatory")
        results = _call(query, max_articles)
        if len(results) < 2:
            # widen if rotation query came up dry
            results += _call("RBI India banking regulation", max_articles)
        return results

    if pillar == "ai_genai":
        query = _next_from_pool(WORLD_AI_QUERY_POOL, "ai")
        results = _call(query, max_articles)
        if len(results) < 2:
            results += _call("artificial intelligence world", max_articles)
        return results

    if pillar == "pmp":
        query = _next_from_pool(PMP_QUERY_POOL, "pmp")
        results = _call(query, max_articles)
        if len(results) < 2:
            results += _call("project management practice", max_articles)
        return results

    if pillar == "change_management":
        query = _next_from_pool(CHANGE_MGMT_QUERY_POOL, "change")
        results = _call(query, max_articles)
        if len(results) < 2:
            results += _call("Lean Six Sigma change management India", max_articles)
        return results

    query = NEWS_QUERIES.get(pillar, "RBI India banking")
    return _call(query, max_articles)


# ── RBI Scraper ────────────────────────────────────────────

def fetch_rbi_website() -> list[dict]:
    """Scrape RBI press releases and circulars directly from rbi.org.in."""
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
    regulatory        → RBI scraper + RBI-circular-focused NewsAPI queries
    ai_genai          → world-AI-pros/cons NewsAPI queries + HBR
    pmp               → PMI/PMP practice NewsAPI queries + HBR
    change_management → RCA/Lean/change NewsAPI queries
    Returns deduplicated list.
    """
    recent_topics = recent_topics or []

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        if pillar in ("regulatory","any"):
            futures[executor.submit(fetch_rbi_website)] = "rbi"

        futures[executor.submit(fetch_newsapi, pillar, 5)] = "newsapi"

        if include_hbr or pillar in ("ai_genai", "pmp"):
            futures[executor.submit(fetch_hbr_articles, ["ai","project_management"])] = "hbr"

        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                print(f"[Fetch] {key} error: {e}")
                results[key] = []

    combined = (
        results.get("rbi",[]) +
        results.get("newsapi",[]) +
        results.get("hbr",[])
    )

    seen, unique = set(), []
    for item in combined:
        key = item["title"].lower()[:50]
        if key not in seen and item["title"]:
            seen.add(key)
            unique.append(item)

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
    print("\n── Regulatory (RBI circulars) ──")
    for a in get_news_for_pillar("regulatory"):
        print(f"  [{a['source']}] {a['title'][:70]}")

    print("\n── AI/GenAI (world AI pros/cons) ──")
    for a in get_news_for_pillar("ai_genai"):
        print(f"  [{a['source']}] {a['title'][:70]}")

    print("\n── PMP (PMI/PMP practice) ──")
    for a in get_news_for_pillar("pmp"):
        print(f"  [{a['source']}] {a['title'][:70]}")

    print("\n── Change Management (RCA/Lean/Change) ──")
    for a in get_news_for_pillar("change_management"):
        print(f"  [{a['source']}] {a['title'][:70]}")
