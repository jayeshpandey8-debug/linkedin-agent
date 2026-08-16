"""
config.py - Full configuration for Jayesh Pandey LinkedIn Agent
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ── API Keys ───────────────────────────────────────────────
ANTHROPIC_API_KEY      = os.getenv("ANTHROPIC_API_KEY", "")
# Centralised here so a future model deprecation is a one-line env var change
# instead of a repo-wide sed (this broke production once already).
ANTHROPIC_MODEL        = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
NEWS_API_KEY           = os.getenv("NEWS_API_KEY", "")
PEXELS_API_KEY         = os.getenv("PEXELS_API_KEY", "")
INCLUDE_IMAGE          = os.getenv("INCLUDE_IMAGE", "true").lower() == "true"

# ── LinkedIn OAuth ─────────────────────────────────────────
LINKEDIN_CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN  = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN    = os.getenv("LINKEDIN_PERSON_URN", "")

# ── Twilio WhatsApp ────────────────────────────────────────
TWILIO_ACCOUNT_SID     = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM   = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_WHATSAPP_TO     = os.getenv("TWILIO_WHATSAPP_TO", "whatsapp:+919004141203")

# ── Dashboard ──────────────────────────────────────────────
DASHBOARD_PORT         = int(os.getenv("DASHBOARD_PORT", "5000"))
DASHBOARD_SECRET       = os.getenv("DASHBOARD_SECRET", "jayesh_agent_secret_2025")
AUTO_POST              = False

# ── Posting Schedule (IST, day: hour/minute) ───────────────
# REBUILT FRESH — Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
import pytz
IST = pytz.timezone("Asia/Kolkata")

POSTING_SCHEDULE = {
    0: {"hour": 8,  "minute": 30},   # Monday    08:30 IST — RBI Circulars
    1: {"hour": 12, "minute": 0},    # Tuesday   12:00 IST — AI / GenAI
    2: {"hour": 8,  "minute": 30},   # Wednesday 08:30 IST — Change Management
    3: {"hour": 12, "minute": 0},    # Thursday  12:00 IST — PMP / Project Mgmt
    5: {"hour": 10, "minute": 0},    # Saturday  10:00 IST — AI / GenAI (personal story)
}
WEEKLY_SUMMARY_DAY    = 6
WEEKLY_SUMMARY_HOUR   = 9
WEEKLY_SUMMARY_MINUTE = 0
ENGAGEMENT_REMINDER_MINUTES = 30

# ── Content Rotation ───────────────────────────────────────
# REBUILT: focused on 4 pillars — RBI Circulars, AI/GenAI, PMP, Change Management.
# RCA/FMEA + Lean Six Sigma are folded into "change_management" (they're the tools
# of change management, not a separate topic). Industry trends / personal
# excellence pillars removed — still reachable anytime via WhatsApp "TOPIC ...".
CONTENT_ROTATION = {
    0: ("regulatory",        "news_insight"),
    1: ("ai_genai",          "did_you_know"),
    2: ("change_management", "dmaic_case"),
    3: ("pmp",               "poll"),
    5: ("ai_genai",          "personal_story"),
}

# ── Topic Pillars ────────────────────────────────────────────
PILLARS = {
    # Anchored to actual RBI publications/circulars and India Government
    # BFSI policy + execution, not generic banking news
    "regulatory": (
        "RBI Master Directions, RBI Circulars, RBI Press Releases, RBI Notifications, "
        "Fair Practice Code, NBFC Compliance, KYC, PPG Frameworks, "
        "RBI Inspection Readiness, NBFC SBR Framework, KFS, RBI Ombudsman Scheme, "
        "Ministry of Finance BFSI Policy, India Government Financial Sector Reforms, "
        "Budget Announcements for BFSI, Policy Execution and Implementation Timelines, "
        "SEBI, IRDAI, NHB Regulations, Financial Inclusion Policy, Priority Sector Lending Targets"
    ),
    # World AI/GenAI developments — separated out from PMP so AI gets its own voice
    "ai_genai": (
        "World AI Developments, Generative AI Trends Worldwide, Global AI Regulation, "
        "AI Pros and Cons, AI Job Displacement Debate, AI Safety and Ethics, "
        "Frontier AI Models, AI Adoption Risks and Benefits, GenAI in BFSI, "
        "AI Agents, AI in Financial Services, Responsible AI, AI Governance"
    ),
    # PMI/PMP project management practice — separated out from AI
    "pmp": (
        "PMI Project Management Practices, PMP Methodology, PMBOK Guide, "
        "PRINCE2, Program Governance, Stakeholder Management, Risk Register, "
        "Agile vs Waterfall, Earned Value Management, Project Charter, "
        "Project Governance, Program Management Office, Portfolio Management"
    ),
    # Change Management — now the home for RCA/FMEA + Lean Six Sigma, since
    # those are the practitioner tools used to actually execute change
    "change_management": (
        "Change Management, SOP Governance, Business Continuity, Process Reengineering, "
        "Root Cause Analysis, FMEA, 5 Whys, Fishbone Analysis, Complaint Governance, "
        "Lean Six Sigma, DMAIC, Kaizen, 5S, TAT Reduction, Operational Efficiency, "
        "Value Stream Mapping, Waste Elimination, Cost of Quality, CAPA, "
        "Organisational Change, Adoption and Resistance to Change"
    ),
    "any": (
        "Any of the above pillars — pick the most trending topic today"
    ),
}

# ── Expanded News Queries ──────────────────────────────────
NEWS_QUERIES = {
    # SHARPENED: targets actual RBI circulars/publications + Govt BFSI policy execution
    "regulatory": [
        "RBI master direction circular",
        "RBI notification NBFC",
        "RBI press release banking",
        "Ministry of Finance BFSI policy India",
        "India government financial sector reform",
        "RBI policy implementation NBFC",
    ],
    # AI/GenAI — world developments, kept distinct from PMP
    "ai_genai": [
        "artificial intelligence pros cons",
        "AI regulation world global",
        "AI risks benefits debate 2026",
        "generative AI adoption enterprise",
        "AI agents enterprise 2026",
        "responsible AI governance",
    ],
    # PMI/PMP practice — kept distinct from AI
    "pmp": [
        "PMI project management methodology",
        "PMP project management practice",
        "PMBOK agile waterfall project",
        "program governance stakeholder management",
    ],
    # Change Management — now covers RCA/FMEA + Lean Six Sigma + change execution
    "change_management": [
        "change management India",
        "Lean Six Sigma India",
        "operational excellence India",
        "process improvement BFSI India",
        "quality management banking India",
        "root cause analysis banking",
    ],
    "any": [
        "RBI India banking",
        "NBFC India news",
        "indian banking finance",
    ],
}

# ── Hashtag Bank ─────────────────────────────────────────────
HASHTAG_BANK = {
    "regulatory":         ["#NBFCCompliance","#RBIRegulation","#FairPracticeCode","#RegulatoryGovernance","#IndianBanking","#BFSI","#KYC","#RBICircular"],
    "ai_genai":           ["#ArtificialIntelligence","#GenAI","#AIRegulation","#FutureOfWork","#ResponsibleAI","#AIGovernance"],
    "pmp":                ["#PMI","#PMP","#ProjectManagement","#PMO","#PRINCE2","#AgileVsWaterfall"],
    "change_management":  ["#ChangeManagement","#RootCauseAnalysis","#FMEA","#LeanSixSigma","#DMAIC","#Kaizen","#OperationalExcellence","#ProcessReengineering"],
    "always":             ["#BajajFinance","#StrategicExecution","#TransformationLeadership","#IndianFinance"],
}

# ── Post Formats ───────────────────────────────────────────
FORMATS = {
    "news_insight":    "News + Practitioner Insight",
    "did_you_know":    "Did You Know? Regulatory or Process fact",
    "dmaic_case":      "Lean/DMAIC Case Study",
    "poll":            "LinkedIn Poll",
    "personal_story":  "Personal Win/Story",
    "rca_tip":         "RCA/FMEA Practitioner Tip",
}

# ── Practitioner Context (trimmed) ─────────────────────────
# Used to ground first-person "subtle aside" voice in post_generator.py.
# Deliberately excludes specific stats/numbers so posts don't read as a
# resume dump — role + domain only, so opinions sound authentic without bragging.
PRACTITIONER_CONTEXT = (
    "The author leads Fair Practice Code and regulatory governance for an NBFC "
    "in India, with 15+ years across banking operations, compliance, and process "
    "transformation. Background includes RCA/root-cause governance, Lean Six Sigma, "
    "PMO/project delivery, and hands-on GenAI adoption work. Writes as a working "
    "practitioner in this space, not an outside commentator."
)

# ── Author Profile (full — reserved for personal_story format only) ────────
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
- Executed President-flagship programs: Zero Hold, Paperless Sourcing, Service-to-Sale, GenAI adoption
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

CORE EXPERTISE:
- RBI Regulation & NBFC Compliance
- Fair Practice Code & PPG Framework Governance
- Root Cause Analysis (RCA), FMEA, 5 Whys, Fishbone Analysis
- Lean Six Sigma (DMAIC, Kaizen, Blitz, 5S)
- Program & PMO Leadership (PRINCE2, PMI/PMP practices)
- SOP Lifecycle Governance
- Complaint Governance & Customer Fairness
- GenAI Adoption in BFSI and World AI Trends
- Change Management & Operational Transformation
- Regulatory Inspection Readiness & Audit Coordination
- Business Continuity Planning

SEO KEYWORDS:
Fair Practice Code, NBFC compliance, RBI regulation, RBI circular, RBI master direction,
PPG framework, root cause analysis, FMEA, Lean Six Sigma, DMAIC, operational excellence,
process reengineering, complaint governance, KFS compliance, regulatory governance,
audit readiness, change management, GenAI, PMI, PMP, PMBOK, project management,
business excellence, Six Sigma Black Belt, PMO leadership, RCA governance, Kaizen, 5S,
NPA management, credit risk, KYC compliance, digital transformation banking, AI regulation,
artificial intelligence pros and cons, India government BFSI policy

TONE RULES:
- Layman language — Class 10 readability
- Diplomatic — never criticise RBI, banks, government, or institutions negatively
- No personal opinion or political bias — facts + practitioner implications only
- For AI pros/cons content — present a balanced view (benefits AND risks/limitations), never one-sided
- Practitioner lens — speak as someone who lives these challenges daily
- Professional yet warm — never preachy or academic
- Always end with engagement question
"""

# ── Memory Settings ────────────────────────────────────────
MEMORY_LOOKBACK_POSTS = 30
