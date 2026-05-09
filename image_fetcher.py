"""
image_fetcher.py
Fetches relevant images from Pexels API based on post topic.
Free forever — no cost.
"""

import requests
import config

PEXELS_API_KEY = config.PEXELS_API_KEY

# Topic to search query mapping
PILLAR_SEARCH = {
    "regulatory":     "banking regulation india professional",
    "rca_fmea":       "quality management process analysis",
    "lean_excellence":"business excellence process improvement",
    "pmo_genai":      "artificial intelligence technology business",
    "any":            "indian banking finance professional",
}


def get_image_for_post(pillar: str = "any", topic: str = "") -> dict | None:
    """
    Search Pexels for a relevant image.
    Returns {url, photographer, pexels_url} or None.
    """
    if not PEXELS_API_KEY:
        print("[Pexels] No API key set.")
        return None

    # Build search query from topic or pillar
    if topic:
        # Extract key words from topic for better search
        query = topic[:50]
    else:
        query = PILLAR_SEARCH.get(pillar, "indian banking finance")

    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query":       query,
                "per_page":    5,
                "orientation": "landscape",
                "size":        "medium",
            },
            timeout=10,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])

        if not photos:
            # Try broader search if specific fails
            resp2 = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": "indian banking finance professional", "per_page": 3},
                timeout=10,
            )
            photos = resp2.json().get("photos", [])

        if photos:
            photo = photos[0]
            print(f"[Pexels] Found image: {photo.get('url')}")
            return {
                "url":          photo["src"]["large"],
                "medium_url":   photo["src"]["medium"],
                "photographer": photo.get("photographer", "Pexels"),
                "pexels_url":   photo.get("url", ""),
                "photo_id":     photo.get("id"),
            }

    except Exception as e:
        print(f"[Pexels] Error: {e}")

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
    img = get_image_for_post(pillar="regulatory", topic="RBI NBFC regulation")
    if img:
        print(f"Image URL: {img['url']}")
        print(f"Photographer: {img['photographer']}")
    else:
        print("No image found")
