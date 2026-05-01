"""
config.py
All configuration for Jayesh Pandey LinkedIn Agent.
Reads from .env file — never hardcode secrets here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ───────────────────────────────────────────────
ANTHROPIC_API_KEY       = os.getenv("ANTHROPIC_API_KEY", "")
NEWS_API_KEY            = os.getenv("NEWS_API_KEY", "")

# ── LinkedIn OAuth ─────────────────────────────────────────
LINKEDIN_CLIENT_ID      = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET  = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN   = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN     = os.getenv("LINKEDIN_PERSON_URN", "")

# ── Twilio WhatsApp ────────────────────────────────────────
TWILIO_ACCOUNT_SID      = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN       = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM    = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_WHATSAPP_TO      = os.getenv("TWILIO_WHATSAPP_TO", "whatsapp:+919004141203")

# ── Dashboard ──────────────────────────────────────────────
DASHBOARD_PORT          = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_SECRET        = os.getenv("DASHBOARD_SECRET", "change_me_in_prod")

# ── Auto-post (always False — WhatsApp approval required) ─
AUTO_POST               = False   # NEVER change this to True

# ── Posting Schedule (IST, 24hr) ──────────────────────────
# Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
POSTING_SCHEDULE = {
    0: {"hour": 8,  "minute": 30},   # Monday    08:30 IST
    1: {"hour": 12, "minute": 0},    # Tuesday   12:00 IST
    2: {"hour": 8,  "minute": 30},   # Wednesday 08:30 IST
    3: {"hour": 12, "minute": 0},    # Thursday  12:00 IST
    5: {"hour": 10, "minute": 0},    # Saturday  10:00 IST (2x/month)
}
# No posts on Friday (5) and Sunday (6) — Sunday = weekly summary only
WEEKLY_SUMMARY_DAY      = 6   # Sunday
WEEKLY_SUMMARY_HOUR     = 9
WEEKLY_SUMMARY_MINUTE   = 0

# ── Engagement Reminder ────────────────────────────────────
ENGAGEMENT_REMINDER_MINUTES = 30   # WhatsApp ping after posting

# ── Content Pillars & Format Rotation ─────────────────────
# Format: {day_of_week: (pillar, format)}
CONTENT_ROTATION = {
    0: ("regulatory",    "news_insight"),       # Monday
    1: ("rca_fmea",      "did_you_know"),        # Tuesday
    2: ("lean_excellence","dmaic_case"),          # Wednesday
    3: ("any",           "poll"),                # Thursday
    5: ("pmo_genai",     "personal_story"),      # Saturday
}

PILLARS = {
    "regulatory":     "RBI Regulation, Fair Practice Code, NBFC Compliance, KYC, PPG Frameworks, RBI Inspection Readiness",
    "rca_fmea":       "Root Cause Analysis, FMEA, 5 Whys, Fishbone Analysis, Complaint Governance, Systemic Risk Elimination",
    "lean_excellence":"Lean Six Sigma, DMAIC, Kaizen, 5S, Business Excellence, Process Reengineering, TAT Reduction, Operational Efficiency",
    "pmo_genai":      "PMO Leadership, PRINCE2, SOP Governance, Change Management, GenAI in BFSI, Digital Transformation, Audit Readiness",
    "any":            "Any of the above pillars — pick the most trending/engaging topic of the day",
}

FORMATS = {
    "news_insight":   "News + Practitioner Insight (Hook → 3-4 bullets → Personal lens → Engagement question)",
    "did_you_know":   "Did You Know? Regulatory or Process fact (Hook → 3 bullets → Why it matters → Save this)",
    "dmaic_case":     "Lean/DMAIC Case Study (Problem → D-M-A-I-C breakdown → Quantified outcome → Lesson)",
    "poll":           "LinkedIn Poll (Question + 4 options + 1 line context)",
    "personal_story": "Personal Win/Story (Surprising result → What we did → Quantified outcome → Lesson → Offer to share)",
    "rca_tip":        "RCA/FMEA Practitioner Tip (Step-by-step approach → Real outcome → Reader question)",
}

# ── Hashtag Bank (rotated — never all at once) ─────────────
HASHTAG_BANK = {
    "regulatory":     ["#NBFCCompliance", "#RBIRegulation", "#FairPracticeCode", "#RegulatoryGovernance", "#IndianBanking", "#BFSI"],
    "rca_fmea":       ["#RootCauseAnalysis", "#FMEA", "#ComplaintGovernance", "#QualityManagement", "#RiskMitigation", "#ProcessControl"],
    "lean_excellence":["#LeanSixSigma", "#SixSigma", "#DMAIC", "#Kaizen", "#5S", "#OperationalExcellence", "#BusinessExcellence", "#ContinuousImprovement"],
    "pmo_genai":      ["#ProjectManagement", "#PMO", "#PRINCE2", "#ChangeManagement", "#GenAI", "#AIinBFSI", "#DigitalTransformation"],
    "always":         ["#BajajFinance", "#StrategicExecution", "#ProcessReengineering", "#TransformationLeadership"],
}

# ── Author Profile (Jayesh's resume — agent's permanent context) ──
AUTHOR_PROFILE = """
FULL NAME: Jayesh Taradutt Pandey
CURRENT ROLE: Deputy National Lead – Fair Practice Code (FPC) Unit, Bajaj Finance Limited
EXPERIENCE: 15+ years in Banking, NBFC, Operations, Compliance, and Transformation
LOCATION: Pune, India

CAREER HIGHLIGHTS:
- Transformed Bajaj Finance's Fair Practice Code governance from reactive to proactive Board-grade control
- Consolidated 65 Product Program Guidelines into 31 clusters with full PPG change governance
- Built India's first structured Root Cause Analysis (RCA) governance unit in BFSI sector
- Reduced EMI debit error complaints from 300+ to under 10 monthly using DMAIC and process redesign
- Reduced customer refunds by 85% (₹95L → ₹15L YTD) with 100% financial calculation accuracy
- Delivered zero critical audit observations across multiple Internal Audit and Compliance cycles
- Strategic Advisor to EVP – Operations & Service at Bajaj Finance (2023–2025)
- Served as SPOC for RBI Supervision — earned RBI appreciation for near-zero audit observations
- Executed President-flagship programs: Zero Hold, Paperless Sourcing (100% digital KYC), Service-to-Sale, GenAI adoption
- Led nationwide Business Continuity Planning during COVID — zero service downtime
- Expanded CRCR team from 3 to 16 members, embedded RCA culture across the organization
- Trained 1,500+ employees in Lean Six Sigma and change leadership
- Mentored 20+ Green Belt projects

PREVIOUS EXPERIENCE:
- HDFC Bank Limited (2012–2015): Project Manager – Process Transformation
- Intelenet Global Services (2009–2012): Quality Analyst

EDUCATION:
- Professional Certificate in Leadership with AI – E&ICT, IIT Kanpur (Pursuing)
- Certificate in General Management – IIM Lucknow (2020)
- MBA Finance – Institute of Technology and Management (2014)
- B.Com Finance – Mumbai University (2006)

CERTIFICATIONS:
- PRINCE2 Practitioner
- Lean Six Sigma Black Belt
- CMMI for Services & Development
- Generative AI for Project Management
- CMMI Auditor Certification
- Kaizen & 5S Implementation Certified

CORE EXPERTISE AREAS:
- RBI Regulation & NBFC Compliance
- Fair Practice Code & PPG Framework Governance
- Root Cause Analysis (RCA), FMEA, 5 Whys, Fishbone Analysis
- Lean Six Sigma (DMAIC, Kaizen, Blitz, 5S)
- Program & PMO Leadership (PRINCE2)
- SOP Lifecycle Governance
- Complaint Governance & Customer Fairness
- GenAI Adoption in BFSI
- Change Management & Operational Transformation
- Regulatory Inspection Readiness & Audit Coordination
- Business Continuity Planning
- KFS (Key Fact Statement) Compliance

SEO KEYWORDS TO WEAVE INTO POSTS:
Fair Practice Code, NBFC compliance, RBI regulation, PPG framework, root cause analysis,
FMEA, Lean Six Sigma, DMAIC, operational excellence, process reengineering, complaint governance,
KFS compliance, regulatory governance, audit readiness, change management, GenAI BFSI,
digital transformation banking, business excellence, Six Sigma Black Belt, PMO leadership

TONE RULES:
- Layman language — Class 10 readability
- Diplomatic — never criticise RBI, banks, or institutions negatively by name
- No personal opinion or political bias — facts + practitioner implications only
- Practitioner lens — speak as someone who lives these challenges daily
- Professional yet warm — never preachy or academic
- Always end with an engagement question to the audience
"""

# ── No-Repeat Memory ───────────────────────────────────────
MEMORY_LOOKBACK_POSTS   = 30   # Agent checks last 30 posts before picking topic
