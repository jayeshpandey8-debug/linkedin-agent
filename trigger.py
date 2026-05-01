"""
trigger.py
Simple one-click web page to trigger post generation from browser.
Add this to your Railway deployment.
"""

from flask import Blueprint, render_template_string
import requests

trigger_bp = Blueprint('trigger', __name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Jayesh LinkedIn Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1E3A8A, #3730A3);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 400px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .avatar {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #1E3A8A, #3730A3);
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
        }
        h1 { color: #1E3A8A; font-size: 22px; margin-bottom: 8px; }
        .subtitle { color: #6B7280; font-size: 13px; margin-bottom: 30px; }
        .btn {
            display: block;
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            margin-bottom: 12px;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #1E3A8A, #3730A3);
            color: white;
        }
        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn-secondary {
            background: #F3F4F6;
            color: #374151;
        }
        .btn-secondary:hover { background: #E5E7EB; }
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 10px;
            font-size: 14px;
            display: none;
        }
        .status.success { background: #D1FAE5; color: #065F46; display: block; }
        .status.error { background: #FEE2E2; color: #991B1B; display: block; }
        .status.loading { background: #DBEAFE; color: #1E40AF; display: block; }
        .schedule {
            margin-top: 24px;
            text-align: left;
            background: #F9FAFB;
            border-radius: 12px;
            padding: 16px;
        }
        .schedule h3 { color: #374151; font-size: 13px; margin-bottom: 10px; }
        .schedule-item {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #6B7280;
            padding: 4px 0;
            border-bottom: 1px solid #E5E7EB;
        }
        .schedule-item:last-child { border-bottom: none; }
        .day { font-weight: 600; color: #374151; }
    </style>
</head>
<body>
    <div class="card">
        <div class="avatar">🤖</div>
        <h1>Jayesh LinkedIn Agent</h1>
        <p class="subtitle">Banking · NBFC · Lean Six Sigma · RCA · GenAI</p>

        <button class="btn btn-primary" onclick="generatePost()">
            ⚡ Generate & Send to WhatsApp
        </button>

        <button class="btn btn-secondary" onclick="testWhatsapp()">
            📱 Test WhatsApp Connection
        </button>

        <button class="btn btn-secondary" onclick="weeklySummary()">
            📊 Send Weekly Summary
        </button>

        <div id="status" class="status"></div>

        <div class="schedule">
            <h3>📅 Posting Schedule (IST)</h3>
            <div class="schedule-item">
                <span class="day">Monday</span>
                <span>8:30 AM · Regulatory</span>
            </div>
            <div class="schedule-item">
                <span class="day">Tuesday</span>
                <span>12:00 PM · RCA/FMEA</span>
            </div>
            <div class="schedule-item">
                <span class="day">Wednesday</span>
                <span>8:30 AM · Lean Six Sigma</span>
            </div>
            <div class="schedule-item">
                <span class="day">Thursday</span>
                <span>12:00 PM · Poll</span>
            </div>
            <div class="schedule-item">
                <span class="day">Saturday</span>
                <span>10:00 AM · Personal Story</span>
            </div>
            <div class="schedule-item">
                <span class="day">Sunday</span>
                <span>9:00 AM · Weekly Summary</span>
            </div>
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
                showStatus('✅ Done! Check your WhatsApp for the draft. Reply YES to post!', 'success');
            } catch(e) {
                showStatus('❌ Error: ' + e.message, 'error');
            }
        }

        async function testWhatsapp() {
            showStatus('⏳ Sending test message...', 'loading');
            try {
                const r = await fetch('/api/test-whatsapp', { method: 'POST' });
                const data = await r.json();
                if(data.success) {
                    showStatus('✅ Test message sent! Check WhatsApp now.', 'success');
                } else {
                    showStatus('❌ WhatsApp test failed. Check Twilio settings.', 'error');
                }
            } catch(e) {
                showStatus('❌ Error: ' + e.message, 'error');
            }
        }

        async function weeklySummary() {
            showStatus('⏳ Sending weekly summary...', 'loading');
            try {
                const r = await fetch('/api/weekly-summary', { method: 'POST' });
                showStatus('✅ Weekly summary sent to WhatsApp!', 'success');
            } catch(e) {
                showStatus('❌ Error: ' + e.message, 'error');
            }
        }
    </script>
</body>
</html>
"""

@trigger_bp.route('/trigger')
def trigger_page():
    return render_template_string(HTML)
