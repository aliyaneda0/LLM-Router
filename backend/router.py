from __future__ import annotations

import os
import time
from typing import Any
import site
import sys

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

import requests

from backend.config import get_settings
from backend.predict import predict_prompt


def choose_model(predicted_class: str, confidence: float) -> tuple[str, bool, str]:
    settings = get_settings()
    if confidence < settings.confidence_fallback_threshold:
        return (
            settings.strong_api_model,
            True,
            f"Confidence below threshold {settings.confidence_fallback_threshold}",
        )
    if predicted_class == "weak":
        return settings.local_weak_model, False, "Predicted weak prompt"
    if predicted_class == "moderate":
        return settings.local_moderate_model, False, "Predicted moderate prompt"
    return settings.strong_api_model, False, "Predicted strong prompt"


def call_ollama(prompt: str, model_name: str) -> tuple[str, float]:
    settings = get_settings()
    start = time.perf_counter()
    try:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("response", "")
    except requests.RequestException as exc:
        text = f"[local model unavailable: {exc}]"
    latency_ms = (time.perf_counter() - start) * 1000
    return text, latency_ms


def call_strong_api(prompt: str, model_name: str) -> tuple[str, float, float]:
    settings = get_settings()
    start = time.perf_counter()
    api_key = settings.openai_api_key
    if not api_key:
        latency_ms = (time.perf_counter() - start) * 1000
        return "[strong API not configured: set OPENAI_API_KEY]", latency_ms, 0.0

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model_name,
        "input": prompt,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("output", [{}])[0].get("content", [{}])[0].get("text", "")
        usage = payload.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        estimated_cost = estimate_cost(model_name, input_tokens, output_tokens)
    except requests.RequestException as exc:
        text = f"[strong API unavailable: {exc}]"
        estimated_cost = 0.0

    latency_ms = (time.perf_counter() - start) * 1000
    return text, latency_ms, estimated_cost


def estimate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    pricing: dict[str, tuple[float, float]] = {
        "gpt-4o-mini": (0.15 / 1_000_000, 0.60 / 1_000_000),
    }
    input_rate, output_rate = pricing.get(model_name, (0.0, 0.0))
    return round((input_tokens * input_rate) + (output_tokens * output_rate), 6)


def route_prompt(prompt: str) -> dict[str, Any]:
    settings = get_settings()
    prediction = predict_prompt(prompt)
    predicted_class = prediction["predicted_class"]
    confidence = prediction["confidence"]
    model_used, fallback_applied, route_reason = choose_model(predicted_class, confidence)

    if model_used in {settings.local_weak_model, settings.local_moderate_model}:
        response_text, latency_ms = call_ollama(prompt, model_used)
        estimated_cost = 0.0
    else:
        response_text, latency_ms, estimated_cost = call_strong_api(prompt, model_used)

    return {
        "predicted_class": predicted_class,
        "confidence": round(confidence, 4),
        "class_probabilities": prediction["class_probabilities"],
        "model_used": model_used,
        "fallback_applied": fallback_applied,
        "route_reason": route_reason,
        "latency_ms": round(latency_ms, 2),
        "estimated_cost": estimated_cost,
        "response": response_text,
    }
