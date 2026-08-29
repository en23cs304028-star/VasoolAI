# AGENTS.md — VasoolAI

## Before doing anything
Read `vasoolai-engineering-prd.md` in this repo root, in full, before writing any code. It is the single source of truth for this project — schema, API contract, formulas, thresholds, and phase-by-phase Definition of Done are all locked there. If something isn't specified in that document, stop and ask rather than inventing a default.

## What this project is
VasoolAI: an agent that detects at-risk B2B invoice receivables for Indian MSMEs, computes statutory interest owed under the MSMED Act, decides an escalation action, and executes it through real sandboxed channels (Razorpay test-mode payment links, Twilio WhatsApp Sandbox, sandbox email) — with a full audit trail and a synthetic backtest as the measured result. Dual deliverable: Razorpay AI Buildathon (Track 03) submission and a college major project. Deadline: 5 September 2026.

## Non-negotiable constraints
- **Execute phases in order** (0 → 6), each with its own Definition of Done in the PRD's §10. Do not start a phase until the previous one's DoD checklist is fully satisfied.
- **The interest-calculation engine is deterministic code, never LLM output.** No exceptions — see PRD §1 and §7.
- **LLM provider is NVIDIA (Nemotron/Mistral models via OpenRouter)**, using the `openai` package. Do not use `google-generativeai` or `anthropic`.
- Every escalation tier, stopping rule, and approval-gate threshold is exact in PRD §5 — do not infer different numbers.
- Stay inside PRD §11's non-goals list. Do not add scope that isn't there, even if it looks easy.

## Stack quick-reference (full justification in PRD §6)
Python 3.11 / FastAPI / SQLAlchemy / SQLite (no Alembic) / XGBoost + SHAP / NVIDIA LLMs / Razorpay test mode / Twilio WhatsApp Sandbox / React+Vite (fallback: Streamlit, decide by 2 Sept per PRD §0) / pytest + hypothesis / Docker Compose.

## Working style
- Commit directly to `main`, Conventional Commits style (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- After finishing a phase, output the phase's Definition of Done checklist from the PRD with each item marked done/not-done — don't just say "phase complete."
- If a required external account/credential is missing (Razorpay, Twilio, NVIDIA, Mailtrap), stop and report exactly which one — do not stub around it silently.
