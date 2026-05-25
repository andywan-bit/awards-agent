# ============================================================
#  agent.py — main agent loop
#
#  Usage:
#    python agent.py          # run once
#    python agent.py --watch  # run every hour continuously
# ============================================================

import sys
import time
import json
import os
from datetime import datetime

from news_scout   import fetch_all_shows
from ai_parser    import parse_all_shows
from data_updater import apply_winners
from edge_detector import find_edges
from alerter      import alert_on_edges
from config       import CHECK_INTERVAL_MINUTES

# Inline precursor data (kept in sync with opportunities.py via GitHub)
PRECURSOR_DATA = {
    "The Brutalist":               {"show": "Oscars",        "category": "Best Picture",           "sag_win": False, "bafta_win": True,  "critics_choice": True,  "guild_noms": 3, "rt_score": 89,   "social_volume": 0.72},
    "Adrien Brody":                {"show": "Oscars",        "category": "Best Actor",              "sag_win": True,  "bafta_win": True,  "critics_choice": True,  "guild_noms": 0, "rt_score": None, "social_volume": 0.65},
    "Brady Corbet":                {"show": "Oscars",        "category": "Best Director",           "sag_win": None,  "bafta_win": False, "critics_choice": False, "guild_noms": 2, "rt_score": 89,   "social_volume": 0.55},
    "Demi Moore":                  {"show": "Oscars",        "category": "Best Actress",            "sag_win": True,  "bafta_win": False, "critics_choice": True,  "guild_noms": 0, "rt_score": None, "social_volume": 0.48},
    "Emilia Pérez":                {"show": "Oscars",        "category": "Best Intl. Film",         "sag_win": None,  "bafta_win": True,  "critics_choice": True,  "guild_noms": 1, "rt_score": 79,   "social_volume": 0.60},
    "The Day of the Jackal":       {"show": "Emmys",         "category": "Best Drama Series",       "sag_win": False, "bafta_win": None,  "critics_choice": False, "guild_noms": 2, "rt_score": 93,   "social_volume": 0.58},
    "The Bear":                    {"show": "Emmys",         "category": "Best Comedy Series",      "sag_win": True,  "bafta_win": None,  "critics_choice": True,  "guild_noms": 3, "rt_score": 98,   "social_volume": 0.80},
    "Disclaimer":                  {"show": "Emmys",         "category": "Best Limited Series",     "sag_win": False, "bafta_win": None,  "critics_choice": False, "guild_noms": 2, "rt_score": 94,   "social_volume": 0.52},
    "Beyoncé – Cowboy Carter":     {"show": "Grammys",       "category": "Album of the Year",       "sag_win": None,  "bafta_win": None,  "critics_choice": None,  "guild_noms": 0, "rt_score": None, "social_volume": 0.88, "metascore": 90},
    "Kendrick Lamar – Not Like Us":{"show": "Grammys",       "category": "Record of the Year",      "sag_win": None,  "bafta_win": None,  "critics_choice": None,  "guild_noms": 0, "rt_score": None, "social_volume": 0.95},
    "Conclave":                    {"show": "Golden Globes", "category": "Best Picture – Drama",    "sag_win": False, "bafta_win": False, "critics_choice": True,  "guild_noms": 2, "rt_score": 92,   "social_volume": 0.62},
    "Shōgun":                      {"show": "Golden Globes", "category": "Best TV Series – Drama",  "sag_win": True,  "bafta_win": None,  "critics_choice": True,  "guild_noms": 3, "rt_score": 99,   "social_volume": 0.75},
}

STATE_FILE = "agent_state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "runs_completed": 0, "winners_found": 0, "alerts_sent": 0}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_cycle(state: dict) -> dict:
    """Run one full agent cycle."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'═' * 60}")
    print(f"  AGENT CYCLE — {now}")
    print(f"{'═' * 60}")

    # Step 1: Fetch news
    print("\n[1/4] Scouting for awards news...")
    news = fetch_all_shows()

    # Step 2: Parse with Claude
    print("\n[2/4] Parsing articles with Claude AI...")
    winners = parse_all_shows(news)
    print(f"  Total winners extracted: {len(winners)}")

    # Step 3: Update data on GitHub
    print("\n[3/4] Updating data...")
    if winners:
        updated = apply_winners(winners)
        if updated:
            state["winners_found"] = state.get("winners_found", 0) + len(winners)
            print(f"  ✓ GitHub updated with {len(winners)} winner(s)")
    else:
        print("  No new winners found in news.")

    # Step 4: Find edges and alert
    print("\n[4/4] Scanning for Kalshi edges...")
    edges = find_edges(PRECURSOR_DATA)

    if edges:
        print(f"  Found {len(edges)} edge(s) above threshold:")
        for e in edges:
            print(f"    ★ {e['nominee']} — +{e['edge']}% edge ({e['confidence']} conf)")
        alert_on_edges(edges)
        state["alerts_sent"] = state.get("alerts_sent", 0) + 1
    else:
        print("  No edges above threshold found.")

    state["last_run"]        = now
    state["runs_completed"]  = state.get("runs_completed", 0) + 1
    print(f"\n  Cycle complete. Total runs: {state['runs_completed']}\n")
    return state


def run_once():
    state = load_state()
    state = run_cycle(state)
    save_state(state)


def run_watch():
    print(f"\n  Agent starting — checking every {CHECK_INTERVAL_MINUTES} minutes.")
    print("  Press Ctrl+C to stop.\n")
    try:
        while True:
            state = load_state()
            state = run_cycle(state)
            save_state(state)
            print(f"  Sleeping {CHECK_INTERVAL_MINUTES} minutes...\n")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        print("\n  Agent stopped.\n")


if __name__ == "__main__":
    if "--watch" in sys.argv:
        run_watch()
    else:
        run_once()
