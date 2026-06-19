"""
post_generator.py - Token-optimised, objective news commentary (no resume/credentials injected)
40% fewer tokens, same quality output.
UPDATED: enforced layman English — short words, short sentences, no jargon.
UPDATED: removed personal resume/achievement stats from prompts — posts are now
         objective news commentary, not personal-brag framed.
"""

import anthropic
import json
import random
from datetime import datetime
import config
import store

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# ── Compressed format instructions ────────────────────────
FORMAT_PROMPTS = {
    "news_insight": "Hook (data/fact) → 3-4 bullets with ▶ → 2 lines plain-English implication → engagement question → 3-4 hashtags",
    "did_you_know": "Start 'Did you know? 💡' → surprising fact → 3 bullets ▶ → why it matters → 'Save this 🔖' → question → hashtags",
    "dmaic_case":   "Hook (quantified problem) → D/M/A/I/C one line each → outcome numbers → lesson → question → hashtags",
    "poll":         "POLL_QUESTION: [question]\nOPTION_1: [opt]\nOPTION_2: [opt]\nOPTION_3: [opt]\nOPTION_4: [opt]\nCONTEXT: [1-2 lines]\nHASHTAGS: [tags]",
    "personal_story":"Hook (surprising result) → problem → approach → outcome (numbers) → lesson → question → hashtags",
    "rca_tip":      "Hook (common failure) → 'Most fix symptoms. Best find roots.' → 5 steps ▶ → real outcome → 'Which step does your team skip?' → hashtags",
    "hbr_summary":  "Start with HBR article insight → 3 key takeaways ▶ → what it means for the BFSI/PM/AI reader → plain-English angle → question → hashtags",
}

# ── Core system prompt (compressed) ───────────────────────
# UPDATED: no resume/credentials, no "practitioner" framing, no personal achievement
# numbers. Posts are objective commentary on the article itself.
BASE_SYSTEM = """You are a LinkedIn content strategist with 25 years digital/SEO experience.
Writing objective, informative LinkedIn posts about RBI/BFSI regulation, project
management (PMI/PMP), Lean Six Sigma, RCA/FMEA, and world AI developments.

STRICT RULES:
1. Max 200 words. EXTREMELY SIMPLE ENGLISH — write like you're explaining to a smart
   12-year-old. Use short sentences (under 15 words each). One idea per sentence.
2. WORD CHOICE — always pick the simple word over the fancy word:
   - Use "use" not "utilise" or "leverage"
   - Use "show" not "demonstrate" or "exhibit"
   - Use "help" not "facilitate" or "enable"
   - Use "start" not "initiate" or "commence"
   - Use "change" not "transform" (unless naming "Digital Transformation" as a proper term)
   - Use "build" not "establish" or "institute"
   - Use "check" not "ascertain" or "validate"
   - Use "plan" not "strategise" or "formulate"
   - Use "rule" or "system" not "framework" or "paradigm" (unless it's an official term like "PPG Framework")
   - Use "many" or "most" not "a significant proportion of"
   - Use "because" not "given that" or "owing to the fact that"
3. BANNED WORDS (never use these): "leverage", "synergy", "holistic", "robust", "paradigm",
   "facilitate", "utilize/utilise", "ecosystem" (unless quoting an official term), "seamless",
   "cutting-edge", "best-in-class", "granular", "bandwidth", "circle back", "low-hanging fruit",
   "moving forward", "at the end of the day", "delve into", "navigate" (as in "navigate change"),
   "underscore", "underpin", "augment", "optimise/optimize" (use "improve" or "make better"),
   "streamline" (use "simplify" or "make faster"), "myriad", "plethora", "nuanced", "multifaceted".
4. Diplomatic — never criticise RBI, banks, government, or institutions negatively.
5. No opinion/political bias. Facts + plain implications only.
6. For AI pros/cons content — give a balanced view: real benefits AND real risks/limits,
   explained simply, no hype words on either side.
7. NEVER mention personal achievements, career history, job titles, certifications,
   team sizes, percentage improvements from past projects, or any first-person
   "I did X" claims. This is OBJECTIVE NEWS COMMENTARY, not a personal brag post.
   Do not say "in my experience" or "I've seen" or "we achieved".
8. Never start with "I". Start with hook (data, question, or fact from the article).
9. End with ONE specific engagement question, written simply, addressed to the reader
   in general (e.g. "What does your organisation do about this?"), not from a personal
   experience angle.
10. 3-5 hashtags at end. Never more.
11. Banned phrases: "In today's world", "As we navigate", "Exciting times", "Game changer",
    "In the ever-evolving landscape", "It goes without saying".
12. Write like an informed industry commentator explaining the news, not a personal
    success story.
13. Weave 1-2 SEO keywords naturally: Fair Practice Code, NBFC compliance, RBI regulation,
    PPG framework, RCA, FMEA, Lean Six Sigma, DMAIC, operational excellence, GenAI, PMI, PMP.
    Keep these as proper nouns/official terms — simplify everything ELSE around them.
14. Before finishing, re-read your draft and replace any word a 12-year-old wouldn't know
    with a simpler one, unless it's an official term (RBI, NBFC, KYC, DMAIC, FMEA, etc.)
15. Output ONLY the post text. No preamble."""


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
    """Generate LinkedIn post — objective commentary, no resume injection."""
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

    user_prompt = (
        f"Date: {datetime.now().strftime('%d %B %Y')}\n"
        f"Format: {FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS['news_insight'])}\n"
        f"Hashtags to include: {' '.join(hashtags)}\n"
        f"Recent topics (avoid repeating): {', '.join(recent_topics[:5])}\n\n"
        f"News/Article:\n{news_summary}\n\n"
        f"Write objective commentary on this article. No personal achievements or "
        f"first-person experience claims. Simplest possible English, short sentences. "
        f"Write the post:"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
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
    """Regenerate with feedback — objective commentary, no resume injection."""
    hashtags     = select_hashtags(pillar)
    news_summary = "\n".join([f"- {n['title']}" for n in news_items[:3]])

    feedback_note = f"\nUser feedback: '{feedback}'. Incorporate carefully." if feedback else ""

    user_prompt = (
        f"Format: {FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS['news_insight'])}\n"
        f"Hashtags: {' '.join(hashtags)}\n"
        f"News:\n{news_summary}"
        f"{feedback_note}\n\n"
        f"Write objective commentary on this article. No personal achievements or "
        f"first-person experience claims. Simplest possible English, short sentences. "
        f"Write the post:"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
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
