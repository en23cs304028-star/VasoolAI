# VasoolAI

VasoolAI is an AI-powered payment recovery assistant for Indian MSMEs, automating follow-ups and interest computation per the MSMED Act.

## Track 03 Capabilities & Feature Mapping

VasoolAI addresses B2B payment recovery with depth, deterministic statutory compliance, and transparent machine learning:

1. **B2B Receivables Chaser (Core Workflow)**:
   - Automated overdue detection calibrated to the MSMED Act, 2006 (credit periods capped at 45 days).
   - Deterministic compound interest computation (3× RBI Bank Rate, compounded monthly) — zero LLM hallucination in financial math.
   - Tiered escalation engine (`nudge` → `firm_reminder` → `statutory_notice`) with strict stopping rules (5-day cooldown, max 1 message/tier, max 4 messages/30 days) and mandatory human-in-the-loop approval gates for legal notices.
   - Real sandboxed channel execution: Razorpay payment link generation, Twilio WhatsApp sandbox, and Mailtrap email.

2. **Promise-to-Pay Tracker (New Capability)**:
   - Tracks buyer commitments via `POST /actions/{id}/promise` with timestamped audit logging.
   - Dashboard flags broken promises visually when `today > promised_payment_date` and the invoice remains unpaid.

3. **Payment Degradation → Root Cause → Recovery Action (Pipeline Mapping)**:
   - *Our core pipeline — risk detection, SHAP-based root-cause explanation, and tiered recovery action — also directly satisfies the track's 'payment degradation → root cause → recovery action' pattern; we didn't build this separately, it's the same engine viewed through that lens.*
     - **Payment Degradation:** XGBoost risk model scores overdue probability and categorizes risk into low/medium/high tiers.
     - **Root Cause:** TreeSHAP calculates top-3 contributing risk features per invoice in under 500ms.
     - **Recovery Action:** The escalation decision engine plans the appropriate tier and channel, drafting non-hallucinatory recovery messages with embedded Razorpay payment links.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in any required actual values.
   ```bash
   cp .env.example .env
   ```

3. **Run the Backend**
   ```bash
   uvicorn backend.main:app --reload
   ```
   The API will be accessible at http://localhost:8000.
   Check health: http://localhost:8000/health

4. **Run via Docker**
   ```bash
   docker-compose up --build
   ```

## Results

**Risk Model Performance (XGBoost, Held-out Test Set):**
- Precision: 0.7143
- Recall: 0.6250
- AUC: 0.7292
*(Note: The test set is only ~50 invoices—20% of a 250-invoice batch—so these metrics are directional, not high-precision estimates.)*

**Agent vs Baseline Backtest Results (Synthetic Simulation):**
- Baseline (45-Day Naive) Mean Days of Advance Notice: -14.7 days
- Baseline Recovery Rate: 19.5%
- Ablation (Day 1 Flat) Mean Days of Advance Notice: 29.3 days
- Ablation Recovery Rate: 100.0%
- VasoolAI Agent Mean Days of Advance Notice: 29.1 days
- VasoolAI Agent Recovery Rate: 100.0%

*Interpretation: The agent and the day-1 ablation perform near-identically on advance-notice and recovery-rate because these metrics are driven by first-contact timing. Per the escalation rules, only the statutory_notice tier (31+ days overdue) is risk-gated — nudge fires on a fixed day-count regardless of the model's score. This backtest therefore isolates the value of early contact.*

## Known Sandbox Limitations
Due to Twilio's Sandbox rules for Trial accounts, outbound WhatsApp messages can only be delivered to numbers that have explicitly joined the sandbox via the designated code. To ensure tests execute smoothly, the `data_gen.py` script assigns the exact same verified `TEST_WHATSAPP_NUMBER` (from your `.env` file) to the `phone_number` field of every synthetic `Buyer` record. In a production environment, this field would contain the actual unique contact number for each buyer.

Furthermore, WhatsApp delivery via Twilio's trial-tier 'Try out WhatsApp' flow requires a pre-approved Content Template for all business-initiated messages, even within an active session window — a genuine Twilio trial-account policy, not an implementation bug. Razorpay, email, and the approval gate are fully verified with real evidence; WhatsApp's code path is implemented and correctly blocked/logged, but real delivery requires either a paid Twilio account or Meta-approved custom templates, both out of scope for this sandbox build.
