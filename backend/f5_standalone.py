"""
Standalone F5 Fade the Tie server for local testing.
Run: python3 f5_standalone.py
Serves F5 endpoints on port 8888 so the frontend can connect.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes.f5_fade_tie import router as f5_router
from routes.f5_viability import router as f5_viability_router
from routes.f5_logic_explained import router as f5_explain_router
from routes.f5_complete_strategy import router as f5_strategy_router
from routes.f5_two_of_three import router as f5_two_of_three_router
from routes.f5_sizing_deep_dive import router as f5_sizing_router

app = FastAPI(title="F5 Fade the Tie — Standalone")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(f5_router)
app.include_router(f5_viability_router)
app.include_router(f5_explain_router)
app.include_router(f5_strategy_router)
app.include_router(f5_two_of_three_router)
app.include_router(f5_sizing_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "module": "f5-fade-tie-standalone"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
