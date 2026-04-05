# LLM Router MVP Interview Q&A

## 1. Why did you choose a classifier before generation instead of routing with hand-written rules only?
I wanted routing decisions that scale beyond a few obvious keywords. Hand-written rules are easy to start with, but they become brittle as prompt variety grows. A classifier lets the system learn patterns from labeled examples, improves consistency, and creates a path for retraining as new prompt types appear.

## 2. Why use TF-IDF + Logistic Regression over embeddings or an LLM judge for the MVP?
For an MVP, TF-IDF + Logistic Regression is fast, cheap, interpretable, and easy to train on a small labeled dataset. It is also lightweight enough to run locally with low latency. Embeddings or an LLM judge could improve flexibility later, but they would increase complexity, cost, and operational dependencies too early.

## 3. Why did you calibrate the classifier, and how does calibration improve routing quality?
The router does not only need the predicted label, it also needs a reliable confidence score. Calibration makes the predicted probabilities more trustworthy, which matters because low-confidence cases are escalated to the strong model. Without calibration, fallback decisions would be less stable and could either waste money or hurt answer quality.

## 4. Why is the fallback threshold `0.55`, and how would you tune it in production?
`0.55` is a practical MVP starting point that gives the router some caution without sending too many prompts to the expensive tier. In production, I would tune it using offline evaluation plus real traffic analysis by measuring the tradeoff between cost, latency, and routing mistakes. The right threshold depends on business tolerance for bad answers versus API spend.

## 5. How do you balance latency, quality, and cost across weak, moderate, and strong models?
The main idea is to reserve expensive capacity for prompts that actually need it. Weak prompts go to the cheapest local model, moderate prompts go to a stronger local model, and strong or uncertain prompts go to the cloud model. That gives low latency and near-zero cost for simpler work while protecting quality on complex requests.

## 6. Why use Ollama for local models and OpenAI/Gemini for the strong tier?
Ollama is a good fit for local inference because it is simple to run, supports multiple local models, and keeps cheap requests off paid APIs. OpenAI and Gemini are good strong-tier options because they provide high-quality frontier models through stable APIs. This hybrid design keeps the architecture flexible and demonstrates vendor-agnostic routing.

## 7. What happens when a local model or API provider is unavailable?
The current code catches request failures and returns an availability message instead of crashing the service. That keeps the API responsive and makes failures visible in the logs. A stronger production version would also add retries, circuit breaking, health-based provider failover, and clearer user-facing error policies.

## 8. Why store logs in SQLite first, and when would you move to Postgres?
SQLite is perfect for an MVP because it has zero setup overhead, works well for local demos, and still gives durable analytics. I would move to Postgres when write concurrency increases, when multiple services need shared access, or when I need stronger querying, indexing, and operational reliability.

## 9. How would you detect misroutes and use the logged data for retraining?
I would review low-confidence cases, fallback-heavy cases, bad user outcomes, and prompts whose final answer quality did not match the predicted class. Those examples become high-value labeled data for the next training cycle. Over time, the router improves because logging turns production traffic into a feedback loop for error analysis and retraining.

## 10. How would you expand the router to support more classes, tenants, or providers?
I would separate routing policy from provider integration more clearly, so classes, thresholds, and model maps can be configured instead of hard-coded. For tenants, I would support per-tenant policies, budgets, and model preferences. For providers, I would add a provider abstraction so new backends can be plugged in without changing the API contract.

## 11. What are the main risks of this architecture, and how would you mitigate them?
The biggest risks are classifier drift, overconfidence, provider outages, and SQLite limits under concurrency. I would mitigate them with better monitoring, periodic retraining, threshold tuning, provider failover, and eventually moving persistence to Postgres. Another risk is that complexity labels may not perfectly capture answer quality, so I would add human review or quality scoring for important traffic.

## 12. If traffic grows, which layer would you scale or redesign first?
I would first address persistence and routing operations before replacing the classifier. SQLite would be the earliest bottleneck under concurrent writes, so I would move to Postgres and add better observability. After that, I would look at async request handling, caching, queueing for expensive calls, and possibly a richer router if prompt diversity outgrows the current classifier.
