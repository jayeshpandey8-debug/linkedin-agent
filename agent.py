"""
agent.py - Optimised with parallel execution + DB-based post ID tracking
"""
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

import config
import store
import news_fetcher
import post_generator
import linkedin_api
import whatsapp

IST = pytz.timezone("Asia/Kolkata")

# In-memory cache (backed by DB for persistence)
_pending_news = []


def get_todays_rotation() -> tuple:
    today_dow = datetime.now(IST).weekday()
    rotation  = config.CONTENT_ROTATION.get(today_dow)
    if not rotation:
        return None, None
    pillar, fmt = rotation
    recent_pillars = store.get_recent_pillars(limit=2)
    if pillar != "any" and pillar in recent_pillars[:2]:
        all_pillars = [p for p in config.PILLARS.keys() if p != "any"]
        for alt in all_pillars:
            if alt not in recent_pillars:
                pillar = alt
                break
    return pillar, fmt


def run_daily_cycle():
    """Optimised daily cycle with parallel execution."""
    global _pending_news
    now_ist = datetime.now(IST)
    print(f"\n[Agent] ═══ Daily Cycle — {now_ist.strftime('%A %d %b %Y %H:%M IST')} ═══")

    pillar, fmt = get_todays_rotation()
    if not pillar:
        print("[Agent] No post scheduled today.")
        return

    print(f"[Agent] Pillar: {pillar} | Format: {fmt}")
    recent_topics = store.get_recent_topics(limit=config.MEMORY_LOOKBACK_POSTS)

    # Check if Thursday — include HBR for PMO/GenAI posts
    today_dow  = datetime.now(IST).weekday()
    include_hbr = (pillar == "pmo_genai") or (today_dow == 3)

    # Fetch news (parallel inside news_fetcher)
    news = news_fetcher.get_news_for_pillar(
        pillar,
        recent_topics=recent_topics,
        include_hbr=include_hbr
    )
    if not news:
        whatsapp.send_error_alert("Could not fetch news today.")
        return

    _pending_news = news

    # Generate post
    print("[Agent] Generating post via Claude...")
    try:
        post = post_generator.generate_post(
            news_items=news,
            pillar=pillar,
            fmt=fmt,
            recent_topics=recent_topics,
        )
    except Exception as e:
        whatsapp.send_error_alert(f"Claude generation failed: {e}")
        return

    # Save draft + set active post in DB
    post_id = store.save_draft(post)
    post["id"] = post_id
    store.set_active_post(post_id)   # ← DB-persisted, survives restarts
    store.update_status(
        post_id, "whatsapp_sent",
        sent_to_whatsapp_at=datetime.now().isoformat()
    )

    print(f"[Agent] Draft #{post_id} saved. Sending to WhatsApp...")
    whatsapp.send_draft_for_approval(post_id, post)


def generate_on_topic(topic: str):
    """Generate post on specific user-requested topic — with HBR check."""
    global _pending_news
    print(f"[Agent] Topic on demand: {topic}")
    whatsapp.send_topic_confirmation(topic)

    # Check if topic is HBR/AI/PM related
    hbr_keywords = ["harvard","hbr","ai","artificial intelligence","project management",
                     "leadership","digital transformation","agile","strategy","innovation"]
    is_hbr_topic = any(kw in topic.lower() for kw in hbr_keywords)

    news = []

    if is_hbr_topic:
        print("[Agent] HBR topic detected — fetching HBR articles...")
        news = news_fetcher.get_hbr_for_post()

    if not news:
        # Search NewsAPI for the topic
        try:
            import requests, os
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        topic,
                    "language": "en",
                    "pageSize": 4,
                    "sortBy":   "relevancy",
                    "apiKey":   config.NEWS_API_KEY,
                },
                timeout=8,
            )
            articles = resp.json().get("articles",[])
            news = [
                {
                    "title":       a.get("title",""),
                    "description": a.get("description",""),
                    "url":         a.get("url",""),
                    "source":      a.get("source",{}).get("name","NewsAPI"),
                    "pillar":      "any",
                    "image_url":   a.get("urlToImage",""),
                    "is_hbr":      False,
                }
                for a in articles
                if a.get("title") and "[Removed]" not in a.get("title","")
            ][:4]
        except Exception as e:
            print(f"[Agent] NewsAPI topic search error: {e}")

    if not news:
        news = [{
            "title":       topic,
            "description": f"Analysis and insights on: {topic}",
            "source":      "User Request",
            "url":         "",
            "pillar":      "any",
            "image_url":   "",
            "is_hbr":      False,
        }]

    _pending_news = news

    # Generate post
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        news_summary = "\n".join([
            f"- [{n['source']}] {n['title']}: {n.get('description','')[:150]}"
            for n in news[:3]
        ])

        hbr_note = ""
        if is_hbr_topic and any(n.get("is_hbr") for n in news):
            hbr_note = "\nThis is based on a Harvard Business Review article. Reference HBR in your post and link it to Indian BFSI context."

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=post_generator.BASE_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Author: {post_generator.PILLAR_CREDENTIALS['any'].strip()}\n"
                    f"Topic requested: {topic}\n"
                    f"Format: Hook → 3-4 bullets ▶ → practitioner insight → question → 3-4 hashtags\n"
                    f"News/Articles:\n{news_summary}"
                    f"{hbr_note}\n\nWrite the post:"
                )
            }],
        )
        post_text = response.content[0].text.strip()

        # Add source URL
        for n in news:
            if n.get("url","").startswith("http"):
                post_text += f"\n\n📌 Source: {n['url']}"
                break

    except Exception as e:
        whatsapp.send_error_alert(f"Post generation failed: {e}")
        return

    # Determine HBR image
    hbr_image = ""
    for n in news:
        if n.get("is_hbr") and n.get("image_url"):
            hbr_image = n["image_url"]
            break

    post = {
        "post_text":    post_text,
        "pillar":       "pmo_genai" if is_hbr_topic else "any",
        "format":       "hbr_summary" if is_hbr_topic else "news_insight",
        "topic":        topic,
        "keywords_used":[topic],
        "hashtags_used":[],
        "sources":      [n["source"] for n in news[:2]],
        "generated_at": datetime.now().isoformat(),
        "status":       "draft",
        "is_hbr":       is_hbr_topic,
        "hbr_image":    hbr_image,
    }

    post_id = store.save_draft(post)
    post["id"] = post_id
    store.set_active_post(post_id)
    store.update_status(
        post_id, "whatsapp_sent",
        sent_to_whatsapp_at=datetime.now().isoformat()
    )
    whatsapp.send_draft_for_approval(post_id, post)


def handle_whatsapp_reply(reply_text: str) -> str:
    global _pending_news

    parsed   = whatsapp.parse_reply(reply_text)
    action   = parsed["action"]
    feedback = parsed.get("feedback","")

    print(f"[Agent] Reply: action={action}, feedback='{feedback}'")

    # ── TOPIC ON DEMAND ────────────────────────────────────
    if action == "topic":
        if not feedback:
            return "Please tell me the topic.\nExample:\nTOPIC RBI FMEA circular\nTOPIC Harvard AI project management"
        threading.Thread(target=generate_on_topic, args=(feedback,), daemon=True).start()
        return f"🔍 Got it! Writing about:\n_{feedback}_\n\nCheck WhatsApp in 60 seconds! ⏳"

    # Get pending post — from DB first (survives restarts)
    post_id = store.get_active_post_id()
    if not post_id:
        pending = store.get_latest_pending()
        if pending:
            post_id = pending["id"]
        else:
            return (
                "No pending post found.\n\n"
                "You can:\n"
                "⚡ Use control panel to generate\n"
                "📌 Send: TOPIC [your topic]\n"
                "Example: TOPIC RBI Fair Practice Code"
            )

    # ── APPROVE ────────────────────────────────────────────
    if action == "approve":
        post = store.get_post(post_id)
        if not post:
            return "Post not found."

        # Fetch image in parallel with LinkedIn auth
        image_bytes = None
        if config.INCLUDE_IMAGE:
            try:
                import image_fetcher
                # Check for HBR article image first
                hbr_image_url = post.get("hbr_image","")
                if hbr_image_url:
                    print(f"[Agent] Using HBR article image...")
                    image_bytes = image_fetcher.download_image(hbr_image_url)

                # Fall back to Pexels if no HBR image
                if not image_bytes:
                    img = image_fetcher.get_image_for_post(
                        pillar=post.get("pillar","any"),
                        topic=post.get("topic",""),
                        post_text=post.get("post_text",""),
                    )
                    if img:
                        image_bytes = image_fetcher.download_image(img["url"])
                        print(f"[Agent] Pexels image ready: {img['photographer']}")
            except Exception as e:
                print(f"[Agent] Image error: {e}")

        result = linkedin_api.post_to_linkedin(
            post["post_text"],
            image_bytes=image_bytes
        )

        if result["success"]:
            store.update_status(post_id, "posted", linkedin_post_id=result["post_id"])
            store.clear_active_post()   # ← Clear DB tracking

            def _reminder():
                time.sleep(config.ENGAGEMENT_REMINDER_MINUTES * 60)
                whatsapp.send_engagement_reminder(post_id)
            threading.Thread(target=_reminder, daemon=True).start()

            return (
                f"✅ *Posted to LinkedIn!*\n\n"
                f"Post #{post_id} is now live! 🎉\n"
                f"{'🖼️ With image!' if image_bytes else '📝 Text only'}\n\n"
                f"I'll remind you in {config.ENGAGEMENT_REMINDER_MINUTES} min to engage."
            )
        else:
            store.update_status(post_id, "failed")
            return f"❌ LinkedIn posting failed:\n{result['error']}"

    # ── EDIT ───────────────────────────────────────────────
    elif action == "edit":
        if not feedback:
            return "Tell me what to change.\nExample: EDIT make it shorter and add more about DMAIC"
        try:
            post   = store.get_post(post_id)
            pillar = post.get("pillar","regulatory")
            fmt    = post.get("format","news_insight")
            new_post = post_generator.regenerate_post(
                post_id=post_id, news_items=_pending_news,
                pillar=pillar, fmt=fmt, feedback=feedback
            )
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
            post   = store.get_post(post_id)
            pillar = post.get("pillar","regulatory")
            fmt    = post.get("format","news_insight")
            new_post = post_generator.regenerate_post(
                post_id=post_id, news_items=_pending_news,
                pillar=pillar, fmt=fmt, feedback=feedback
            )
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
        store.clear_active_post()
        return (
            "⏭ Skipped.\n\n"
            "📌 Send TOPIC [topic] to write about anything anytime!\n"
            "Example: TOPIC Harvard AI project management"
        )

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
            "Example: TOPIC Harvard AI project management article"
        )


def approve_and_post(post_id: int) -> dict:
    post = store.get_post(post_id)
    if not post:
        return {"success": False, "error": "Post not found"}
    result = linkedin_api.post_to_linkedin(post["post_text"])
    if result["success"]:
        store.update_status(post_id, "posted", linkedin_post_id=result["post_id"])
        store.clear_active_post()
    return result


def run_weekly_summary():
    print("[Agent] Sending weekly summary...")
    stats = store.get_week_stats()
    whatsapp.send_weekly_summary(stats)


if __name__ == "__main__":
    store.init_db()
    run_daily_cycle()
