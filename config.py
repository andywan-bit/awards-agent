# ============================================================
#  config.py — keys are loaded from environment variables
#  so they never appear in your code or GitHub
# ============================================================

import os

# ── Anthropic (Claude) ───────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your-anthropic-key-here")

# ── NewsAPI ──────────────────────────────────────────────────
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your-newsapi-key-here")

# ── Twilio (SMS alerts) ──────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "your-twilio-sid-here")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN",  "your-twilio-token-here")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "+1XXXXXXXXXX")
TWILIO_TO_NUMBER   = os.environ.get("TWILIO_TO_NUMBER",   "+1XXXXXXXXXX")

# ── Kalshi ───────────────────────────────────────────────────
KALSHI_API_KEY = os.environ.get("KALSHI_API_KEY", None)

# ── GitHub (auto-updates data) ───────────────────────────────
GITHUB_TOKEN     = os.environ.get("GITHUB_TOKEN",     "your-github-token-here")
GITHUB_REPO      = os.environ.get("GITHUB_REPO",      "andywan-bit/awards-repository")
GITHUB_FILE_PATH = os.environ.get("GITHUB_FILE_PATH", "opportunities.py")

# ── Agent settings ───────────────────────────────────────────
CHECK_INTERVAL_MINUTES = 60
EDGE_ALERT_THRESHOLD   = 10
MIN_CONFIDENCE         = "medium"
