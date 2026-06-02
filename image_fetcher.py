"""
image_fetcher.py - Fresh, article-relevant images using post-specific keywords.
Each post gets a unique image based on its actual content — no repetition.
"""

import requests
import re
import hashlib
import config

PEXELS_API_KEY = config.PEXELS_API_KEY

# ── Pillar base context (human-centric fallback only) ─────
PILLAR_FALLBACK = {
    "regulatory":          "indian banking compliance professionals office",
    "rca_fmea":            "quality team analysis professionals meeting",
    "lean_excellence":     "process improvement team professionals india",
    "pmo_genai":           "technology professionals AI india office",
    "personal_excellence": "indian business leader professional confident",
    "industry_trends":     "indian banking professionals conference meeting",
    "any":                 "indian business professionals office meeting",
}

# ── Topic keyword extractor ───────────────────────────────
STOP_WORDS = {
    "the","a","an","in","on","at","to","for","of","and","or","is","are",
    "was","were","with","by","from","about","this","that","they","their",
    "have","has","had","not","but","also","been","its","will","would",
    "could","should","more","most","after","before","during","than",
    "how","what","when","where","who","which","can","may","might",
    "one","two","three","four","five","six","seven","eight","nine","ten",
    "india","indian","professional","professionals","office","meeting",
    "team","business","corporate","people","person","man","woman",
}

# ── High-value BFSI → visual concept mapping ─────────────
# Maps specific financial/compliance terms to visual concepts Pexels understands
CONCEPT_MAP = {
    "rbi":                  "central bank india regulation",
    "nbfc":                 "financial institution india lending",
    "fair practice code":   "customer protection banking compliance",
    "fpc":                  "compliance banking customer",
    "fmea":                 "risk analysis failure prevention team",
    "rca":                  "root cause analysis whiteboard team",
    "dmaic":                "process improvement data analysis",
    "lean six sigma":       "lean process efficiency team",
    "six sigma":            "quality control process improvement",
    "kaizen":               "continuous improvement team collaboration",
    "5s":                   "workplace organisation efficiency",
    "pmo":                  "project management office team",
    "genai":                "artificial intelligence technology future",
    "kyc":                  "identity verification banking digital",
    "npa":                  "banking risk management finance",
    "unclaimed":            "forgotten money finance banking dormant",
    "deposit":              "bank savings deposit finance",
    "crypto":               "cryptocurrency digital finance blockchain",
    "quantum":              "quantum technology future finance",
    "forensic audit":       "financial investigation audit professional",
    "currency":             "currency exchange finance market",
    "rupee":                "indian rupee currency finance",
    "grievance":            "customer complaint resolution service",
    "complaint":            "customer service resolution professional",
    "audit":                "financial audit review professional",
    "digital transformation": "digital technology transformation future",
    "agile":                "agile team collaboration sprints",
    "board":                "corporate boardroom governance meeting",
    "governance":           "corporate governance board meeting",
    "fintech":              "financial technology startup innovation",
    "credit":               "credit lending finance approval",
    "loan":                 "loan approval banking finance",
    "interest rate":        "interest rate finance market",
    "penalty":              "regulation penalty fine compliance",
    "merger":               "business merger acquisition corporate",
    "acquisition":          "corporate acquisition business deal",
    "startup":              "startup innovation entrepreneur team",
    "leadership":           "business leadership executive professional",
    "strategy":             "business strategy planning boardroom",
    "data analytics":       "data analytics dashboard professional",
    "machine learning":     "machine learning AI data science",
    "automation":           "automation technology robot future",
    "operational excellence": "operational excellence team efficiency",
    "risk management":      "risk management finance professional",
    "customer experience":  "customer experience service satisfaction",
}


def extract_article_keywords(post_text: str, topic: str) -> list:
    """
    Extract the most meaningful keywords from the actual article content.
    Returns ranked list of specific terms found.
    """
    combined = f"{topic} {post_text[:600]}".lower()
    found = []

    # Check concept map first (most specific matches)
    for term, concept in CONCEPT_MAP.items():
        if term in combined:
            found.append((len(term), concept))

    # Sort by term length (longer = more specific)
    found.sort(reverse=True)
    return [concept for _, concept in found[:3]]


def build_unique_query(post_text: str, topic: str, pillar: str) -> str:
    """
    Build a unique, article-specific image search query.
    Uses actual article keywords so every post gets a different image.
    """
    concepts = extract_article_keywords(post_text, topic)

    if concepts:
        # Use top 2 concepts combined for specificity
        primary = concepts[0]
        print(f"[Pexels] Article-specific query: '{primary}'")
        return primary

    # Extract meaningful words from topic itself
    if topic:
        words = [
            w for w in re.sub(r'[^a-z\s]', '', topic.lower()).split()
            if w not in STOP_WORDS and len(w) > 4
        ]
        if words:
            query = " ".join(words[:3]) + " professional india"
            print(f"[Pexels] Topic-based query: '{query}'")
            return query

    # Pillar fallback
    fallback = PILLAR_FALLBACK.get(pillar, PILLAR_FALLBACK["any"])
    print(f"[Pexels] Pillar fallback: '{fallback}'")
    return fallback


def get_rotation_offset(post_text: str, topic: str) -> int:
    """
    Generate a deterministic offset from post content hash.
    Same post always gets same image, different posts get different ones.
    Prevents showing the same #1 Pexels result every time.
    """
    seed = f"{topic}{post_text[:100]}"
    hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return hash_val % 8   # offset between 0-7


def search_pexels(query: str, per_page: int = 15) -> list:
    """Search Pexels with given query, return photos list."""
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
                "size":        "large",
            },
            timeout=10,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        print(f"[Pexels] '{query}' → {len(photos)} results")
        return photos
    except Exception as e:
        print(f"[Pexels] Search error: {e}")
        return []


def score_photo(photo: dict) -> float:
    """Score photo for quality. Favours landscape, high-res, human presence."""
    width  = photo.get("width", 0)
    height = photo.get("height", 1)
    ratio  = width / height
    score  = 0.0

    # Landscape ratio 1.5–2.0 fits LinkedIn well
    if 1.4 <= ratio <= 2.1:
        score += 3.0
    elif 1.2 <= ratio <= 2.4:
        score += 1.5

    # High resolution
    if width >= 2000:
        score += 2.0
    elif width >= 1200:
        score += 1.0

    # Human presence in alt text
    alt = photo.get("alt", "").lower()
    if any(w in alt for w in ["person","people","man","woman","group","team","professional"]):
        score += 3.0
    if any(w in alt for w in ["professional","business","office","meeting","india"]):
        score += 2.0

    return score


def get_image_for_post(
    pillar:    str = "any",
    topic:     str = "",
    post_text: str = "",
) -> dict | None:
    """
    Main function — fetch a fresh, article-relevant image for each LinkedIn post.

    Strategy:
    1. Build article-specific query from actual post keywords
    2. Fetch 15 results (larger pool = more variety)
    3. Use content hash to rotate which result is picked
    4. Falls back through 3 query levels before giving up
    """
    if not PEXELS_API_KEY:
        print("[Pexels] No API key configured.")
        return None

    # Step 1: Article-specific primary query
    primary_query = build_unique_query(post_text, topic, pillar)

    # Step 2: Fetch larger pool for variety
    photos = search_pexels(primary_query, per_page=15)

    # Step 3: If weak results, try secondary concept query
    if len(photos) < 5:
        concepts = extract_article_keywords(post_text, topic)
        if len(concepts) > 1:
            secondary_query = concepts[1]
            print(f"[Pexels] Trying secondary query: '{secondary_query}'")
            more = search_pexels(secondary_query, per_page=10)
            photos.extend(more)

    # Step 4: Pillar fallback
    if len(photos) < 3:
        fallback_query = PILLAR_FALLBACK.get(pillar, PILLAR_FALLBACK["any"])
        print(f"[Pexels] Pillar fallback: '{fallback_query}'")
        more = search_pexels(fallback_query, per_page=10)
        photos.extend(more)

    # Step 5: Generic fallback
    if not photos:
        print("[Pexels] Using generic professional fallback")
        photos = search_pexels("indian business professionals office", per_page=10)

    if not photos:
        print("[Pexels] ❌ No images found.")
        return None

    # Remove duplicates by photo ID
    seen_ids = set()
    unique_photos = []
    for p in photos:
        if p["id"] not in seen_ids:
            seen_ids.add(p["id"])
            unique_photos.append(p)

    # Score all photos
    scored = sorted(
        [(score_photo(p), p) for p in unique_photos],
        key=lambda x: x[0],
        reverse=True
    )

    # Use content hash to pick from top results (not always #1)
    # This ensures different posts get different images
    top_pool = scored[:min(6, len(scored))]   # pick from top 6
    offset   = get_rotation_offset(post_text, topic) % len(top_pool)
    _, best_photo = top_pool[offset]

    print(f"[Pexels] ✅ Selected photo #{offset+1} of {len(top_pool)} top results")
    print(f"[Pexels] Alt: {best_photo.get('alt','')[:60]}")
    print(f"[Pexels] Photographer: {best_photo.get('photographer','?')}")

    return {
        "url":          best_photo["src"]["large2x"],
        "medium_url":   best_photo["src"]["large"],
        "photographer": best_photo.get("photographer", "Pexels"),
        "pexels_url":   best_photo.get("url", ""),
        "photo_id":     best_photo.get("id"),
        "alt":          best_photo.get("alt", ""),
        "query_used":   primary_query,
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
        ("regulatory",     "RBI rejects NBFC funding norms tightening", "equity investments group entities public funds"),
        ("rca_fmea",       "FMEA root cause analysis complaint reduction EMI", ""),
        ("lean_excellence","DMAIC Lean Six Sigma process TAT reduction banking", ""),
        ("pmo_genai",      "GenAI agentic AI startups incumbents BFSI", ""),
        ("regulatory",     "Unclaimed deposits insurance mutual funds government portal", ""),
        ("regulatory",     "RBI quantum safe cryptography banking Q-SAFE panel", ""),
    ]
    for pillar, topic, text in tests:
        print(f"\n── {pillar.upper()} | {topic[:50]} ──")
        img = get_image_for_post(pillar=pillar, topic=topic, post_text=text)
        if img:
            print(f"  Query used: {img.get('query_used','')}")
            print(f"  Alt: {img.get('alt','')[:60]}")
            print(f"  By: {img['photographer']}")
