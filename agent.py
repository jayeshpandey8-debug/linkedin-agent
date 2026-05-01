"""
agent.py
Core orchestrator for Jayesh's LinkedIn Agent.

Daily cycle:
  1. Determine today's pillar + format from rotation
  2. Fetch fresh news for that pillar
  3. Generate post via Claude
  4. Send to Jayesh's WhatsApp for approval
  5. Wait for reply (handled by webhook in app.py)
  6. On YES → post to LinkedIn + send engagement reminder in 30 min
  7. On EDIT/REDO → regenerate + resend
  8. On NO → skip, log as skipped
  9. Sunday → send weekly stats summary
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

# In-memory state for pending post (survives within session)
# For production, this is persisted via DB status field
_pending_post_id   = None
_pending_news      = []


def get_todays_rotation() -> tuple[str, str]:
    """Returns (pillar, format) for today based on the content rotation schedule."""
    today_dow = datetime.now(IST).weekday()   # 0=Mon, 6=Sun
    rotation  = config.CONTENT_ROTATION.get(today_dow)

    if not rotation:
        return None, None   # No post scheduled today

    pillar, fmt = rotation

    # Smart override: if same pillar was used last 2 days, rotate to next
    recent_pillars = store.get_recent_pillars(limit=2)
    if pillar != "any" and pillar in recent_pillars[:2]:
        # Find alternative pillar
        all_pillars = list(config.PILLARS.keys())
        all_pillars.remove("any")
        for alt in all_pillars:
            if alt not in recent_pillars:
                print(f"[Agent] Pillar override: {pillar} → {alt} (used recently)")
                pillar = alt
                break

    return pillar, fmt


def run_daily_cycle():
    """
    Full daily posting cycle.
    Called by APScheduler at the right time each day.
    """
    global _pending_post_id, _pending_news

    now_ist = datetime.now(IST)
    print(f"\n[Agent] ═══ Daily Cycle — {now_ist.strftime('%A %d %b %Y %H:%M IST')} ═══")

    pillar, fmt = get_todays_rotation()

    if not pillar:
        print("[Agent] No post scheduled today.")
        return

    print(f"[Agent] Pillar: {pillar} | Format: {fmt}")

    # Step 1: Fetch news
    recent_topics = store.get_recent_topics(limit=config.MEMORY_LOOKBACK_POSTS)
    news = news_fetcher.get_news_for_pillar(pillar, recent_topics=recent_topics)

    if not news:
        whatsapp.send_error_alert("Could not fetch news today. No post generated.")
        return

    _pending_news = news

    # Step 2: Generate post
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

    # Step 3: Save as draft
    post_id = store.save_draft(post)
    post["id"] = post_id
    _pending_post_id = post_id
    print(f"[Agent] Draft saved — ID: {post_id}")

    # Step 4: Send to WhatsApp
    store.update_status(post_id, "whatsapp_sent",
                        sent_to_whatsapp_at=datetime.now().isoformat())
    success = whatsapp.send_draft_for_approval(post_id, post)

    if not success:
        print("[Agent] ⚠️ WhatsApp send failed — check Twilio config.")
        whatsapp.send_error_alert("Failed to send draft to WhatsApp.")


def handle_whatsapp_reply(reply_text: str) -> str:
    """
    Called from Flask webhook when Jayesh replies on WhatsApp.
    Returns response message to send back.
    """
    global _pending_post_id, _pending_news

    parsed = whatsapp.parse_reply(reply_text)
    action = parsed["action"]
    feedback = parsed.get("feedback", "")

    print(f"[Agent] WhatsApp reply received: action={action}, feedback='{feedback}'")

    # Get latest pending post if not in memory
    if not _pending_post_id:
        pending = store.get_latest_pending()
        if pending:
            _pending_post_id = pending["id"]
        else:
            return "No pending post found. The next draft will be sent at the scheduled time."

    post_id = _pending_post_id

    # ── APPROVE ────────────────────────────────────────────
    if action == "approve":
        post = store.get_post(post_id)
        if not post:
            return "Post not found. Please wait for the next draft."

        print(f"[Agent] Posting #{post_id} to LinkedIn...")
        result = linkedin_api.post_to_linkedin(post["post_text"])

        if result["success"]:
            store.update_status(post_id, "posted", linkedin_post_id=result["post_id"])
            _pending_post_id = None

            # Schedule engagement reminder in 30 min
            def _reminder():
                time.sleep(config.ENGAGEMENT_REMINDER_MINUTES * 60)
                whatsapp.send_engagement_reminder(post_id)

            threading.Thread(target=_reminder, daemon=True).start()

            return (
                f"✅ *Posted to LinkedIn!*\n\n"
                f"Your post is now live. 🎉\n"
                f"I'll remind you in {config.ENGAGEMENT_REMINDER_MINUTES} minutes "
                f"to engage with it for better reach."
            )
        else:
            store.update_status(post_id, "failed")
            return f"❌ LinkedIn posting failed:\n{result['error']}\n\nPlease check your token."

    # ── EDIT ───────────────────────────────────────────────
    elif action == "edit":
        if not feedback:
            return "Please tell me what to change. Example: EDIT make it shorter and add more about DMAIC"

        print(f"[Agent] Regenerating #{post_id} with feedback: {feedback}")
        try:
            pillar = store.get_post(post_id).get("pillar", "regulatory")
            fmt    = store.get_post(post_id).get("format", "news_insight")

            new_post = post_generator.regenerate_post(
                post_id=post_id,
                news_items=_pending_news,
                pillar=pillar,
                fmt=fmt,
                feedback=feedback,
            )
            store.update_post_text(post_id, new_post["post_text"])
            store.update_status(post_id, "whatsapp_sent", feedback=feedback)

            # Resend to WhatsApp
            new_post["id"] = post_id
            whatsapp.send_draft_for_approval(post_id, new_post)
            return "🔄 Regenerated with your feedback! Check the new draft above."

        except Exception as e:
            return f"❌ Regeneration failed: {e}"

    # ── REDO ───────────────────────────────────────────────
    elif action == "redo":
        print(f"[Agent] Regenerating #{post_id} from scratch...")
        try:
            pillar = store.get_post(post_id).get("pillar", "regulatory")
            fmt    = store.get_post(post_id).get("format", "news_insight")

            new_post = post_generator.regenerate_post(
                post_id=post_id,
                news_items=_pending_news,
                pillar=pillar,
                fmt=fmt,
                feedback=feedback,
            )
            store.update_post_text(post_id, new_post["post_text"])
            store.update_status(post_id, "whatsapp_sent")

            new_post["id"] = post_id
            whatsapp.send_draft_for_approval(post_id, new_post)
            return "🔄 Completely regenerated! New draft sent above."

        except Exception as e:
            return f"❌ Regeneration failed: {e}"

    # ── SKIP ───────────────────────────────────────────────
    elif action == "skip":
        store.update_status(post_id, "rejected")
        _pending_post_id = None
        return "⏭ Skipped. Next post will arrive at the next scheduled time."

    # ── UNKNOWN ────────────────────────────────────────────
    else:
        return (
            "I didn't understand that. Please reply with:\n"
            "✅ *YES* — Post it\n"
            "✏️ *EDIT [feedback]* — e.g. EDIT make it shorter\n"
            "🔄 *REDO* — Regenerate\n"
            "❌ *NO* — Skip"
        )


def run_weekly_summary():
    """Called every Sunday morning — sends analytics summary."""
    print("[Agent] Sending weekly summary...")
    stats = store.get_week_stats()
    whatsapp.send_weekly_summary(stats)


if __name__ == "__main__":
    store.init_db()
    run_daily_cycle()
