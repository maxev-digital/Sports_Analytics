from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import hmac, hashlib, os, time

app = FastAPI(title="MaxEV Injury Webhook")

# set this in env: export WEBHOOK_SECRET="supersecret"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
MAX_SKEW_SEC = 120  # optional: prevent replay >2 min old

class InjuryAlert(BaseModel):
    strategy_id: str = Field(..., example="injury-cascade")
    league: Optional[str] = None
    team: Optional[str] = None
    player: Optional[str] = None
    change: Optional[str] = None
    sources: Optional[List[str]] = None
    title: Optional[str] = None
    link: Optional[str] = None
    published: Optional[str] = None
    entities_guess: Optional[List[str]] = None
    text: Optional[str] = None
    # dedupe keys from your scraper:
    source: str
    item_id: str
    ts_unix: int  # sender adds int(time.time()) for anti-replay

def verify_signature(raw_body: bytes, signature: str) -> bool:
    mac = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

@app.post("/webhooks/injury-alert")
async def injury_alert(
    request: Request,
    x_signature: str = Header(default=""),
):
    raw = await request.body()
    if not x_signature or not verify_signature(raw, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    alert = InjuryAlert.model_validate_json(raw)

    # optional anti-replay:
    if abs(int(time.time()) - alert.ts_unix) > MAX_SKEW_SEC:
        raise HTTPException(status_code=400, detail="stale webhook")

    # >>> YOUR PIPELINE HERE <<<
    # 1) write to DB / Kafka / Redis queue
    # 2) fan out to sockets / email / Discord
    # 3) enforce cooldown/idempotency using (source,item_id)

    # Example: print + 200
    print(f"[WEBHOOK] {alert.strategy_id} | {alert.team} | {alert.player} | {alert.change}")

    return {"status": "ok"}
