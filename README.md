# LLM Router MVP

This project is a locally runnable LLM routing prototype that classifies prompts as `weak`, `moderate`, or `strong`, then routes them to local or API models based on predicted complexity and confidence.

## Project Structure

```text
llm-router/
  data/
    prompts.csv
    app.db
  models/
    classifier.pkl
  backend/
    train.py
    predict.py
    router.py
    api.py
    db.py
  frontend/
    dashboard.py
  requirements.txt
```

## Week 2 Improvements

- Configurable local and API models through environment variables.
- Confidence-calibrated classifier for safer fallback behavior.
- SQLite logs now store whether fallback happened and why.
- Evaluation script writes reusable metrics to `models/evaluation.json`.
- Analytics summary endpoint for dashboards and demos.

## How It Works

1. We manually label prompts as `weak`, `moderate`, or `strong`.
2. We train a TF-IDF + calibrated Logistic Regression classifier.
3. The classifier predicts prompt difficulty.
4. The router maps the predicted class to a model:
   - `weak` -> local weak model
   - `moderate` -> local moderate model
   - `strong` -> API strong model
5. If confidence is below `0.55`, we escalate to the strong API model.
6. The API stores route outcomes in SQLite, including fallback decisions.
7. The dashboard displays route counts, fallback counts, latency, and cost.

## Run

Create and use the project virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Configure your models:

```powershell
copy .env.example .env
```

Then edit `.env` and put your real values there. The app loads `.env` automatically.

Train:

```powershell
.\.venv\Scripts\python.exe backend\train.py
.\.venv\Scripts\python.exe backend\evaluate.py
```

Start API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload
```

Start dashboard:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend\dashboard.py
```

## Model Integrations

- Local model calls go to Ollama at `OLLAMA_BASE_URL`.
- Set your local model names with `LOCAL_WEAK_MODEL` and `LOCAL_MODERATE_MODEL`.
- Set your cloud/API model with `STRONG_API_MODEL`.
- Set `OPENAI_API_KEY` before using the strong API model.

## Database

The SQLite database is created automatically at `data/app.db`.

It stores:
- The original prompt
- Predicted class
- Confidence
- Chosen model
- Whether fallback was applied
- Why the route was chosen
- Latency
- Estimated cost
- Model response
- Timestamp

Use it for:
- Demo screenshots
- Dashboard analytics
- Interview discussion about observability
- Later retraining and error analysis

## Key Modules

- `backend/train.py`: trains and saves the classifier.
- `backend/evaluate.py`: measures classifier quality and writes reusable metrics.
- `backend/predict.py`: loads the saved classifier and returns prediction probabilities.
- `backend/router.py`: chooses the model and calls Ollama or the API provider.
- `backend/db.py`: creates the SQLite schema and stores routing logs.
- `backend/api.py`: exposes `/route`, `/health`, and `/analytics/summary`.
- `frontend/dashboard.py`: displays logs and high-level metrics in Streamlit.

## Deployment

Yes, this project can be deployed.

Typical paths:
- Local demo: run FastAPI and Streamlit on your laptop with Ollama installed.
- VM deployment: deploy FastAPI on a Linux VM, use SQLite for MVP traffic, and run behind Nginx.
- Container deployment: package the API with Docker and point it to Ollama on the same host or a separate model server.

For a first deployment:
1. Move secrets to environment variables.
2. Run `uvicorn` behind Nginx or a process manager.
3. Replace SQLite with Postgres when concurrent writes grow.
4. Keep Ollama on the same machine if you want local inference, or point to a remote model server.
