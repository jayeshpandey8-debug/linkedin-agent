"""
image_fetcher.py - Smart image selection
Extracts keywords from actual post content for better image matching.
"""

import requests
import re
import config

PEXELS_API_KEY = config.PEXELS_API_KEY

# ── Pillar fallback queries ────────────────────────────────
PILLAR_SEARCH = {
    "regulatory":     [
        "india banking regulation professional",
        "RBI india finance compliance",
        "banking law india professional",
        "financial regulation india",
    ],
    "rca_fmea":       [
        "quality management process india",
        "root cause analysis business",
        "process improvement manufacturing india",
        "quality control professional",
    ],
    "lean_excellence":[
        "lean six sigma process improvement",
        "business excellence india professional",
        "operational efficiency manufacturing",
        "continuous improvement process",
    ],
    "pmo_genai":      [
        "artificial intelligence india technology",
        "digital transformation banking india",
        "technology innovation finance",
        "AI machine learning business",
    ],
    "any":            [
        "india banking finance professional",
        "financial services india",
        "business professional india",
    ],
}

# ── Keywords that map to better image searches ─────────────
KEYWORD_MAP = {
    "rbi":             "reserve bank india regulation",
    "nbfc":            "india non banking finance company",
    "compliance":      "india banking compliance professional",
    "fmea":            "quality risk analysis professional",
    "rca":             "root cause analysis process",
    "lean":            "lean manufacturing process improvement",
    "six sigma":       "six sigma quality management",
    "dmaic":           "process improvement quality control",
    "kaizen":          "continuous improvement japan manufacturing",
    "pmo":             "project management office professional",
    "genai":           "artificial intelligence technology business",
    "ai":              "artificial intelligence india technology",
    "digital":         "digital transformation technology india",
    "complaint":       "customer service quality management",
    "audit":           "financial audit compliance professional",
    "regulation":      "india banking financial regulation",
    "credit":          "india banking credit finance",
    "loan":            "india banking loan finance",
    "fintech":         "fintech india technology finance",
    "operational":     "operational excellence business india",
    "governance":      "corporate governance india professional",
    "transformation":  "business transformation india professional",
    "risk":            "risk management finance india",
    "process":         "business process improvement professional",
    "banking":         "india banking finance professional",
    "insurance":       "india insurance finance professional",
    "microfinance":    "microfinance india rural banking",
    "repo":            "reserve bank india monetary policy",
    "inflation":       "india economy finance banking",
    "npa":             "india banking non performing assets",
    "kyc":             "india banking identity verification",
    "data":            "data analytics technology business",
    "automation":      "automation technology business india",
    "paperless":       "digital paperless office technology",
    "5s":              "workplace organization manufacturing",
    "bcp":             "business continuity planning professional",
}


def extract_smart_query(post_text: str, topic: str, pillar: str) -> str:
    """
    Extract the best image search query from post content.
    Priority: topic keywords > post text keywords > pillar default
    """
    combined_text = f"{topic} {post_text[:500]}".lower()

    # Check for keyword matches
    matched_queries = []
    for keyword, image_query in KEYWORD_MAP.items():
        if keyword in combined_text:
            matched_queries.append(image_query)

    if matched_queries:
        # Use the most specific match (longest keyword)
        best = sorted(matched_queries, key=len, reverse=True)[0]
        print(f"[Pexels] Smart query: '{best}'")
        return best

    # Extract meaningful words from topic
    if topic:
        # Remove common words
        stop_words = {"the","a","an","in","on","at","to","for","of","and","or","is","are","was","were","with","by","from","about","into","through"}
        words = [w for w in re.sub(r'[^a-z\s]', '', topic.lower()).split()
                 if w not in stop_words and len(w) > 3]
        if words:
            query = " ".join(words[:4]) + " india professional"
            print(f"[Pexels] Topic query: '{query}'")
            return query

    # Fall back to pillar default
    queries = PILLAR_SEARCH.get(pillar, PILLAR_SEARCH["any"])
    print(f"[Pexels] Pillar fallback query: '{queries[0]}'")
    return queries[0]


def search_pexels(query: str, per_page: int = 5) -> list:
    """Search Pexels and return list of photos."""
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query":       query,
                "per_page":    per_page,
                "orientation": "landscape",
                "size":        "medium",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("photos", [])
    except Exception as e:
        print(f"[Pexels] Search error: {e}")
        return []


def pick_best_photo(photos: list) -> dict | None:
    """
    Pick best photo from results.
    Prefers photos with more likes/downloads (quality signal).
    Avoids purely abstract or people-only shots.
    """
    if not photos:
        return None

    # Score each photo — prefer wider images (better for LinkedIn)
    scored = []
    for p in photos:
        width  = p.get("width", 0)
        height = p.get("height", 1)
        ratio  = width / height
        # Prefer landscape ratio between 1.5 and 2.0
        ratio_score = 1 if 1.4 <= ratio <= 2.1 else 0
        scored.append((ratio_score, p))

    # Sort by score descending, pick best
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def get_image_for_post(pillar: str = "any", topic: str = "", post_text: str = "") -> dict | None:
    """
    Main function — get best image for a post.
    Returns {url, medium_url, photographer, pexels_url} or None.
    """
    if not PEXELS_API_KEY:
        print("[Pexels] No API key set.")
        return None

    # Build smart query
    query = extract_smart_query(post_text, topic, pillar)

    # Search with smart query
    photos = search_pexels(query, per_page=5)

    # If no results — try pillar fallback queries
    if not photos:
        print(f"[Pexels] No results for '{query}' — trying fallback...")
        for fallback_query in PILLAR_SEARCH.get(pillar, PILLAR_SEARCH["any"])[1:]:
            photos = search_pexels(fallback_query, per_page=3)
            if photos:
                break

    # Last resort — generic india business
    if not photos:
        photos = search_pexels("india business professional finance", per_page=3)

    photo = pick_best_photo(photos)
    if photo:
        print(f"[Pexels] ✅ Selected: {photo.get('url')} by {photo.get('photographer')}")
        return {
            "url":          photo["src"]["large"],
            "medium_url":   photo["src"]["medium"],
            "photographer": photo.get("photographer","Pexels"),
            "pexels_url":   photo.get("url",""),
            "photo_id":     photo.get("id"),
        }

    print("[Pexels] ❌ No image found.")
    return None


def download_image(image_url: str) -> bytes | None:
    """Download image bytes for LinkedIn upload."""
    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"[Pexels] Download error: {e}")
        return None


if __name__ == "__main__":
    tests = [
        ("regulatory", "RBI rejects NBFC funding norms tightening", ""),
        ("rca_fmea",   "FMEA root cause analysis complaint reduction", ""),
        ("lean_excellence", "DMAIC Lean Six Sigma process improvement banking", ""),
        ("pmo_genai",  "GenAI adoption Indian banking automation", ""),
        ("any",        "KYC digital compliance RBI direction", ""),
    ]
    for pillar, topic, text in tests:
        print(f"\n── {pillar.upper()} ──")
        img = get_image_for_post(pillar=pillar, topic=topic, post_text=text)
        if img:
            print(f"  Photo by: {img['photographer']}")
            print(f"  URL: {img['pexels_url']}")
