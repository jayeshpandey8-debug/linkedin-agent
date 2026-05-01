"""
post_generator.py
Claude-powered LinkedIn post generator.
Uses Jayesh's full resume as permanent context.
Generates 6 different post formats across 5 pillars.
"""

import anthropic
import json
import random
from datetime import datetime
import config
import store

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────────────────────
# System Prompt — Jayesh's Brand Voice
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""
You are a senior LinkedIn content strategist and SEO specialist with 25 years of digital marketing experience.
You are writing on behalf of Jayesh Taradutt Pandey — a compliance and transformation leader in Indian BFSI.

YOUR MISSION:
Increase Jayesh's LinkedIn profile visits, followers, and authority by writing posts that:
1. Position him as a genuine expert — not a news aggregator
2. Speak directly to compliance officers, NBFC leaders, ops managers, and Six Sigma practitioners
3. Are grounded in his real experience and achievements
4. Use SEO-friendly language naturally woven into the post — never forced

JAYESH'S FULL PROFILE:
{config.AUTHOR_PROFILE}

STRICT CONTENT RULES:
1. Language: Simple, layman-friendly. Class 10 readability. No jargon without explanation.
2. Diplomatic: Never criticise RBI, banks, government bodies, or named institutions negatively.
3. No opinion or political bias — only facts and practitioner implications.
4. No buzzword fluff — "In today's world", "As we navigate", "Exciting times" are BANNED.
5. Every post must end with ONE specific engagement question to the audience.
6. Always write from the first-person practitioner lens — "In my experience...", "When we implemented this..."
7. Max 220 words for text posts. Polls are shorter.
8. Include 3-5 relevant hashtags at the end — never more than 5.
9. Never start with "I" — start with a hook (data, question, or surprising statement).
10. The post must make the reader feel: "This person really works in this space."

SEO KEYWORDS TO WEAVE NATURALLY (pick 2-3 per post):
Fair Practice Code, NBFC compliance, RBI regulation, PPG framework, root cause analysis,
FMEA, Lean Six Sigma, DMAIC, operational excellence, process reengineering, complaint governance,
KFS compliance, regulatory governance, audit readiness, change management, GenAI BFSI,
business excellence, Six Sigma Black Belt, PMO leadership, RCA governance

OUTPUT FORMAT:
Return ONLY the LinkedIn post text. No preamble, no title, no explanation.
Start directly with the hook line.
"""


# ─────────────────────────────────────────────────────────────
# Format-specific prompt templates
# ─────────────────────────────────────────────────────────────

FORMAT_PROMPTS = {

    "news_insight": """
Write a "News + Practitioner Insight" LinkedIn post.
Structure:
- Line 1: Hook (surprising data point or statement about the news)
- 3-4 bullet points using ▶ : key facts from the news in plain English
- 2 lines: What this means for compliance/operations practitioners specifically
- 1 engagement question
- 3-4 hashtags
""",

    "did_you_know": """
Write a "Did You Know?" LinkedIn post about a regulatory fact or process excellence insight.
Structure:
- Start with: "Did you know? 💡" followed by a surprising fact
- 3 bullet points using ▶ : what most people miss about this topic
- 1-2 lines: Why this matters for BFSI professionals
- End with: "Save this if you work in BFSI. 🔖"
- 1 engagement question
- 3-4 hashtags
""",

    "dmaic_case": """
Write a "Lean/DMAIC Case Study" LinkedIn post based on a real process challenge in BFSI.
Draw on Jayesh's actual experience (EMI complaints reduced from 300+ to under 10, TAT reduction, etc.)
Structure:
- Hook line: The quantified problem
- D — Define: What was broken
- M — Measure: The baseline numbers
- A — Analyse: What data revealed
- I — Improve: Specific change made
- C — Control: How improvement was sustained
- Outcome: Quantified result
- 1 lesson learned
- 1 engagement question
- 3-4 hashtags
""",

    "poll": """
Write a LinkedIn Poll post. Keep it SHORT.
Structure:
- 1 thought-provoking question relevant to BFSI compliance or operations (this is the poll question)
- 4 poll options (each max 5 words):
  Option 1: ...
  Option 2: ...
  Option 3: ...
  Option 4: ...
- 1-2 lines of context explaining why you're asking
- 2-3 hashtags

Format the output EXACTLY like this so the app can parse it:
POLL_QUESTION: [the question]
OPTION_1: [option]
OPTION_2: [option]
OPTION_3: [option]
OPTION_4: [option]
CONTEXT: [1-2 lines]
HASHTAGS: [#tag1 #tag2 #tag3]
""",

    "personal_story": """
Write a "Personal Win / Story" LinkedIn post based on Jayesh's real achievements.
Choose one specific achievement (RCA unit, complaint reduction, Zero Hold, FPC transformation, etc.)
Structure:
- Hook: The surprising quantified result (e.g. "We cut 300 complaints to under 10.")
- What the problem was
- What approach we took (name the tool: DMAIC, RCA, FMEA, Lean, etc.)
- The specific outcome with numbers
- The lesson that stayed with me (1-2 lines — genuine, not generic)
- Offer: "If you're dealing with [same challenge], happy to share the framework."
- 1 engagement question
- 3-4 hashtags
""",

    "rca_tip": """
Write an "RCA / FMEA Practitioner Tip" LinkedIn post.
Structure:
- Hook: A common failure mode in BFSI operations stated as a fact
- "Most teams fix symptoms. The best teams find the root."
- Step-by-step RCA approach (5 steps using ▶):
  Step 1: Define the defect precisely
  Step 2: Apply 5 Whys
  Step 3: Fishbone analysis
  Step 4: FMEA scoring
  Step 5: Corrective action with control plan
- Quantified real outcome from Jayesh's experience
- Question: "Which step does your team usually skip?"
- 3-4 hashtags
""",
}


# ─────────────────────────────────────────────────────────────
# Hashtag selector (no-repeat logic)
# ─────────────────────────────────────────────────────────────

def select_hashtags(pillar: str, count: int = 4) -> list[str]:
    recent_tags = store.get_recent_hashtags(limit=7)
    pillar_tags = config.HASHTAG_BANK.get(pillar, [])
    always_tags = config.HASHTAG_BANK.get("always", [])

    # Filter out recently used
    fresh_pillar = [t for t in pillar_tags if t not in recent_tags]
    if not fresh_pillar:
        fresh_pillar = pillar_tags  # reset if all used

    # Pick 2-3 pillar + 1-2 always
    chosen = random.sample(fresh_pillar, min(3, len(fresh_pillar)))
    chosen += random.sample(always_tags, min(2, len(always_tags)))

    return list(dict.fromkeys(chosen))[:count]   # deduplicate, limit


# ─────────────────────────────────────────────────────────────
# Main generator
# ─────────────────────────────────────────────────────────────

def generate_post(
    news_items: list[dict],
    pillar:     str,
    fmt:        str,
    recent_topics: list[str] = None,
) -> dict:
    """
    Generate a LinkedIn post using Claude.
    Returns full post dict ready to save to DB.
    """
    recent_topics = recent_topics or []
    hashtags      = select_hashtags(pillar)

    news_summary = "\n\n".join([
        f"[{i+1}] Source: {n['source']}\n"
        f"    Headline: {n['title']}\n"
        f"    Detail: {n.get('description', '')}"
        for i, n in enumerate(news_items[:4])
    ])

    format_instruction = FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS["news_insight"])

    user_prompt = f"""
Today's date: {datetime.now().strftime("%A, %d %B %Y")}
Content pillar: {pillar.upper()} — {config.PILLARS.get(pillar, "")}
Post format: {fmt.upper()}

Recent topics already covered (DO NOT repeat these):
{chr(10).join(f"- {t}" for t in recent_topics[:10])}

Today's fresh news/context:
{news_summary}

Suggested hashtags to include: {" ".join(hashtags)}

{format_instruction}

Write the post now:
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    post_text = response.content[0].text.strip()

    # Extract topic keyword for memory
    topic_words = news_items[0]["title"].split()[:5] if news_items else [pillar]
    topic       = " ".join(topic_words)

    return {
        "post_text":    post_text,
        "pillar":       pillar,
        "format":       fmt,
        "topic":        topic,
        "keywords_used": [pillar, fmt],
        "hashtags_used": hashtags,
        "sources":      [n["source"] for n in news_items[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
    }


def regenerate_post(
    post_id:    int,
    news_items: list[dict],
    pillar:     str,
    fmt:        str,
    feedback:   str = "",
) -> dict:
    """Regenerate with user feedback."""
    feedback_str = f"\n\nUser feedback on previous draft: '{feedback}'\nIncorporate this feedback carefully." if feedback else ""

    modified_system = SYSTEM_PROMPT + feedback_str
    hashtags = select_hashtags(pillar)

    news_summary = "\n".join([f"- {n['title']}" for n in news_items[:3]])
    format_instruction = FORMAT_PROMPTS.get(fmt, FORMAT_PROMPTS["news_insight"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=modified_system,
        messages=[{
            "role": "user",
            "content": f"Date: {datetime.now().strftime('%A, %d %B %Y')}\n"
                       f"Pillar: {pillar}\nFormat: {fmt}\n"
                       f"News context:\n{news_summary}\n"
                       f"Hashtags: {' '.join(hashtags)}\n\n"
                       f"{format_instruction}\nWrite the post now:"
        }],
    )

    post_text = response.content[0].text.strip()
    topic     = news_items[0]["title"][:50] if news_items else pillar

    return {
        "post_text":    post_text,
        "pillar":       pillar,
        "format":       fmt,
        "topic":        topic,
        "hashtags_used": hashtags,
        "sources":      [n["source"] for n in news_items[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
        "feedback":     feedback,
    }


if __name__ == "__main__":
    store.init_db()
    mock_news = [{
        "title":       "RBI issues updated Fair Practice Code directions for NBFCs",
        "description": "RBI has revised FPC norms requiring NBFCs to display all charges upfront in the Key Fact Statement.",
        "source":      "RBI",
        "url":         "https://www.rbi.org.in",
        "pillar":      "regulatory",
    }]
    result = generate_post(mock_news, pillar="regulatory", fmt="news_insight")
    print("\n── Generated Post ────────────────────────────────────")
    print(result["post_text"])
