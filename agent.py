"""
agent.py - Updated with topic on demand feature
"""
import time
import threading
from datetime import datetime
import pytz

import config
import store
import news_fetcher
import post_generator
import linkedin_api
import whatsapp

IST = pytz.timezone("Asia/Kolkata")

_pending_post_id = None
_pending_news    = []


def get_todays_rotation() -> tuple:
    today_dow = datetime.now(IST).weekday()
    rotation  = config.CONTENT_ROTATION.get(today_dow)
    if not rotation:
        return None, None
    pillar, fmt = rotation
    recent_pillars = store.get_recent_pillars(limit=2)
    if pillar != "any" and pillar in recent_pillars[:2]:
        all_pillars = list(config.PILLARS.keys())
        all_pillars.remove("any")
        for alt in all_pillars:
            if alt not in recent_pillars:
                pillar = alt
                break
    return pillar, fmt


def run_daily_cycle():
    global _pending_post_id, _pending_news
    now_ist = datetime.now(IST)
    print(f"\n[Agent] ═══ Daily Cycle — {now_ist.strftime('%A %d %b %Y %H:%M IST')} ═══")
    pillar, fmt = get_todays_rotation()
    if not pillar:
        print("[Agent] No post scheduled today.")
        return
    print(f"[Agent] Pillar: {pillar} | Format: {fmt}")
    recent_topics = store.get_recent_topics(limit=config.MEMORY_LOOKBACK_POSTS)
    news = news_fetcher.get_news_for_pillar(pillar, recent_topics=recent_topics)
    if not news:
        whatsapp.send_error_alert("Could not fetch news today.")
        return
    _pending_news = news
    print("[Agent] Generating post via Claude...")
    try:
        post = post_generator.generate_post(news_items=news, pillar=pillar, fmt=fmt, recent_topics=recent_topics)
    except Exception as e:
        whatsapp.send_error_alert(f"Claude generation failed: {e}")
        return
    post_id = store.save_draft(post)
    post["id"] = post_id
    _pending_post_id = post_id
    store.update_status(post_id, "whatsapp_sent", sent_to_whatsapp_at=datetime.now().isoformat())
    whatsapp.send_draft_for_approval(post_id, post)


def generate_on_topic(topic: str):
    """Generate post on a specific user-requested topic."""
    global _pending_post_id, _pending_news
    print(f"[Agent] Topic on demand: {topic}")

    # Confirm receipt immediately
    whatsapp.send_topic_confirmation(topic)

    # Search news for this specific topic
    try:
        import requests, os
        api_key = config.NEWS_API_KEY
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        topic,
                "language": "en",
                "pageSize": 4,
                "sortBy":   "relevancy",
                "apiKey":   api_key,
            },
            timeout=10,
        )
        articles = resp.json().get("articles", [])
        news = [
            {
                "title":       a.get("title",""),
                "description": a.get("description",""),
                "url":         a.get("url",""),
                "source":      a.get("source",{}).get("name","NewsAPI"),
                "pillar":      "any",
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title","")
        ][:4]
    except Exception as e:
        print(f"[Agent] News search error: {e}")
        news = []

    # Fallback if no news found
    if not news:
        news = [{
            "title":       topic,
            "description": f"Analysis and insights on: {topic}",
            "source":      "User Request",
            "url":         "",
            "pillar":      "any",
        }]

    _pending_news = news

    # Generate post with topic as context
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        news_summary = "\n".join([f"- {n['title']}: {n.get('description','')}" for n in news[:3]])

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=700,
            system=f"""You are a LinkedIn content strategist for Jayesh Taradutt Pandey.
{config.AUTHOR_PROFILE}
Rules: Layman language, diplomatic, no bias, practitioner lens, max 200 words, 
end with engagement question, 3-4 hashtags. Start directly with hook line.""",
            messages=[{
                "role": "user",
                "content": f"Write a LinkedIn post about: {topic}\n\nRelated news:\n{news_summary}\n\nDate: {datetime.now().strftime('%d %B %Y')}"
            }],
        )
        post_text = response.content[0].text.strip()
    except Exception as e:
        whatsapp.send_error_alert(f"Post generation failed: {e}")
        return

    post = {
        "post_text":    post_text,
        "pillar":       "any",
        "format":       "news_insight",
        "topic":        topic,
        "keywords_used": [topic],
        "hashtags_used": [],
        "sources":      [n["source"] for n in news[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
    }

    post_id = store.save_draft(post)
    post["id"] = post_id
    _pending_post_id = post_id
    store.update_status(post_id, "whatsapp_sent", sent_to_whatsapp_at=datetime.now().isoformat())
    whatsapp.send_draft_for_approval(post_id, post)


def handle_whatsapp_reply(reply_text: str) -> str:
    global _pending_post_id, _pending_news

    parsed   = whatsapp.parse_reply(reply_text)
    action   = parsed["action"]
    feedback = parsed.get("feedback", "")

    print(f"[Agent] Reply: action={action}, feedback='{feedback}'")

    # ── TOPIC ON DEMAND ────────────────────────────────────
    if action == "topic":
        if not feedback:
            return "Please tell me the topic. Example:\nTOPIC RBI FMEA circular\nTOPIC Lean Six Sigma in banking"
        # Run in background thread
        threading.Thread(target=generate_on_topic, args=(feedback,), daemon=True).start()
        return f"🔍 Got it! Searching and writing about:\n_{feedback}_\n\nCheck WhatsApp in 60 seconds! ⏳"

    # Get pending post
    if not _pending_post_id:
        pending = store.get_latest_pending()
        if pending:
            _pending_post_id = pending["id"]
        else:
            return (
                "No pending post found.\n\n"
                "You can:\n"
                "⚡ Use the control panel to generate\n"
                "📌 Send: *TOPIC [your topic]*\n"
                "Example: TOPIC RBI Fair Practice Code update"
            )

    post_id = _pending_post_id

    # ── APPROVE ────────────────────────────────────────────
    if action == "approve":
        post = store.get_post(post_id)
        if not post:
            return "Post not found."
        result = linkedin_api.post_to_linkedin(post["post_text"])
        if result["success"]:
            store.update_status(post_id, "posted", linkedin_post_id=result["post_id"])
            _pending_post_id = None
            def _reminder():
                time.sleep(config.ENGAGEMENT_REMINDER_MINUTES * 60)
                whatsapp.send_engagement_reminder(post_id)
            threading.Thread(target=_reminder, daemon=True).start()
            return (
                f"✅ *Posted to LinkedIn!*\n\n"
                f"Your post is now live! 🎉\n"
                f"I'll remind you in {config.ENGAGEMENT_REMINDER_MINUTES} min to engage."
            )
        else:
            store.update_status(post_id, "failed")
            return f"❌ LinkedIn posting failed:\n{result['error']}"

    # ── EDIT ───────────────────────────────────────────────
    elif action == "edit":
        if not feedback:
            return "Please tell me what to change.\nExample: EDIT make it shorter and add more about DMAIC"
        try:
            pillar = store.get_post(post_id).get("pillar","regulatory")
            fmt    = store.get_post(post_id).get("format","news_insight")
            new_post = post_generator.regenerate_post(post_id=post_id, news_items=_pending_news, pillar=pillar, fmt=fmt, feedback=feedback)
            store.update_post_text(post_id, new_post["post_text"])
            store.update_status(post_id, "whatsapp_sent", feedback=feedback)
            new_post["id"] = post_id
            whatsapp.send_draft_for_approval(post_id, new_post)
            return "🔄 Regenerated with your feedback! Check new draft above."
        except Exception as e:
            return f"❌ Regeneration failed: {e}"

    # ── REDO ───────────────────────────────────────────────
    elif action == "redo":
        try:
            pillar = store.get_post(post_id).get("pillar","regulatory")
            fmt    = store.get_post(post_id).get("format","news_insight")
            new_post = post_generator.regenerate_post(post_id=post_id, news_items=_pending_news, pillar=pillar, fmt=fmt, feedback=feedback)
            store.update_post_text(post_id, new_post["post_text"])
            store.update_status(post_id, "whatsapp_sent")
            new_post["id"] = post_id
            whatsapp.send_draft_for_approval(post_id, new_post)
            return "🔄 Completely regenerated! New draft sent."
        except Exception as e:
            return f"❌ Regeneration failed: {e}"

    # ── SKIP ───────────────────────────────────────────────
    elif action == "skip":
        store.update_status(post_id, "rejected")
        _pending_post_id = None
        return "⏭ Skipped. Next post at scheduled time.\n\n📌 You can also send:\nTOPIC [your topic]\nto write about anything anytime!"

    # ── UNKNOWN ────────────────────────────────────────────
    else:
        return (
            "I didn't understand that.\n\n"
            "Reply with:\n"
            "✅ *YES* — Post it\n"
            "✏️ *EDIT [feedback]*\n"
            "🔄 *REDO* — Regenerate\n"
            "❌ *NO* — Skip\n"
            "📌 *TOPIC [topic]* — Write about specific topic\n\n"
            "Example: TOPIC RBI FMEA circular update"
        )


def run_weekly_summary():
    print("[Agent] Sending weekly summary...")
    stats = store.get_week_stats()
    whatsapp.send_weekly_summary(stats)


if __name__ == "__main__":
    store.init_db()
    run_daily_cycle()
