import base64
import datetime
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import os

BASE_URL = "https://trading-api.kalshi.com"
KALSHI_API_KEY    = os.environ.get("KALSHI_API_KEY")
KALSHI_KEY_ID     = os.environ.get("KALSHI_KEY_ID")

def load_private_key(pem_string: str):
    pem_string = pem_string.replace("\\n", "\n")
    return serialization.load_pem_private_key(
        pem_string.encode("utf-8"),
        password=None,
        backend=default_backend()
    )

def sign_request(private_key, timestamp_ms: str, method: str, path: str) -> str:
    msg = timestamp_ms + method + path
    signature = private_key.sign(
        msg.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("utf-8")

def get_headers(method: str, path: str) -> dict:
    ts = str(int(datetime.datetime.now().timestamp() * 1000))
    private_key = load_private_key(KALSHI_API_KEY)
    sig = sign_request(private_key, ts, method, path)
    return {
        "KALSHI-ACCESS-KEY":       KALSHI_KEY_ID,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "Content-Type":            "application/json",
    }

def fetch_markets_for_show(show: str) -> list[dict]:
    from config import KALSHI_SEARCH_TERMS
    search_term = KALSHI_SEARCH_TERMS.get(show, show.lower())
    path = "/trade-api/v2/markets"
    try:
        resp = requests.get(
            BASE_URL + path,
            headers=get_headers("GET", path),
            params={"status": "open", "limit": 100},
            timeout=10,
        )
        resp.raise_for_status()
        markets = resp.json().get("markets", [])
        results = []
        for m in markets:
            if search_term in m.get("title", "").lower():
                results.append({
                    "id":          m["ticker"],
                    "title":       m.get("title", ""),
                    "kalshi_prob": m.get("yes_ask", 50),
                    "show":        show,
                })
        return results
    except Exception as e:
        print(f"  [Kalshi error for {show}]: {e}")
        return []

def fetch_all_award_markets() -> list[dict]:
    from config import KALSHI_SEARCH_TERMS, KALSHI_API_KEY as KEY
    if not KEY or KEY == "your-key-here":
        from opportunities import DEMO_MARKETS
        print("  No Kalshi key — using demo data")
        return DEMO_MARKETS
    all_markets = []
    for show in KALSHI_SEARCH_TERMS:
        markets = fetch_markets_for_show(show)
        all_markets.extend(markets)
    return all_markets
