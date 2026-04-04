from __future__ import annotations

import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.db import fetch_summary, init_db, insert_route_log
from backend.router import route_prompt


app = FastAPI(title="LLM Router MVP", version="0.1.0")


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt to classify and route.")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/route")
def route(request: RouteRequest) -> dict[str, object]:
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt must not be empty.")

    result = route_prompt(prompt)
    insert_route_log(
        {
            "prompt": prompt,
            "predicted_class": result["predicted_class"],
            "confidence": result["confidence"],
            "model_used": result["model_used"],
            "fallback_applied": result["fallback_applied"],
            "route_reason": result["route_reason"],
            "latency_ms": result["latency_ms"],
            "estimated_cost": result["estimated_cost"],
            "response": result["response"],
        }
    )
    return result


@app.get("/analytics/summary")
def analytics_summary() -> dict[str, object]:
    return fetch_summary()
