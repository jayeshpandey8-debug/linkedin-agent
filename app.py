"""
app.py
Flask server for Jayesh's LinkedIn Agent.

Responsibilities:
  1. APScheduler — triggers daily post cycle at right time
  2. Twilio WhatsApp webhook — receives Jayesh's replies
  3. LinkedIn OAuth callback — handles token exchange
  4. Admin API — manual triggers, post history
"""

from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pytz
from datetime import datetime

import config
import store
import agent
import whatsapp
import linkedin_api

app     = Flask(__name__)
IST     = pytz.timezone("Asia/Kolkata")

# ─────────────────────────────────────────────────────────────
# Scheduler Setup
# ─────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler(timezone=IST)

# Add daily post jobs for each scheduled day
for day_of_week, time_cfg in config.POSTING_SCHEDULE.items():
    scheduler.add_job(
        agent.run_daily_cycle,
        trigger="cron",
        day_of_week=day_of_week,
        hour=time_cfg["hour"],
        minute=time_cfg["minute"],
        id=f"daily_post_day_{day_of_week}",
        misfire_grace_time=300,
    )

# Weekly summary — every Sunday at 9:00 AM IST
scheduler.add_job(
    agent.run_weekly_summary,
    trigger="cron",
    day_of_week=config.WEEKLY_SUMMARY_DAY,
    hour=config.WEEKLY_SUMMARY_HOUR,
    minute=config.WEEKLY_SUMMARY_MINUTE,
    id="weekly_summary",
)

scheduler.start()
atexit.register(lambda: scheduler.shutdown())
print("[Scheduler] All jobs registered.")


# ─────────────────────────────────────────────────────────────
# WhatsApp Webhook (Twilio sends POST here when Jayesh replies)
# ─────────────────────────────────────────────────────────────

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    Twilio calls this endpoint when Jayesh replies on WhatsApp.
    Must return TwiML response.
    """
    incoming_msg = request.form.get("Body", "").strip()
    from_number  = request.form.get("From", "")

    print(f"[Webhook] Incoming from {from_number}: '{incoming_msg}'")

    # Security: only accept from Jayesh's number
    if config.TWILIO_WHATSAPP_TO not in from_number:
        print(f"[Webhook] ⚠️ Unauthorized sender: {from_number}")
        resp = MessagingResponse()
        resp.message("Unauthorized.")
        return str(resp)

    # Handle the reply
    response_text = agent.handle_whatsapp_reply(incoming_msg)

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)


# ─────────────────────────────────────────────────────────────
# LinkedIn OAuth Callback
# ─────────────────────────────────────────────────────────────

@app.route("/callback")
def linkedin_callback():
    """LinkedIn redirects here after OAuth authorization."""
    code  = request.args.get("code", "")
    error = request.args.get("error", "")

    if error:
        return f"❌ LinkedIn OAuth error: {error}", 400

    if not code:
        return "❌ No code received.", 400

    token_data = linkedin_api.exchange_code_for_token(
        code=code,
        redirect_uri="http://localhost:8080/callback",
    )

    if token_data.get("access_token"):
        token = token_data["access_token"]
        return f"""
        <h2>✅ LinkedIn Token Obtained!</h2>
        <p>Copy this into your <code>.env</code> file:</p>
        <pre>LINKEDIN_ACCESS_TOKEN={token}</pre>
        <p>Token expires in: {token_data.get('expires_in', '?')} seconds
        (~{token_data.get('expires_in', 0)//86400} days)</p>
        """, 200
    else:
        return "❌ Token exchange failed. Check logs.", 500


# ─────────────────────────────────────────────────────────────
# Admin API Routes
# ─────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id":       job.id,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return jsonify({
        "status":    "running",
        "time_ist":  datetime.now(IST).strftime("%d %b %Y %H:%M IST"),
        "jobs":      jobs,
        "auto_post": config.AUTO_POST,
    })


@app.route("/api/posts")
def api_posts():
    return jsonify(store.get_all_posts(limit=50))


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Manually trigger post generation."""
    import threading
    threading.Thread(target=agent.run_daily_cycle, daemon=True).start()
    return jsonify({"message": "Generation triggered. WhatsApp draft coming shortly."})


@app.route("/api/posts/<int:post_id>")
def api_get_post(post_id):
    post = store.get_post(post_id)
    return jsonify(post) if post else (jsonify({"error": "Not found"}), 404)


@app.route("/api/test-whatsapp", methods=["POST"])
def api_test_whatsapp():
    """Send a test WhatsApp message."""
    result = whatsapp.send_message(
        "✅ *LinkedIn Agent Test*\n\nConnection confirmed! Agent is running. 🚀"
    )
    return jsonify({"success": result})


@app.route("/api/weekly-summary", methods=["POST"])
def api_weekly_summary():
    """Manually trigger weekly summary."""
    agent.run_weekly_summary()
    return jsonify({"message": "Weekly summary sent to WhatsApp."})


# ─────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "agent":  "Jayesh LinkedIn Agent",
        "status": "running",
        "endpoints": [
            "POST /webhook/whatsapp  — Twilio webhook",
            "GET  /api/status        — Scheduler status",
            "GET  /api/posts         — Post history",
            "POST /api/generate      — Manual trigger",
            "POST /api/test-whatsapp — Test WhatsApp",
        ]
    })


if __name__ == "__main__":
    store.init_db()
    print(f"[App] Jayesh LinkedIn Agent starting...")
    print(f"[App] WhatsApp webhook: POST /webhook/whatsapp")
    print(f"[App] Running on port {config.DASHBOARD_PORT}")
    app.run(
        host="0.0.0.0",
        port=config.DASHBOARD_PORT,
        debug=False,
    )
