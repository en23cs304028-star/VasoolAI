# VasoolAI — Engineering PRD & Build Spec (for AI coding assistant)

**Purpose of this document:** this is the single source of truth for building VasoolAI. Every decision that could otherwise require a guess — schema, API contract, formulas, thresholds, library choices, folder layout — is locked below. If something is genuinely not specified here, treat it as an open question to raise, not something to invent silently. We are starting execution at **Phase 0** today; Phases 1–6 are fully specified here so later work doesn't require re-deriving decisions.

---

## 0. Locked decisions (read this first)

| Decision | Value |
|---|---|
| Language/runtime | Python 3.11+ (backend), Node 20+ (frontend) |
| Backend framework | FastAPI |
| Database | SQLite (file `sandbox.db`), via SQLAlchemy ORM — no Alembic migrations for this build; use `Base.metadata.create_all()` on startup. Alembic is deliberately skipped: not worth the setup overhead for a 14-day single-file-DB sandbox project. |
| ML | XGBoost (classification), scikit-learn for preprocessing/splits, SHAP for explanations |
| LLM | Anthropic API — `claude-sonnet-5` for message drafting, `claude-haiku-4-5` for cheap parsing tasks |
| Payments | Razorpay Payment Links API, **test mode only** |
| WhatsApp | Twilio WhatsApp Sandbox — **not** Meta WhatsApp Business API (verification takes too long for this timeline) |
| Email | Python `smtplib` against a free sandbox inbox (Mailtrap or similar) |
| Frontend | React 18 + Vite + TypeScript + TailwindCSS + Recharts. **Fallback trigger:** if Phase 3 is not complete by 2 Sept, switch to Streamlit instead of building the React frontend — decide on that date, not later. |
| Containerization | Docker + docker-compose, one service per: `backend`, `frontend` |
| Testing | `pytest` + `hypothesis` for property-based tests on the interest engine |
| Formatting/linting | `black`, `ruff`, type hints on every function signature, Google-style docstrings on every public function |
| Commit style | Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`) — commit directly to `main`, no branching overhead needed for a solo 14-day build |
| Currency | All amounts in INR, stored as `NUMERIC`/`Decimal`, never `float`, to avoid rounding errors in interest math |
| Default RBI Bank Rate | `0.055` (5.5%), stored as a configurable constant in `backend/config.py` — **not hardcoded inline anywhere**, since it changes over time |

---

## 1. Domain primer (so nothing here needs outside context)

**MSMED Act, 2006 — the rule we're encoding:**
- If a written agreement specifies a credit period, the payment due date is `invoice_date + min(agreed_credit_days, 45)`.
- If there's no written agreement, due date is `invoice_date + 15 days`.
- Once overdue, compound interest accrues at **3× the RBI Bank Rate, compounded monthly**.

**Worked example (must match the engine's output exactly):**
Principal ₹100,000, agreed credit 30 days, invoice date 1 Jan, so due date = 31 Jan. Payment actually made 15 Apr → 74 days overdue. Bank rate 5.5% → monthly rate = `3 × 0.055 / 12 = 0.01375` (1.375%/month). 74 days = 2 full months (60 days) + 14 remaining days.
- After month 1: `100000 × 1.01375 = 101,375.00`
- After month 2: `101,375.00 × 1.01375 = 102,769.16`
- Partial month (14/30 days): partial rate = `0.01375 × 14/30 = 0.006417`; `102,769.16 × 1.006417 = 103,428.11`
- **Interest owed = 103,428.11 − 100,000 = ₹3,428.11**

This exact example must appear as a unit test with this exact expected output (rounded to 2 decimals).

---

## 2. Repository structure (create exactly this)

```
vasoolai/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # settings, incl. RBI_BANK_RATE constant
│   ├── db.py                    # SQLAlchemy engine/session
│   ├── models.py                # SQLAlchemy ORM models (schema in §4)
│   ├── schemas.py                # Pydantic request/response models
│   ├── interest_engine.py       # deterministic MSMED interest math
│   ├── data_gen.py              # synthetic batch generator
│   ├── risk_model/
│   │   ├── features.py          # feature engineering
│   │   ├── train.py             # training script
│   │   └── model.py             # load/predict/SHAP wrapper
│   ├── agent/
│   │   ├── escalation.py        # tier logic + stopping rules
│   │   └── decision_engine.py   # orchestrates score → tier → action
│   ├── llm/
│   │   ├── client.py            # Anthropic API wrapper
│   │   └── prompts.py           # prompt templates (see §7)
│   ├── channels/
│   │   ├── razorpay_client.py
│   │   ├── whatsapp_client.py   # Twilio sandbox
│   │   └── email_client.py
│   ├── audit.py                 # audit log writer
│   ├── backtest.py              # agent-vs-baseline simulation
│   └── routers/                 # one file per API resource group
│       ├── invoices.py
│       ├── actions.py
│       ├── admin.py
│       ├── audit_log.py
│       └── backtest.py
├── frontend/                    # React app (Phase 5)
├── tests/
│   ├── test_interest_engine.py
│   ├── test_due_date.py
│   ├── test_stopping_rules.py
│   ├── test_api_health.py
│   └── test_risk_model.py
├── docker-compose.yml
├── Dockerfile.backend
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Environment variables (`.env.example` — commit this file with placeholder values, never real secrets)

```
ANTHROPIC_API_KEY=sk-ant-xxx
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=xxx
SMTP_PASS=xxx
RBI_BANK_RATE=0.055
DATABASE_URL=sqlite:///./sandbox.db
```

**Human prerequisite steps (cannot be automated by the coding assistant — flag these back to the user, don't attempt to sign up for accounts):** create a Razorpay test account and generate test-mode keys; create a Twilio account and activate the WhatsApp Sandbox (join code + test number, done via WhatsApp message to Twilio's sandbox number); create an Anthropic API key; create a free Mailtrap inbox. All four should be done on Day 0 before Phase 1 starts, since account-verification delays are the most common silent time-sink.

---

## 4. Database schema (SQLAlchemy models — exact fields)

**`buyers`**
`id` (PK, int) · `name` (str) · `sector` (str) · `created_at` (datetime)

**`invoices`**
`id` (PK, int) · `buyer_id` (FK→buyers.id) · `supplier_name` (str, default `"Demo Supplier"`) · `invoice_number` (str) · `invoice_date` (date) · `agreed_credit_days` (int, nullable) · `due_date` (date, computed at insert time via `interest_engine.calculate_due_date`) · `principal_amount` (Numeric(12,2)) · `status` (enum: `open` / `paid` / `partially_paid`) · `actual_payment_date` (date, nullable) · `actual_payment_amount` (Numeric(12,2), nullable) · `created_at` (datetime)

**`risk_scores`**
`id` (PK) · `invoice_id` (FK) · `scored_at` (datetime) · `risk_probability` (float, 0–1) · `risk_tier` (enum: `low`/`medium`/`high`) · `shap_top_features` (JSON/text) · `model_version` (str)

**`actions`**
`id` (PK) · `invoice_id` (FK) · `escalation_tier` (enum: `nudge`/`firm_reminder`/`statutory_notice`) · `channel` (enum: `whatsapp`/`email`) · `drafted_message` (text) · `computed_interest_amount` (Numeric(12,2), nullable — populated only for `statutory_notice`) · `payment_link_url` (text, nullable) · `requires_approval` (bool) · `approved` (bool, default `False`) · `approved_by` (str, nullable) · `sent` (bool, default `False`) · `sent_at` (datetime, nullable) · `created_at` (datetime)

**`audit_log`**
`id` (PK) · `entity_type` (str) · `entity_id` (int) · `event` (str) · `details` (JSON/text) · `created_at` (datetime)

**`backtest_runs`**
`id` (PK) · `run_at` (datetime) · `baseline_metric_recovery_days` (float) · `agent_metric_recovery_days` (float) · `baseline_metric_recovery_rate` (float) · `agent_metric_recovery_rate` (float) · `notes` (text)

---

## 5. Escalation rules (exact thresholds — do not infer different ones)

| Tier | Trigger | Auto-send allowed? | Content |
|---|---|---|---|
| `monitor` | not yet past due_date | n/a — no message | — |
| `nudge` | 1–15 days overdue | Yes, by default config flag | Friendly reminder, no interest amount mentioned |
| `firm_reminder` | 16–30 days overdue | Yes, by default config flag | Firmer tone, states days overdue, no legal citation yet |
| `statutory_notice` | 31+ days overdue **and** `risk_probability ≥ 0.6` | **No — always requires explicit human approval via `POST /actions/{id}/approve` before `POST /actions/{id}/send` will execute** | Cites MSMED Act Sections 15/16, states exact computed interest |

**Stopping rules (hard-coded, not configurable via API in this build):**
- Max **one** message per tier per invoice — never repeat the same tier.
- Max **four** total messages to the same buyer (across all their invoices) within any rolling 30-day window.
- Minimum **5-day cooldown** between any two messages sent to the same buyer.
- Any attempt to violate a stopping rule must be blocked in `agent/escalation.py`, **and logged to `audit_log` with event `stopping_rule_blocked`** — this log entry is itself part of the deliverable, since it's evidence the stopping rules work, for the pitch and for the college evaluator.

---

## 6. Risk model — exact feature list (Phase 2)

Target: `is_late` (binary — 1 if `actual_payment_date > due_date`, computed only on invoices with a known outcome, i.e. training uses `status = paid`).

Features (compute in `risk_model/features.py`):
`invoice_amount` · `agreed_credit_days` (or 15 if null) · `days_since_invoice_raised` (as of scoring date) · `buyer_historical_avg_days_late` (mean over that buyer's other paid invoices, excluding the current one) · `buyer_historical_pct_late` · `buyer_invoice_count_so_far` · `invoice_amount_pct_of_buyer_avg_order` · `month_of_year` (int 1–12) · `sector` (one-hot encoded)

Model: `XGBClassifier`, start with `n_estimators=200, max_depth=4, learning_rate=0.05` — treat as a starting point, tune only if time allows, and **report the actual test-set precision/recall/AUC in the README, whatever they are** — do not cherry-pick a favorable run.

`risk_tier` mapping from `risk_probability`: `< 0.35` → `low`, `0.35–0.6` → `medium`, `> 0.6` → `high`.

---

## 7. LLM usage — exact constraints (Phase 3)

**Hard rule, non-negotiable:** the LLM drafts prose only. Every number in a message (amount, days overdue, interest, buyer name) is injected into the prompt as already-computed fact, and the system prompt must explicitly instruct the model not to alter or invent any figure. Verify this in code review, not just by inspection — a test in `tests/test_llm_output.py` should check that every numeric value appearing in a drafted message matches a value passed into the prompt.

System prompt skeleton (`llm/prompts.py`):
```
You are drafting a payment reminder on behalf of an Indian MSME supplier to
their buyer. Use ONLY the facts provided below — never invent, round, or
alter any number. Match this tone exactly for the given tier:
- nudge: friendly, brief, assumes an oversight
- firm_reminder: professional, direct, states the invoice is now overdue
- statutory_notice: formal, cites MSMED Act Sections 15 and 16, states the
  exact interest amount provided, references the buyer's obligation

Facts: {buyer_name}, {invoice_number}, {principal_amount}, {days_overdue},
{interest_amount (if tier is statutory_notice)}, {payment_link}
```

---

## 8. API contract (exact routes — implement all of these, no more, no fewer for this build)

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /health` | liveness check | returns `{"status": "ok"}` |
| `POST /admin/generate-batch?n=250&seed=42` | synthetic data generation | returns `{"buyers_created": int, "invoices_created": int}` |
| `GET /invoices?status=&overdue=` | list invoices | filterable |
| `GET /invoices/{id}` | invoice detail incl. latest risk score if present | |
| `POST /invoices/{id}/score` | run risk model on one invoice | writes to `risk_scores`, also writes `audit_log` event `risk_scored` |
| `POST /batch/score` | score all open invoices | |
| `POST /invoices/{id}/plan-action` | run decision engine, create a queued `actions` row | does not send |
| `POST /actions/{id}/approve` | body: `{"approved_by": "string"}` | sets `approved=True` |
| `POST /actions/{id}/send` | executes via the correct channel adapter | **must check `requires_approval` and block with HTTP 403 if `approved=False`**; writes `audit_log` event `action_sent` |
| `GET /audit-log?entity_type=&entity_id=` | filtered audit trail | |
| `POST /backtest/run` | run agent-vs-baseline simulation over full batch | writes + returns a `backtest_runs` row |
| `GET /backtest/latest` | latest backtest result | for the dashboard |

---

## 9. Backtest methodology (Phase 5 — must be this exact design, since it's the core evaluation deliverable)

For every invoice in the synthetic batch (which has a known, generated ground-truth outcome — paid on time or late, and how late):
- **Baseline:** simulate a naive strategy — flag and message every invoice the day it turns 45 days overdue, no prioritization, one message only.
- **Agent:** simulate VasoolAI's actual tier/timing logic as specified in §5.
- **Metrics to report (both, side by side):** mean days-to-recovery (simulated, using the batch's generated ground truth as the "true" payment date the message could influence — define this simulation assumption explicitly in the README, since it's a synthetic proxy, not a real causal claim) and overall recovery rate within a fixed window (e.g., % of overdue invoices "recovered" within 30 days of first contact).
- **Label this everywhere as a synthetic backtest**, in the dashboard UI, the README, and the pitch script. Never phrase results as real-world recovered money.

---

## 10. Full phase plan with Definition of Done

### Phase 0 — Setup (23 Aug) — **start here, today**
Tasks:
1. `git init`, create `.gitignore` (Python + Node + `.env` + `sandbox.db`)
2. Create the exact folder structure in §2 (empty files/`__init__.py` where needed)
3. Create `requirements.txt`: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-dotenv`, `xgboost`, `scikit-learn`, `shap`, `pandas`, `numpy`, `anthropic`, `razorpay`, `twilio`, `pytest`, `hypothesis`, `black`, `ruff` (use latest stable compatible versions — do not guess exact patch pins)
4. `backend/config.py` — load `.env`, expose `settings.RBI_BANK_RATE` etc.
5. `backend/db.py` — SQLAlchemy engine against `sqlite:///./sandbox.db`, session factory
6. `backend/models.py` — all six tables from §4
7. `backend/main.py` — FastAPI app, call `Base.metadata.create_all()` on startup, mount a `/health` route
8. `.env.example` per §3
9. `README.md` — project one-liner, setup steps (`pip install -r requirements.txt`, `uvicorn backend.main:app --reload`), and a placeholder "Results" section to fill in later
10. `docker-compose.yml` + `Dockerfile.backend` — minimal, backend service only for now
11. Push to a **public** GitHub repo

**Definition of Done (all must be true):**
- [ ] Fresh `git clone` + `docker compose up` (or the documented pip/uvicorn steps) starts the backend with no manual edits beyond copying `.env.example` to `.env`
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Running the app once creates `sandbox.db` with all six tables (verify: `sqlite3 sandbox.db ".tables"` lists all of them)
- [ ] Repo structure matches §2 exactly
- [ ] `.env` is gitignored; `.env.example` is committed with placeholders only, no real secrets
- [ ] At least one commit is pushed to a public GitHub repo

### Phase 1 — Data & interest engine (24–25 Aug)
Build `data_gen.py` (synthetic buyers/invoices, calibrated so ~35–45% of invoices end up late, matching the "delayed payment is common" reality from the earlier research) and `interest_engine.py` (exact formulas from §1).

**Definition of Done:**
- [ ] `POST /admin/generate-batch?n=250&seed=42` produces exactly 250 invoices across ~30–40 buyers
- [ ] `tests/test_interest_engine.py` passes, including the exact worked example from §1 (₹3,428.11 expected) and a `hypothesis` property test asserting interest is always ≥ 0 and non-decreasing in days overdue
- [ ] `tests/test_due_date.py` passes: agreed days capped at 45; no-agreement case defaults to 15
- [ ] `GET /invoices?overdue=true` returns correct computed `due_date` and interest for 5 manually spot-checked invoices

### Phase 2 — Risk model (26–28 Aug)
Build `risk_model/features.py`, `train.py`, `model.py` per §6.

**Definition of Done:**
- [ ] Training script produces a held-out test-set precision/recall/AUC, printed and saved into `README.md`'s Results section — real numbers, not placeholders
- [ ] `POST /invoices/{id}/score` returns a risk tier + top-3 SHAP features in under 500ms
- [ ] `tests/test_risk_model.py` passes: model loads, predicts on a known synthetic sample, output shape is correct

### Phase 3 — Agent & LLM layer (29–31 Aug)
Build `agent/escalation.py`, `agent/decision_engine.py`, `llm/client.py`, `llm/prompts.py` per §5 and §7.

**Definition of Done:**
- [ ] `POST /invoices/{id}/plan-action` creates a correctly-tiered `actions` row
- [ ] Stopping rules enforced and tested in `tests/test_stopping_rules.py`: no invoice gets a repeated tier; no buyer exceeds 4 messages/30 days; violations produce an `audit_log` entry with event `stopping_rule_blocked`
- [ ] `POST /actions/{id}/send` returns HTTP 403 if `requires_approval=True` and `approved=False`
- [ ] `tests/test_llm_output.py` passes: 10 sample drafted messages contain zero numeric values that don't match the injected facts

**→ Decision point (2 Sept):** if this phase isn't done, switch the frontend plan to Streamlit per §0.

### Phase 4 — Real integrations (1–2 Sept)
Build `channels/razorpay_client.py`, `channels/whatsapp_client.py`, `channels/email_client.py`.

**Definition of Done:**
- [ ] A real Razorpay test-mode payment link is generated via the API and resolves in a browser
- [ ] A real WhatsApp Sandbox message is received on a test phone (save a screenshot as evidence, store in `docs/evidence/`)
- [ ] A test email is confirmed landing in the sandbox inbox
- [ ] One full end-to-end trace works: generate batch → score → plan-action → approve (if needed) → send → payment link clickable in the delivered message

### Phase 5 — Dashboard & backtest (3–4 Sept)
Build `backend/backtest.py` per §9, and the frontend (React or Streamlit per the decision point above).

**Definition of Done:**
- [ ] `POST /backtest/run` executes and stores a `backtest_runs` row with all four metrics populated
- [ ] Dashboard shows: batch table with risk tiers, a per-invoice drill-down with its audit trail, and a Backtest Results view/chart comparing agent vs. baseline — labeled explicitly as a synthetic backtest
- [ ] Every number shown on the dashboard traces back to a real API response, nothing hardcoded in the frontend

### Phase 6 — Packaging & submission (5 Sept)
**Definition of Done:**
- [ ] `docker-compose.yml` runs both backend and frontend with one command on a clean machine
- [ ] `README.md` finalized: problem, architecture diagram, setup steps, real test results (risk model metrics + backtest numbers), and the evidence screenshots from Phase 4
- [ ] 5-minute pitch video recorded and uploaded
- [ ] Razorpay submission form completed before the deadline

---

## 11. Explicit non-goals for this build (do not implement, even if it seems easy)

Real MSME pilot users or real customer data · crowdsourced cross-customer buyer risk index · MSME ODR-portal auto-filing · production Meta WhatsApp Business API · Alembic migrations · authentication/multi-tenancy (this is a single-demo-tenant sandbox) · Hindi/regional-language message generation · Celery/Redis or any distributed task queue (batch operations run synchronously — the data volumes here don't need it, and adding it would burn time without improving the demo).
