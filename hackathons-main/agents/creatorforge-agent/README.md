# CreatorForge Agent

Production-oriented CreatorForge implementation for the Nevermined autonomous business hackathon.

## Features

- 8-agent hierarchy (CEO, directors, specialists)
- Strands-style specialist tools with LangGraph-backed orchestration
- Seller APIs for 5 creative products
- Procurement APIs with budget/ROI/repeat/switch logic
- Human approval workflow for high-value purchases
- SQLite persistence and immutable audit events
- Nevermined `PaymentMiddleware` with dynamic route credits
- Mindra workflow + SSE orchestration integration (live)
- ZeroClick ad-context and attribution integration (live)
- Trinity deployment artifacts via system manifest (in `trinity-main`)

## Quick start

```bash
cd agents/creatorforge-agent
cp .env.example .env
poetry install
poetry run creatorforge-api
```

Server starts on `http://localhost:3010` by default.

## Public endpoints

- `POST /v1/assets/ad-copy`
- `POST /v1/assets/visual`
- `POST /v1/assets/brand-kit`
- `POST /v1/assets/campaign`
- `POST /v1/assets/ad-enriched`
- `GET /pricing`
- `GET /.well-known/agent.json`
- `GET /health`
- `GET /stats`

## Internal endpoints

- `POST /v1/procurement/run`
- `GET /v1/procurement/vendors`
- `GET /v1/procurement/decisions/{decision_id}`
- `GET /v1/approvals/pending`
- `POST /v1/approvals/{approval_id}/decision`
- `POST /v1/ad-events/attribution`

## Notes

- No mock fallback mode is provided for Mindra/ZeroClick in production paths.
- Ad-enriched generation fails if ZeroClick context cannot be retrieved.
- Ad context is fetched before generation and logged through the attribution funnel.
- Mindra requires `MINDRA_BASE_URL`, creative/procurement workflow slugs, and `MINDRA_API_KEY`.
- High-value procurement actions above 10 credits require approval.
