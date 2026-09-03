# FEATURE_LEDGER.md — what we're actually adding, and what we're not

**Purpose of this document:** with 2 days left, it's easy for "we added a feature" and "we relabeled something that already existed" to blur together under deadline pressure. This is the honest accounting, meant to be read before writing the pitch script or the README's feature list — so nothing said out loud goes further than what was actually built.

---

## 1. Genuinely NEW code — 1 item

### Promise-to-pay tracker
**Status: new schema, new endpoint, new dashboard element. Real new functionality.**

- New column: `actions.promised_payment_date` (nullable date)
- New endpoint: `POST /actions/{id}/promise` — records a buyer's stated promise-to-pay date, body: `{"promised_date": "YYYY-MM-DD"}`
- Dashboard: invoice drill-down (Tab 2) shows the promised date if one exists, and flags it visually if `today > promised_payment_date` and the invoice is still unpaid (a "broken promise" indicator)
- **What this does NOT include, and shouldn't by Friday:** no automated follow-up logic when a promise is broken, no separate promise-tracking analytics/reporting. It's a data field and a flag, not a new workflow engine. Don't let the pitch script imply more than that.

**Definition of Done:**
- [x] Field exists, migration/table-recreation confirmed via `sqlite3 sandbox.db ".schema actions"`
- [x] Endpoint tested with a real curl call, response confirmed
- [x] Dashboard shows the promised date and the broken-promise flag on at least one real test invoice
- [x] No existing test broken by the schema change (`pytest` full run, clean)

---

## 2. RELABELED, not new — 1 item

### "Payment degradation → root cause → recovery action"
**Status: zero new code. This is the existing risk model + SHAP explainability + escalation/decision engine, described using this direction's specific language.**

| Track's example language | What we already built (Phase 2 & 3) |
|---|---|
| "Payment degradation" | The risk model flags an invoice as high-risk (`risk_probability`, `risk_tier`) |
| "Root cause" | SHAP's top-3 contributing features, already returned by `POST /invoices/{id}/score` |
| "Recovery action" | The escalation tier + drafted message + send, already built in Phase 3/4 |

**The only actual work here is documentation and dashboard labeling** — adding a sentence to the README and possibly a small caption in the dashboard explicitly naming this mapping. **No schema change, no new endpoint, no new logic.**

**This must be described honestly in the pitch and README as "the existing pipeline mapped to this direction," not as a second feature built.** A reasonable, accurate sentence: *"Our core pipeline — risk detection, SHAP-based root-cause explanation, and tiered recovery action — also directly satisfies the track's 'payment degradation → root cause → recovery action' pattern; we didn't build this separately, it's the same engine viewed through that lens."*

**Definition of Done:**
- [x] README explicitly states this is the same pipeline, not separate functionality
- [x] No new code committed under this item — if any got written, that's scope creep worth catching, not crediting

---

## 3. Explicitly NOT being added, and why (good to have ready if asked)

| Direction | Why excluded |
|---|---|
| Failed-subscription recovery | No recurring-billing/mandate domain exists in the schema — would require new tables and synthetic data from scratch, not additive |
| Checkout drop-off recovery | Different domain (cart/session events), same problem as above |
| Mandate retry sequencer | UPI/NACH-specific logic, new domain from scratch |
| Hinglish voice recovery | Requires a new external API integration (speech-to-text) — the single highest-risk category of work in this project's own history (see: the multi-day LLM provider and Twilio channel debugging in Phases 3–4) |

This table itself is worth keeping — if a judge asks "why only these two," the honest answer is "we scoped based on what was additive to existing infrastructure versus what required a new domain from scratch with 2 days on the clock," which is a *good* answer, not a defensive one.

---

## 4. Honest function-count summary, for the pitch script

**Before this addition:** 1 of 7 example directions covered (B2B receivables chaser).
**After this addition:** 2 of 7 directions covered by genuinely new work (B2B receivables chaser + promise-to-pay tracker), plus 1 more (payment degradation → root cause → recovery action) satisfied by the existing pipeline under a different framing, not by new code.

**One sentence that stays accurate under any follow-up question:**
> "We built one workflow in real depth — the B2B receivables chaser — with a genuine risk model, LLM-drafted escalation, and real channel integrations. On top of that, we added a promise-to-pay tracker, and our core detection-explanation-action pipeline happens to also satisfy the 'payment degradation → root cause → recovery action' pattern, though that wasn't separately built — it's the same engine."

Do not say "we implemented 3 of the 7 directions" in the pitch — it's technically defensible but reads as inflated once someone asks a follow-up about the third one. Say it the way the sentence above says it: precise about what's new versus what's reframed.
