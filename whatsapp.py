"""
whatsapp.py - Fixed version with message splitting
"""
from twilio.rest import Client
from datetime import datetime
import config

client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
MAX_LENGTH = 1500

def send_message(body: str) -> bool:
    try:
        chunks = _split_message(body)
        for chunk in chunks:
            client.messages.create(
                from_=config.TWILIO_WHATSAPP_FROM,
                to=config.TWILIO_WHATSAPP_TO,
                body=chunk,
            )
        print(f"[WhatsApp] Sent {len(chunks)} message(s).")
        return True
    except Exception as e:
        print(f"[WhatsApp] Send error: {e}")
        return False

def _split_message(body: str) -> list:
    if len(body) <= MAX_LENGTH:
        return [body]
    chunks = []
    while len(body) > MAX_LENGTH:
        split_at = body[:MAX_LENGTH].rfind('\n')
        if split_at == -1:
            split_at = MAX_LENGTH
        chunks.append(body[:split_at].strip())
        body = body[split_at:].strip()
    if body:
        chunks.append(body)
    return chunks

def send_draft_for_approval(post_id: int, post: dict) -> bool:
    pillar_emoji = {"regulatory":"📋","rca_fmea":"🔍","lean_excellence":"⚙️","pmo_genai":"🤖","any":"💡"}
    fmt_label = {"news_insight":"News + Insight","did_you_know":"Did You Know?","dmaic_case":"DMAIC Case","poll":"Poll","personal_story":"Personal Story","rca_tip":"RCA Tip"}
    emoji = pillar_emoji.get(post.get("pillar",""),"📝")
    fmt   = fmt_label.get(post.get("format",""),"Post")
    now   = datetime.now().strftime("%a, %d %b — %I:%M %p IST")
    header = f"{emoji} *LINKEDIN DRAFT #{post_id}*\n📅 {now}\n🏷 Format: {fmt}\n─────────────────────"
    post_text = post.get("post_text","")
    max_post_len = MAX_LENGTH - len(header) - 50
    if len(post_text) > max_post_len:
        post_text = post_text[:max_post_len] + "..."
    part1 = f"{header}\n\n{post_text}"
    part2 = "─────────────────────\nReply:\n✅ *YES* — Post it\n✏️ *EDIT [feedback]*\n🔄 *REDO* — Regenerate\n❌ *NO* — Skip"
    send_message(part1)
    return send_message(part2)

def send_engagement_reminder(post_id: int) -> bool:
    return send_message(f"🔔 *REMINDER*\nPost #{post_id} is live 30 min!\n\nOpen LinkedIn → Like + comment on your post now.\nThis boosts your reach! 🚀")

def send_weekly_summary(stats: dict) -> bool:
    return send_message(f"📊 *WEEKLY SUMMARY*\nWeek of {stats.get('week_start','')}\n\nGenerated: {stats.get('posts_generated',0)}\n✅ Posted: {stats.get('posts_posted',0)}\n❌ Rejected: {stats.get('posts_rejected',0)}\n⏭ Skipped: {stats.get('posts_skipped',0)}")

def send_error_alert(error_msg: str) -> bool:
    return send_message(f"🚨 *AGENT ERROR*\n\n{error_msg}")

def parse_reply(reply_text: str) -> dict:
    text = reply_text.strip().upper()
    original = reply_text.strip()
    if text in ("YES","Y","YEP","YA","OK","OKAY","POST","POST IT","HAAN"):
        return {"action":"approve","feedback":""}
    if text in ("NO","N","SKIP","CANCEL","PASS","NAHI"):
        return {"action":"skip","feedback":""}
    if text in ("REDO","REGENERATE","AGAIN","RETRY","NEW","REWRITE"):
        return {"action":"redo","feedback":""}
    if original.upper().startswith("EDIT"):
        return {"action":"edit","feedback":original[4:].strip().lstrip(":").strip()}
    if original.upper().startswith("REDO"):
        return {"action":"redo","feedback":original[4:].strip().lstrip(":").strip()}
    if any(w in text for w in ["YES","APPROVE","POST","GOOD","PERFECT"]):
        return {"action":"approve","feedback":""}
    if any(w in text for w in ["NO","SKIP","DONT","DON'T","CANCEL"]):
        return {"action":"skip","feedback":""}
    return {"action":"unknown","feedback":original}
