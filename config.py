"""
config.py - Full configuration for Jayesh Pandey LinkedIn Agent
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ── API Keys ───────────────────────────────────────────────
ANTHROPIC_API_KEY      = os.getenv("ANTHROPIC_API_KEY", "")
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

# ── Posting Schedule (IST, day: hour/minute) ──────────────
import pytz
IST = pytz.timezone("Asia/Kolkata")

POSTING_SCHEDULE = {
    0: {"hour": 8,  "minute": 30},   # Monday
    1: {"hour": 12, "minute": 0},    # Tuesday
    2: {"hour": 8,  "minute": 30},   # Wednesday
    3: {"hour": 12, "minute": 0},    # Thursday
    5: {"hour": 10, "minute": 0},    # Saturday
}
WEEKLY_SUMMARY_DAY    = 6
WEEKLY_SUMMARY_HOUR   = 9
WEEKLY_SUMMARY_MINUTE = 0
ENGAGEMENT_REMINDER_MINUTES = 30

# ── Content Rotation ───────────────────────────────────────
CONTENT_ROTATION = {
    0: ("regulatory",     "news_insight"),
    1: ("rca_fmea",       "did_you_know"),
    2: ("lean_excellence","dmaic_case"),
    3: ("any",            "poll"),
    5: ("pmo_genai",      "personal_story"),
}

# ── EXPANDED Topic Pillars ─────────────────────────────────
PILLARS = {
    "regulatory": (
        "RBI Regulation, Fair Practice Code, NBFC Compliance, KYC, PPG Frameworks, "
        "RBI Inspection Readiness, Master Directions, NBFC SBR, KFS, Ombudsman, "
        "RBI Circular, Banking Regulation, Credit Policy, Monetary Policy, "
        "SEBI, IRDAI, NHB, Financial Inclusion, Priority Sector Lending"
    ),
    "rca_fmea": (
        "Root Cause Analysis, FMEA, 5 Whys, Fishbone Analysis, "
        "Complaint Governance, Systemic Risk Elimination, Pareto Analysis, "
        "Control Charts, Process Failure Modes, Defect Prevention, "
        "Quality Circles, Error Proofing, Poka Yoke, CAPA, "
        "Customer Complaint Resolution, NPS, Service Recovery"
    ),
    "lean_excellence": (
        "Lean Six Sigma, DMAIC, Kaizen, 5S, Business Excellence, "
        "Process Reengineering, TAT Reduction, Operational Efficiency, "
        "Value Stream Mapping, Blitz Events, Waste Elimination, "
        "Throughput, Cycle Time, First Time Right, Cost of Quality, "
        "Benchmarking, Balanced Scorecard, OKRs, KPIs, SLA Management"
    ),
    "pmo_genai": (
        "PMO Leadership, PRINCE2, SOP Governance, Change Management, "
        "GenAI in BFSI, Digital Transformation, Audit Readiness, "
        "AI Adoption Banking, Automation, Paperless Operations, "
        "Program Governance, Stakeholder Management, Board Reporting, "
        "Business Continuity, Risk Framework, CMMI, Agile, Waterfall"
    ),
    "personal_excellence": (
        "Leadership, Executive Presence, Strategic Thinking, "
        "Career Growth, Professional Development, Mentoring, "
        "Team Building, Emotional Intelligence, Communication, "
        "Work Life Balance, Productivity, Time Management, "
        "IIT Kanpur AI Program, MBA Finance, Certifications"
    ),
    "industry_trends": (
        "Indian Economy, BFSI Outlook, Credit Growth, NPA Trends, "
        "Banking Sector Performance, NBFC Industry News, "
        "Fintech Disruption, Open Banking, UPI, Digital Rupee, "
        "Financial Inclusion India, Microfinance, Gold Loan, "
        "Green Finance, ESG Banking, Sustainable Finance India"
    ),
    "any": (
        "Any of the above pillars — pick the most trending topic today"
    ),
}

# ── Expanded News Queries ──────────────────────────────────
NEWS_QUERIES = {
    "regulatory": [
        "RBI India banking regulation",
        "NBFC compliance India",
        "RBI circular directive India",
        "fair practice code India banking",
        "RBI monetary policy India",
        "banking regulation SEBI India",
    ],
    "rca_fmea": [
        "quality management banking India",
        "operational risk BFSI India",
        "customer complaint banking India",
        "process quality improvement India",
    ],
    "lean_excellence": [
        "Lean Six Sigma India",
        "operational excellence India",
        "process improvement BFSI India",
        "business excellence India",
    ],
    "pmo_genai": [
        "AI banking India 2025",
        "digital transformation India BFSI",
        "fintech India innovation",
        "automation banking India",
    ],
    "personal_excellence": [
        "leadership banking India",
        "professional development finance India",
        "career banking NBFC India",
    ],
    "industry_trends": [
        "Indian banking sector news",
        "NBFC industry India",
        "credit growth India banking",
        "fintech India news",
        "UPI digital payments India",
    ],
    "any": [
        "RBI India banking",
        "NBFC India news",
        "indian banking finance",
    ],
}

# ── Expanded Hashtag Bank ──────────────────────────────────
HASHTAG_BANK = {
    "regulatory":         ["#NBFCCompliance","#RBIRegulation","#FairPracticeCode","#RegulatoryGovernance","#IndianBanking","#BFSI","#KYC","#RBICircular"],
    "rca_fmea":           ["#RootCauseAnalysis","#FMEA","#ComplaintGovernance","#QualityManagement","#RiskMitigation","#ProcessControl","#5Whys","#ServiceExcellence"],
    "lean_excellence":    ["#LeanSixSigma","#SixSigma","#DMAIC","#Kaizen","#5S","#OperationalExcellence","#BusinessExcellence","#ContinuousImprovement","#ProcessReengineering"],
    "pmo_genai":          ["#ProjectManagement","#PMO","#PRINCE2","#ChangeManagement","#GenAI","#AIinBFSI","#DigitalTransformation","#Automation","#FutureOfFinance"],
    "personal_excellence":["#Leadership","#CareerGrowth","#ProfessionalDevelopment","#ExecutivePresence","#Mentoring","#GrowthMindset"],
    "industry_trends":    ["#IndianBanking","#BFSI","#Fintech","#CreditGrowth","#DigitalIndia","#FinancialInclusion","#UPI","#NBFC"],
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

# ── Author Profile ─────────────────────────────────────────
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
- Program & PMO Leadership (PRINCE2)
- SOP Lifecycle Governance
- Complaint Governance & Customer Fairness
- GenAI Adoption in BFSI
- Change Management & Operational Transformation
- Regulatory Inspection Readiness & Audit Coordination
- Business Continuity Planning

SEO KEYWORDS:
Fair Practice Code, NBFC compliance, RBI regulation, PPG framework, root cause analysis,
FMEA, Lean Six Sigma, DMAIC, operational excellence, process reengineering, complaint governance,
KFS compliance, regulatory governance, audit readiness, change management, GenAI BFSI,
business excellence, Six Sigma Black Belt, PMO leadership, RCA governance, Kaizen, 5S,
NPA management, credit risk, KYC compliance, digital transformation banking

TONE RULES:
- Layman language — Class 10 readability
- Diplomatic — never criticise RBI, banks, or institutions negatively
- No personal opinion or political bias — facts + practitioner implications only
- Practitioner lens — speak as someone who lives these challenges daily
- Professional yet warm — never preachy or academic
- Always end with engagement question
"""

# ── Memory Settings ────────────────────────────────────────
MEMORY_LOOKBACK_POSTS = 30
