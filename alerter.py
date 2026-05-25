# ============================================================
#  alerter.py — sends SMS alerts via Twilio when edges found
# ============================================================

import json
import os
import requests
from datetime import datetime
from config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER
)

SENT_LOG = "sent_alerts.json"


def load_sent_alerts() -> dict:
    """Load log of already-sent alerts to avoid duplicates."""
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG) as f:
            return json.load(f)
    return {}


def save_sent_alert(nominee: str, edge: float):
    """Record that we sent an alert for this nominee+edge."""
    log = load_sent_alerts()
    log[nominee] = {"edge": edge, "sent_at": datetime.utcnow().isoformat()}
    with open(SENT_LOG, "w") as f:
        json.dump(log, f, indent=2)


def already_alerted(nominee: str, current_edge: float) -> bool:
    """
    Return True if we already sent an alert for this nominee
    at a similar edge (within 3%). Prevents spam.
    """
    log = load_sent_alerts()
    if nominee not in log:
        return False
    prev_edge = log[nominee]["edge"]
    # Re-alert if edge has grown by more than 5% since last alert
    return abs(current_edge - prev_edge) < 5.0


def format_sms(edges: list[dict]) -> str:
    """Format edge list into a concise SMS message."""
    lines = ["🎬 Awards Scanner — Edge Alert\n"]
    for e in edges[:3]:   # max 3 per SMS to keep it readable
        sign = "+" if e["edge"] >= 0 else ""
        lines.append(
            f"★ {e['show']} | {e['category']}\n"
            f"  {e['nominee']}\n"
            f"  Model: {e['model_prob']}%  Kalshi: {e['kalshi_prob']}¢\n"
            f"  Edge: {sign}{e['edge']}% ({e['confidence']} conf)\n"
        )
    if len(edges) > 3:
        lines.append(f"...and {len(edges) - 3} more. Check your dashboard.")
    return "\n".join(lines)


def send_sms(message: str) -> bool:
    """Send an SMS via Twilio. Returns True if successful."""
    if TWILIO_ACCOUNT_SID == "your-twilio-sid-here":
        print("  [SMS] Twilio not configured — printing alert instead:")
        print("  " + message.replace("\n", "\n  "))
        return False

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        resp = requests.post(url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data={
                "From": TWILIO_FROM_NUMBER,
                "To":   TWILIO_TO_NUMBER,
                "Body": message,
            },
            timeout=15,
        )
        resp.raise_for_status()
        print(f"  ✓ SMS sent to {TWILIO_TO_NUMBER}")
        return True
    except Exception as e:
        print(f"  [SMS error]: {e}")
        return False


def alert_on_edges(edges: list[dict]):
    """
    Check edges, filter out already-alerted ones, send SMS for new ones.
    """
    new_edges = [e for e in edges if not already_alerted(e["nominee"], e["edge"])]

    if not new_edges:
        print("  No new edges to alert on.")
        return

    print(f"  Sending SMS alert for {len(new_edges)} new edge(s)...")
    message = format_sms(new_edges)
    success = send_sms(message)

    if success:
        for e in new_edges:
            save_sent_alert(e["nominee"], e["edge"])
