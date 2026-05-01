# Jayesh Pandey — LinkedIn AI Agent
**Claude-powered LinkedIn automation | WhatsApp approval | Railway cloud hosting**

---

## What It Does

Every scheduled day, the agent:
1. Picks the right content pillar + format for that day
2. Fetches fresh news (last 24-48 hrs) from RBI website + NewsAPI
3. Claude generates a polished LinkedIn post in your brand voice
4. Sends the draft to your WhatsApp (+91 9004141203) for approval
5. You reply YES/EDIT/REDO/NO from your phone
6. On YES → posts to LinkedIn automatically
7. 30 minutes later → WhatsApp reminder to engage with your post
8. Every Sunday → weekly performance summary on WhatsApp

---

## Content Schedule

| Day | Time (IST) | Pillar | Format |
|-----|-----------|--------|--------|
| Monday | 8:30 AM | RBI / Regulatory | News + Insight |
| Tuesday | 12:00 PM | RCA / FMEA | Did You Know? |
| Wednesday | 8:30 AM | Lean Six Sigma | DMAIC Case |
| Thursday | 12:00 PM | Any (best topic) | Poll |
| Saturday | 10:00 AM | PMO / GenAI | Personal Story |
| Sunday | 9:00 AM | — | Weekly Summary (WhatsApp only) |

---

## Project Files

```
jayesh_agent/
├── app.py                  ← Flask server + scheduler + WhatsApp webhook
├── agent.py                ← Main orchestrator (daily cycle + weekly summary)
├── config.py               ← All settings + Jayesh's full resume context
├── news_fetcher.py         ← RBI scraper + NewsAPI for all 5 pillars
├── post_generator.py       ← Claude API + 6 post formats + SEO logic
├── linkedin_api.py         ← LinkedIn UGC Posts API
├── whatsapp.py             ← Twilio WhatsApp send/receive/parse
├── store.py                ← SQLite history + topic memory (no-repeat)
├── get_linkedin_token.py   ← One-time OAuth helper
├── requirements.txt
├── Procfile                ← Railway deployment
├── .gitignore              ← Keeps .env safe
└── .env.example            ← Copy to .env and fill in
```

---

## Setup Guide

### Step 1 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Configure .env
```bash
cp .env.example .env
```
Open `.env` and fill in:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET` — from LinkedIn Developer App
- `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` — from Twilio console
- `NEWS_API_KEY` — from newsapi.org (free)

### Step 3 — Get LinkedIn Access Token (run once)
```bash
python get_linkedin_token.py
```
Browser opens → log in to LinkedIn → token printed → paste into `.env`

### Step 4 — Test WhatsApp connection
```bash
python -c "import whatsapp; whatsapp.send_message('Agent test! 🚀')"
```
You should receive a WhatsApp from Twilio sandbox.

### Step 5 — Test post generation
```bash
python agent.py
```
This runs one full cycle → generates a draft → sends to your WhatsApp.
Reply YES/EDIT/REDO/NO from your phone.

### Step 6 — Run locally (optional)
```bash
python app.py
```
Agent runs with scheduler. But it stops when your laptop closes.

---

## Railway Deployment (Always-On Cloud)

### Step 1 — Create Railway account
Go to railway.app → Sign up with GitHub

### Step 2 — Push code to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/jayesh-linkedin-agent.git
git push -u origin main
```
⚠️ Make sure `.env` is in `.gitignore` — NEVER push secrets to GitHub.

### Step 3 — Deploy on Railway
1. Go to railway.app → New Project → Deploy from GitHub
2. Select your repository
3. Railway auto-detects Python and uses Procfile

### Step 4 — Add Environment Variables on Railway
In Railway dashboard → Your project → Variables → Add all from `.env`:
```
ANTHROPIC_API_KEY
LINKEDIN_CLIENT_ID
LINKEDIN_CLIENT_SECRET
LINKEDIN_ACCESS_TOKEN
LINKEDIN_PERSON_URN
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
TWILIO_WHATSAPP_TO
NEWS_API_KEY
DASHBOARD_SECRET
```

### Step 5 — Configure Twilio Webhook
This is critical — tells Twilio where to send your WhatsApp replies.

1. Go to Twilio Console → Messaging → Settings → WhatsApp Sandbox Settings
2. Under "When a message comes in" paste your Railway URL:
```
https://your-app-name.up.railway.app/webhook/whatsapp
```
3. Method: HTTP POST
4. Click Save

### Step 6 — Verify deployment
Visit: `https://your-app-name.up.railway.app/api/status`
Should return JSON with scheduler jobs and next run times.

---

## WhatsApp Reply Guide

When you receive a draft on WhatsApp, reply with:

| Reply | Action |
|-------|--------|
| `YES` | Posts immediately to LinkedIn |
| `EDIT make it shorter` | Regenerates with your feedback |
| `EDIT add more about FMEA` | Regenerates with specific instruction |
| `REDO` | Completely regenerates from scratch |
| `NO` | Skips today's post |

---

## Security Checklist

- ✅ `.env` is in `.gitignore` — never pushed to GitHub
- ✅ LinkedIn token scope: `w_member_social` only — cannot touch your settings
- ✅ WhatsApp webhook only accepts messages from your number (+91 9004141203)
- ✅ AUTO_POST is permanently set to False — your WhatsApp approval is mandatory
- ✅ All secrets stored in Railway encrypted environment variables
- ✅ LinkedIn token auto-expires in 60 days — agent reminds you 7 days before

---

## Maintenance

**LinkedIn token renewal (every 60 days):**
```bash
python get_linkedin_token.py
```
Update `LINKEDIN_ACCESS_TOKEN` in Railway Variables.

**View post history:**
Visit `https://your-app.up.railway.app/api/posts`

**Manual trigger:**
```bash
curl -X POST https://your-app.up.railway.app/api/generate
```

---

## Cost Estimate

| Service | Cost |
|---------|------|
| Railway hosting | ~₹420/month |
| Anthropic API | ~₹50-100/month (4-5 posts/week) |
| Twilio WhatsApp sandbox | Free |
| NewsAPI | Free (100 req/day) |
| **Total** | **~₹500-520/month** |
