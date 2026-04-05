# LLM Router MVP

## Application Summary
- Purpose: classify incoming prompts as `weak`, `moderate`, or `strong` and send them to the lowest-cost model that should still answer well.
- User flow: client sends a prompt to FastAPI `/route`, the classifier scores complexity, the router picks a model, the model response is returned, and the event is logged to SQLite.
- Local models: Ollama-hosted `LOCAL_WEAK_MODEL` and `LOCAL_MODERATE_MODEL`.
- Strong model: configurable cloud/API model via `STRONG_API_PROVIDER` and `STRONG_API_MODEL` (`openai` or `gemini`).
- Safety rule: if prediction confidence is below `0.55`, the system falls back to the strong model.

## Core Features
- Cost-aware routing instead of always calling the most expensive model.
- Confidence-based fallback to reduce bad low-tier routing decisions.
- Config-driven providers and model names through `.env`.
- Persistent logging of prompt, class, confidence, model, fallback flag, route reason, latency, cost, response, and timestamp.
- Streamlit dashboard for route counts, fallback counts, latency, cost, and recent logs.
- Offline training and saved evaluation artifacts for demos and model discussions.

## Architecture Choice
- Frontend: Streamlit dashboard for fast MVP analytics and demoability.
- API layer: FastAPI exposes `/health`, `/route`, and `/analytics/summary`.
- ML layer: TF-IDF + calibrated Logistic Regression in a scikit-learn pipeline.
- Routing layer: deterministic policy maps class + confidence to model choice.
- Storage: SQLite is enough for MVP simplicity and observability.
- Config: environment variables keep provider switching and deployment simple.

## Why These Choices Make Sense
- TF-IDF + Logistic Regression is lightweight, fast, interpretable, and strong for short-text classification.
- Calibration matters because routing decisions depend on confidence, not only predicted label.
- FastAPI keeps inference endpoints clean and production-friendly.
- SQLite reduces setup friction while still giving persistent analytics.
- Streamlit speeds up stakeholder demos without building a full custom frontend.

## Evidence From Current Build
- Training combines every `prompts*.csv` file, cleans rows, and removes duplicates.
- Current saved evaluation accuracy: `96.64%`.
- Confusion matrix shows only a small number of class mix-ups across `weak`, `moderate`, and `strong`.

## Interview Questions
1. Why did you choose a classifier before generation instead of routing with hand-written rules only?
2. Why use TF-IDF + Logistic Regression over embeddings or an LLM judge for the MVP?
3. Why did you calibrate the classifier, and how does calibration improve routing quality?
4. Why is the fallback threshold `0.55`, and how would you tune it in production?
5. How do you balance latency, quality, and cost across weak, moderate, and strong models?
6. Why use Ollama for local models and OpenAI/Gemini for the strong tier?
7. What happens when a local model or API provider is unavailable?
8. Why store logs in SQLite first, and when would you move to Postgres?
9. How would you detect misroutes and use the logged data for retraining?
10. How would you expand the router to support more classes, tenants, or providers?
11. What are the main risks of this architecture, and how would you mitigate them?
12. If traffic grows, which layer would you scale or redesign first?
