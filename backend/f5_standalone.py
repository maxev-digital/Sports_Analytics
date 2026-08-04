"""
F5 Edge Engine — Standalone Server

Serves the live F5 dashboard API on port 8888.
Run: ODDS_API_KEY=your_key python3 f5_standalone.py
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set API key from env or default (never commit real keys)
os.environ.setdefault("ODDS_API_KEY", os.getenv("ODDS_API_KEY", ""))

from routes.f5_live import router as f5_live_router
from routes.f5_fade_tie import router as f5_calc_router
from routes.verification import router as verification_router

app = FastAPI(title="F5 Edge Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(f5_live_router)
app.include_router(f5_calc_router)
app.include_router(verification_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "module": "f5-edge-engine"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
