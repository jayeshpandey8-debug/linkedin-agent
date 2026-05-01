"""
app.py
Flask server for Jayesh's LinkedIn Agent.

Responsibilities:
  1. APScheduler — triggers daily post cycle at right time
  2. Twilio WhatsApp webhook — receives Jayesh's replies
  3. LinkedIn OAuth callback — handles token exchange
  4. Admin API — manual triggers, post history
"""

from flask import Flask, request, jsonify, render_template_string
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
    """Manually trigger post generation — ignores schedule."""
    import threading
    def _run():
        import news_fetcher, post_generator, whatsapp, store
        from datetime import datetime
        print("[Manual] Force generating post...")
        pillar = "regulatory"
        fmt    = "news_insight"
        news   = news_fetcher.get_news_for_pillar(pillar)
        post   = post_generator.generate_post(news, pillar=pillar, fmt=fmt)
        post_id = store.save_draft(post)
        post["id"] = post_id
        print(f"[Manual] Draft #{post_id} saved. Sending to WhatsApp...")
        whatsapp.send_draft_for_approval(post_id, post)
        print(f"[Manual] WhatsApp sent!")
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"message": "Generating post... Check WhatsApp in 60 seconds!"})


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
    return render_template_string(TRIGGER_HTML)


TRIGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Jayesh LinkedIn Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               background: linear-gradient(135deg, #1E3A8A, #3730A3);
               min-height: 100vh; display: flex; align-items: center;
               justify-content: center; padding: 20px; }
        .card { background: white; border-radius: 20px; padding: 40px;
                max-width: 400px; width: 100%; text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        .avatar { width: 80px; height: 80px;
                  background: linear-gradient(135deg, #1E3A8A, #3730A3);
                  border-radius: 50%; margin: 0 auto 20px; display: flex;
                  align-items: center; justify-content: center; font-size: 36px; }
        h1 { color: #1E3A8A; font-size: 22px; margin-bottom: 8px; }
        .subtitle { color: #6B7280; font-size: 13px; margin-bottom: 30px; }
        .btn { display: block; width: 100%; padding: 16px; border: none;
               border-radius: 12px; font-size: 16px; font-weight: 700;
               cursor: pointer; margin-bottom: 12px; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #1E3A8A, #3730A3); color: white; }
        .btn-secondary { background: #F3F4F6; color: #374151; }
        .status { margin-top: 20px; padding: 12px; border-radius: 10px;
                  font-size: 14px; display: none; }
        .status.success { background: #D1FAE5; color: #065F46; display: block; }
        .status.error { background: #FEE2E2; color: #991B1B; display: block; }
        .status.loading { background: #DBEAFE; color: #1E40AF; display: block; }
        .schedule { margin-top: 24px; text-align: left; background: #F9FAFB;
                    border-radius: 12px; padding: 16px; }
        .schedule h3 { color: #374151; font-size: 13px; margin-bottom: 10px; }
        .schedule-item { display: flex; justify-content: space-between;
                         font-size: 12px; color: #6B7280; padding: 4px 0;
                         border-bottom: 1px solid #E5E7EB; }
        .schedule-item:last-child { border-bottom: none; }
        .day { font-weight: 600; color: #374151; }
    </style>
</head>
<body>
    <div class="card">
        <div class="avatar">🤖</div>
        <h1>Jayesh LinkedIn Agent</h1>
        <p class="subtitle">Banking · NBFC · Lean Six Sigma · RCA · GenAI</p>
        <button class="btn btn-primary" onclick="generatePost()">⚡ Generate & Send to WhatsApp</button>
        <button class="btn btn-secondary" onclick="testWhatsapp()">📱 Test WhatsApp Connection</button>
        <button class="btn btn-secondary" onclick="weeklySummary()">📊 Send Weekly Summary</button>
        <div id="status" class="status"></div>
        <div class="schedule">
            <h3>📅 Posting Schedule (IST)</h3>
            <div class="schedule-item"><span class="day">Monday</span><span>8:30 AM · Regulatory</span></div>
            <div class="schedule-item"><span class="day">Tuesday</span><span>12:00 PM · RCA/FMEA</span></div>
            <div class="schedule-item"><span class="day">Wednesday</span><span>8:30 AM · Lean Six Sigma</span></div>
            <div class="schedule-item"><span class="day">Thursday</span><span>12:00 PM · Poll</span></div>
            <div class="schedule-item"><span class="day">Saturday</span><span>10:00 AM · Personal Story</span></div>
            <div class="schedule-item"><span class="day">Sunday</span><span>9:00 AM · Weekly Summary</span></div>
        </div>
    </div>
    <script>
        function showStatus(msg, type) {
            const el = document.getElementById('status');
            el.className = 'status ' + type;
            el.innerHTML = msg;
        }
        async function generatePost() {
            showStatus('⏳ Generating post... Check WhatsApp in 40 seconds!', 'loading');
            try {
                const r = await fetch('/api/generate', { method: 'POST' });
                const data = await r.json();
                showStatus('✅ Done! Check WhatsApp for draft. Reply YES to post!', 'success');
            } catch(e) { showStatus('❌ Error: ' + e.message, 'error'); }
        }
        async function testWhatsapp() {
            showStatus('⏳ Sending test message...', 'loading');
            try {
                const r = await fetch('/api/test-whatsapp', { method: 'POST' });
                const data = await r.json();
                if(data.success) { showStatus('✅ Test message sent! Check WhatsApp.', 'success'); }
                else { showStatus('❌ WhatsApp test failed.', 'error'); }
            } catch(e) { showStatus('❌ Error: ' + e.message, 'error'); }
        }
        async function weeklySummary() {
            showStatus('⏳ Sending weekly summary...', 'loading');
            try {
                await fetch('/api/weekly-summary', { method: 'POST' });
                showStatus('✅ Weekly summary sent to WhatsApp!', 'success');
            } catch(e) { showStatus('❌ Error: ' + e.message, 'error'); }
        }
    </script>
</body>
</html>
"""


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
