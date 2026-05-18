"""
post_generator.py - Token-optimised with pillar-specific prompts
40% fewer tokens, same quality output.
"""

import anthropic
import json
import random
from datetime import datetime
import config
import store

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# ── Compressed pillar-specific credentials ─────────────────
# Only sends relevant parts of profile per pillar
# Saves ~300 tokens per request

PILLAR_CREDENTIALS = {
    "regulatory": """
Jayesh Pandey | Deputy National Lead – Fair Practice Code, Bajaj Finance | 15+ yrs NBFC
Key wins: India's first RCA governance unit in BFSI | Zero critical audit observations |
85% customer refund reduction | RBI supervision SPOC – RBI appreciation earned |
65 PPGs consolidated to 31 clusters | Expert: FPC, PPG, KFS, RBI inspection readiness
""",
    "rca_fmea": """
Jayesh Pandey | Complaint Root Cause Resolution Lead, Bajaj Finance | 15+ yrs NBFC
Key wins: EMI complaints 300+ → under 10/month via DMAIC | CRCR team 3 → 16 members |
96% recurring complaint reduction | Expert: RCA, FMEA, 5 Whys, Fishbone, Pareto |
India's first structured RCA governance unit in BFSI
""",
    "lean_excellence": """
Jayesh Pandey | Lean Six Sigma Black Belt | 15+ yrs BFSI operations
Key wins: 1,500+ employees trained in LSS | 20+ Green Belt projects mentored |
30% faster processes via Zero Hold | Kaizen/Blitz events across Bajaj Finance |
Expert: DMAIC, Kaizen, 5S, Value Stream Mapping, TAT reduction
""",
    "pmo_genai": """
Jayesh Pandey | PRINCE2 Practitioner | Strategic Advisor to EVP – Ops & Service |
15+ yrs program management | IIT Kanpur Leadership with AI (pursuing) |
Key wins: 90%+ enterprise initiatives on time | GenAI adoption program |
Paperless Sourcing – 100% digital KYC | Expert: PMO, change management, AI in BFSI
""",
    "personal_excellence": """
Jayesh Pandey | Deputy National Lead, Bajaj Finance | IIM Lucknow | IIT Kanpur AI |
PRINCE2 | Lean Six Sigma Black Belt | CMMI Auditor | 15+ yrs BFSI leadership |
Awards: 3x Hero Award, 2x Super Hero, 3x A+ rating, 2x ESOP grants
""",
    "industry_trends": """
Jayesh Pandey | Deputy National Lead – Fair Practice Code, Bajaj Finance | 15+ yrs NBFC
Expertise: RBI regulation, NBFC compliance, operational excellence, GenAI in BFSI |
Practitioner perspective on Indian banking sector trends and regulatory evolution
""",
    "any": """
Jayesh Pandey | Deputy National Lead – FPC, Bajaj Finance | 15+ yrs BFSI |
PRINCE2 | Lean Six Sigma Black Belt | IIM Lucknow | IIT Kanpur AI (pursuing) |
Expert: RBI compliance, RCA/FMEA, Lean Six Sigma, PMO, GenAI in BFSI
""",
}

# ── Compressed format instructions ────────────────────────
FORMAT_PROMPTS = {
    "news_insight": "Hook (data/fact) → 3-4 bullets with ▶ → 2 lines practitioner insight → engagement question → 3-4 hashtags",
    "did_you_know": "Start 'Did you know? 💡' → surprising fact → 3 bullets ▶ → why it matters → 'Save this 🔖' → question → hashtags",
    "dmaic_case":   "Hook (quantified problem) → D/M/A/I/C one line each → outcome numbers → lesson → question → hashtags",
    "poll":         "POLL_QUESTION: [question]\nOPTION_1: [opt]\nOPTION_2: [opt]\nOPTION_3: [opt]\nOPTION_4: [opt]\nCONTEXT: [1-2 lines]\nHASHTAGS: [tags]",
    "personal_story":"Hook (surprising result) → problem → approach (name the tool) → outcome (numbers) → lesson → offer to share → question → hashtags",
    "rca_tip":      "Hook (common failure) → 'Most fix symptoms. Best find roots.' → 5 steps ▶ → real outcome → 'Which step does your team skip?' → hashtags",
    "hbr_summary":  "Start with HBR article insight → 3 key takeaways ▶ → what it means for Indian BFSI/NBFC → practitioner angle → question → hashtags",
}

# ── Core system prompt (compressed) ───────────────────────
BASE_SYSTEM = """You are a LinkedIn content strategist with 25 years digital/SEO experience.
Writing for a senior BFSI compliance and transformation leader in India.

STRICT RULES:
1. Max 200 words. Layman language. Class 10 readability.
2. Diplomatic — never criticise RBI, banks, or institutions negatively.
3. No opinion/political bias. Facts + practitioner implications only.
4. Never start with "I". Start with hook (data, question, or fact).
5. End with ONE specific engagement question.
6. 3-5 hashtags at end. Never more.
7. Banned phrases: "In today's world", "As we navigate", "Exciting times", "Game changer"
8. Write as practitioner — someone who lives these challenges daily.
9. Weave 1-2 SEO keywords naturally: Fair Practice Code, NBFC compliance, RBI regulation,
   PPG framework, RCA, FMEA, Lean Six Sigma, DMAIC, operational excellence, GenAI BFSI.
10. Output ONLY the post text. No preamble."""


def select_hashtags(pillar: str, count: int = 4) -> list[str]:
    recent_tags  = store.get_recent_hashtags(limit=7)
    pillar_tags  = config.HASHTAG_BANK.get(pillar, [])
    always_tags  = config.HASHTAG_BANK.get("always", [])
    fresh_pillar = [t for t in pillar_tags if t not in recent_tags] or pillar_tags
    chosen = random.sample(fresh_pillar, min(3, len(fresh_pillar)))
    chosen += random.sample(always_tags, min(2, len(always_tags)))
    return list(dict.fromkeys(chosen))[:count]


def _add_source_url(post_text: str, news_items: list) -> str:
    """Add source URL at bottom of post."""
    for n in news_items:
        url = n.get("url","")
        if url and url.startswith("http"):
            return post_text + f"\n\n📌 Source: {url}"
    return post_text


def generate_post(
    news_items:     list[dict],
    pillar:         str,
    fmt:            str,
    recent_topics:  list = None,
) -> dict:
    """Generate LinkedIn post — token optimised."""
    recent_topics = recent_topics or []
    hashtags      = select_hashtags(pillar)

    # Check if this is an HBR article
    hbr_items  = [n for n in news_items if n.get("is_hbr")]
    is_hbr     = len(hbr_items) > 0
    if is_hbr:
        fmt = "hbr_summary"

    news_summary = "\n".join([
        f"- [{n['source']}] {n['title']}: {n.get('description','')[:150]}"
        for n in news_items[:3]
    ])

    # Pillar-specific credentials (saves ~300 tokens vs full profile)
    credentials = PILLAR_CREDENTIALS.get(pillar, PILLAR_CREDENTIALS["any"])

    user_prompt = (
        f"Author: {credentials.strip()}\n"
        f"Date: {datetime.now().strftime('%d %B %Y')}\n"
        f"Format: {FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS['news_insight'])}\n"
        f"Hashtags to include: {' '.join(hashtags)}\n"
        f"Recent topics (avoid repeating): {', '.join(recent_topics[:5])}\n\n"
        f"News/Article:\n{news_summary}\n\nWrite the post:"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=BASE_SYSTEM,
        messages=[{"role":"user","content":user_prompt}],
    )

    post_text = response.content[0].text.strip()
    post_text = _add_source_url(post_text, news_items)

    topic = news_items[0]["title"][:60] if news_items else pillar

    return {
        "post_text":    post_text,
        "pillar":       pillar,
        "format":       fmt,
        "topic":        topic,
        "keywords_used":[pillar, fmt],
        "hashtags_used":hashtags,
        "sources":      [n["source"] for n in news_items[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
        "is_hbr":       is_hbr,
        "hbr_image":    hbr_items[0].get("image_url","") if hbr_items else "",
    }


def regenerate_post(
    post_id:    int,
    news_items: list[dict],
    pillar:     str,
    fmt:        str,
    feedback:   str = "",
) -> dict:
    """Regenerate with feedback — token optimised."""
    hashtags    = select_hashtags(pillar)
    credentials = PILLAR_CREDENTIALS.get(pillar, PILLAR_CREDENTIALS["any"])
    news_summary = "\n".join([f"- {n['title']}" for n in news_items[:3]])

    feedback_note = f"\nUser feedback: '{feedback}'. Incorporate carefully." if feedback else ""

    user_prompt = (
        f"Author: {credentials.strip()}\n"
        f"Format: {FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS['news_insight'])}\n"
        f"Hashtags: {' '.join(hashtags)}\n"
        f"News:\n{news_summary}"
        f"{feedback_note}\n\nWrite the post:"
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=BASE_SYSTEM,
        messages=[{"role":"user","content":user_prompt}],
    )

    post_text = response.content[0].text.strip()
    post_text = _add_source_url(post_text, news_items)

    return {
        "post_text":    post_text,
        "pillar":       pillar,
        "format":       fmt,
        "topic":        news_items[0]["title"][:60] if news_items else pillar,
        "hashtags_used":hashtags,
        "sources":      [n["source"] for n in news_items[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
        "feedback":     feedback,
    }


if __name__ == "__main__":
    store.init_db()
    mock = [{"title":"RBI issues new NBFC liquidity norms","description":"RBI tightens LCR for upper-layer NBFCs","source":"RBI","url":"https://rbi.org.in","pillar":"regulatory","is_hbr":False}]
    r = generate_post(mock, pillar="regulatory", fmt="news_insight")
    print(r["post_text"])
