"""
image_fetcher.py - Upgraded for human-centric, article-relevant images
Always searches for professional people images matching the article topic.
"""

import requests
import re
import config

PEXELS_API_KEY = config.PEXELS_API_KEY

# ── Human-centric pillar searches ─────────────────────────
# Every query ends with "people professional" for human presence
PILLAR_SEARCH = {
    "regulatory": [
        "indian banker professional meeting compliance",
        "business professional india banking discussion",
        "financial compliance team india office meeting",
        "indian professional woman man banking office",
        "corporate governance meeting india professionals",
    ],
    "rca_fmea": [
        "quality team professionals meeting analysis",
        "business people process improvement discussion",
        "professional team problem solving whiteboard",
        "indian professionals office teamwork analysis",
        "business analyst professional india office",
    ],
    "lean_excellence": [
        "professional team lean process improvement",
        "business people india office collaboration",
        "indian professionals process excellence meeting",
        "team leader coaching professionals india",
        "business excellence professionals india office",
    ],
    "pmo_genai": [
        "technology professionals india AI meeting",
        "digital transformation team india office",
        "professional indian business AI technology",
        "data analytics professionals india teamwork",
        "indian tech professionals office collaboration",
    ],
    "personal_excellence": [
        "indian business leader professional confident",
        "executive professional india office portrait",
        "successful indian professional business leader",
        "confident professional india corporate",
        "indian businessman woman leadership",
    ],
    "industry_trends": [
        "indian banking professionals discussion meeting",
        "financial professionals india conference",
        "business people india finance discussion",
        "indian professionals corporate boardroom",
        "finance team india office professionals",
    ],
    "any": [
        "indian business professionals office meeting",
        "professional team india corporate office",
        "confident indian professionals collaboration",
        "business leader india office professional",
        "indian corporate professionals teamwork",
    ],
}

# ── Keyword → human-centric image query ───────────────────
KEYWORD_MAP = {
    "rbi":             "indian banking professional regulation meeting",
    "nbfc":            "indian finance professionals office meeting",
    "compliance":      "compliance professional india office team",
    "fmea":            "quality professionals analysis meeting team",
    "rca":             "professionals root cause analysis whiteboard",
    "lean":            "lean professionals process improvement team",
    "six sigma":       "six sigma professionals quality meeting india",
    "dmaic":           "process improvement professionals team meeting",
    "kaizen":          "team continuous improvement professionals meeting",
    "pmo":             "project management professionals india meeting",
    "genai":           "technology professionals AI india office",
    "ai":              "tech professionals artificial intelligence india",
    "digital":         "digital transformation professionals india office",
    "complaint":       "customer service professionals india office",
    "audit":           "audit professionals india office meeting",
    "regulation":      "regulatory professionals india office discussion",
    "credit":          "banking professionals india credit discussion",
    "loan":            "banking professionals india loan office",
    "fintech":         "fintech professionals india technology office",
    "operational":     "operations professionals india office team",
    "governance":      "corporate governance professionals india meeting",
    "transformation":  "business transformation professionals india",
    "risk":            "risk management professionals india office",
    "process":         "process improvement professionals india team",
    "banking":         "banking professionals india office meeting",
    "leadership":      "business leader india professional confident",
    "management":      "management professionals india office meeting",
    "strategy":        "business strategy professionals india boardroom",
    "innovation":      "innovation professionals india office discussion",
    "data":            "data analytics professionals india office",
    "automation":      "automation technology professionals india",
    "5s":              "workplace organisation professionals india office",
    "kpi":             "business professionals india performance review",
    "npa":             "banking risk professionals india office meeting",
    "kyc":             "banking professionals india verification office",
}


def extract_smart_query(post_text: str, topic: str, pillar: str) -> str:
    """
    Build human-centric image search query from post content.
    Always ensures people appear in results.
    """
    combined = f"{topic} {post_text[:400]}".lower()

    # Find best keyword match
    matched = []
    for keyword, image_query in KEYWORD_MAP.items():
        if keyword in combined:
            matched.append((len(keyword), image_query))

    if matched:
        # Use longest (most specific) match
        matched.sort(reverse=True)
        best_query = matched[0][1]
        print(f"[Pexels] Smart query: '{best_query}'")
        return best_query

    # Build from topic words + add human element
    if topic:
        stop_words = {
            "the","a","an","in","on","at","to","for","of","and",
            "or","is","are","was","were","with","by","from","about"
        }
        words = [
            w for w in re.sub(r'[^a-z\s]','', topic.lower()).split()
            if w not in stop_words and len(w) > 3
        ]
        if words:
            query = " ".join(words[:3]) + " professionals india office"
            print(f"[Pexels] Topic query: '{query}'")
            return query

    # Pillar fallback
    fallback = PILLAR_SEARCH.get(pillar, PILLAR_SEARCH["any"])[0]
    print(f"[Pexels] Pillar fallback: '{fallback}'")
    return fallback


def search_pexels(query: str, per_page: int = 8) -> list:
    """Search Pexels with given query."""
    if not PEXELS_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query":       query,
                "per_page":    per_page,
                "orientation": "landscape",
                "size":        "large",       # ← high quality
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("photos", [])
    except Exception as e:
        print(f"[Pexels] Search error: {e}")
        return []


def score_photo(photo: dict) -> float:
    """
    Score a photo for quality and relevance.
    Higher = better. Favours:
    - Landscape orientation
    - High resolution
    - Professional look (inferred from alt text)
    """
    width  = photo.get("width", 0)
    height = photo.get("height", 1)
    ratio  = width / height

    score = 0.0

    # Prefer landscape ratio 1.5–2.0 (fits LinkedIn well)
    if 1.4 <= ratio <= 2.1:
        score += 3.0
    elif 1.2 <= ratio <= 2.4:
        score += 1.5

    # Prefer high resolution
    if width >= 2000:
        score += 2.0
    elif width >= 1200:
        score += 1.0

    # Prefer photos with descriptive alt text (usually better quality)
    alt = photo.get("alt","").lower()
    if any(w in alt for w in ["professional","business","office","meeting","team","india"]):
        score += 2.0
    if any(w in alt for w in ["person","people","man","woman","group","team"]):
        score += 3.0  # ← strong preference for human presence

    return score


def get_image_for_post(
    pillar:    str = "any",
    topic:     str = "",
    post_text: str = "",
) -> dict | None:
    """
    Main function — get best human-centric image for a LinkedIn post.
    Tries multiple queries with fallback chain.
    Returns image dict or None.
    """
    if not PEXELS_API_KEY:
        print("[Pexels] No API key configured.")
        return None

    # Build primary query
    primary_query = extract_smart_query(post_text, topic, pillar)

    # Build fallback queries
    fallback_queries = PILLAR_SEARCH.get(pillar, PILLAR_SEARCH["any"])

    # Try primary query first
    all_photos = search_pexels(primary_query, per_page=8)

    # If < 3 results, try fallback queries
    if len(all_photos) < 3:
        print(f"[Pexels] Only {len(all_photos)} results — trying fallbacks...")
        for fq in fallback_queries[:3]:
            more = search_pexels(fq, per_page=5)
            all_photos.extend(more)
            if len(all_photos) >= 5:
                break

    # Absolute fallback — generic Indian professionals
    if not all_photos:
        print("[Pexels] No results — using generic professional query")
        all_photos = search_pexels("indian business professionals office", per_page=5)

    if not all_photos:
        print("[Pexels] ❌ No images found at all.")
        return None

    # Score and rank photos
    scored = [(score_photo(p), p) for p in all_photos]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Pick best photo
    best_score, best_photo = scored[0]
    print(f"[Pexels] ✅ Best photo score: {best_score:.1f} | Alt: {best_photo.get('alt','')[:50]}")
    print(f"[Pexels] Photographer: {best_photo.get('photographer','?')} | {best_photo.get('url','')}")

    return {
        "url":          best_photo["src"]["large2x"],   # highest quality
        "medium_url":   best_photo["src"]["large"],
        "photographer": best_photo.get("photographer","Pexels"),
        "pexels_url":   best_photo.get("url",""),
        "photo_id":     best_photo.get("id"),
        "alt":          best_photo.get("alt",""),
    }


def download_image(image_url: str) -> bytes | None:
    """Download image bytes for LinkedIn upload."""
    try:
        resp = requests.get(image_url, timeout=20)
        resp.raise_for_status()
        size_kb = len(resp.content) // 1024
        print(f"[Pexels] Downloaded {size_kb} KB")
        return resp.content
    except Exception as e:
        print(f"[Pexels] Download error: {e}")
        return None


if __name__ == "__main__":
    tests = [
        ("regulatory",     "RBI rejects NBFC funding norms tightening", ""),
        ("rca_fmea",       "FMEA root cause analysis complaint reduction", ""),
        ("lean_excellence","DMAIC Lean Six Sigma process improvement banking", ""),
        ("pmo_genai",      "GenAI AI project management 2025", ""),
        ("personal_excellence","leadership career growth india professional",""),
    ]
    for pillar, topic, text in tests:
        print(f"\n── {pillar.upper()} ──")
        img = get_image_for_post(pillar=pillar, topic=topic, post_text=text)
        if img:
            print(f"  Alt: {img.get('alt','')[:60]}")
            print(f"  By: {img['photographer']}")
            print(f"  URL: {img['pexels_url']}")
