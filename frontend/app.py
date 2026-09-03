import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="VasoolAI Dashboard", layout="wide")
st.title("VasoolAI Dashboard")
st.caption("🤖 **VasoolAI**: Autonomous B2B Receivables Recovery for Indian MSMEs | MSMED Act Statutory Interest Engine")

tab1, tab2, tab3 = st.tabs(["Batch View", "Invoice Drill-down", "Backtest Results"])

# ----------------- Tab 1: Batch View -----------------
with tab1:
    st.header("Invoice Batch")
    if st.button("Refresh Batch Data"):
        st.rerun()
        
    try:
        response = requests.get(f"{API_URL}/invoices")
        if response.status_code == 200:
            invoices = response.json()
            if invoices:
                df = pd.DataFrame(invoices)
                # Reorder and format columns
                cols = ['id', 'buyer_id', 'invoice_number', 'principal_amount', 'status', 'due_date', 'actual_payment_date', 'is_overdue', 'risk_tier']
                df = df[[c for c in cols if c in df.columns]]
                
                # Color code risk tiers
                def color_risk(val):
                    if val == 'high': return 'background-color: #ffcccc'
                    if val == 'medium': return 'background-color: #ffffcc'
                    if val == 'low': return 'background-color: #ccffcc'
                    return ''
                
                st.dataframe(df.style.applymap(color_risk, subset=['risk_tier']), use_container_width=True)
            else:
                st.info("No invoices found.")
        else:
            st.error(f"Failed to fetch invoices: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ----------------- Tab 2: Invoice Drill-down -----------------
with tab2:
    st.header("Invoice Drill-down")
    st.caption("ℹ️ **Track Alignment:** Core pipeline maps to *Payment Degradation (Risk Model) → Root Cause (SHAP Analysis) → Recovery Action (Escalation & Channel)*.")

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        invoice_id = st.number_input("Enter Invoice ID", min_value=1, step=1, value=1, key="drill_invoice_id")
    with col_btn:
        st.write("")
        st.write("")
        fetch_clicked = st.button("Fetch Invoice Details", use_container_width=True)
    
    try:
        inv_resp = requests.get(f"{API_URL}/invoices/{invoice_id}")
        audit_resp = requests.get(f"{API_URL}/audit-log?entity_type=invoice&entity_id={invoice_id}")
        action_audit_resp = requests.get(f"{API_URL}/audit-log?entity_type=action")
        
        if inv_resp.status_code == 200 and 'id' in inv_resp.json():
            inv = inv_resp.json()
            st.subheader(f"Invoice {inv.get('invoice_number')} (ID: {inv.get('id')})")
            
            # --- Promise to Pay Tracker Section ---
            st.markdown("### 🤝 Promise-to-Pay Tracker")
            promised_date_str = inv.get("promised_payment_date")
            today_date = date.today()
            
            if promised_date_str:
                promised_date = datetime.strptime(promised_date_str, "%Y-%m-%d").date()
                is_unpaid = inv.get("status") != "paid"
                
                if today_date > promised_date and is_unpaid:
                    st.error(
                        f"⚠️ **BROKEN PROMISE ALERT:** Buyer stated a promise to pay by **{promised_date_str}**, "
                        f"but the invoice remains **{inv.get('status')}** as of today (**{today_date.isoformat()}**)."
                    )
                elif not is_unpaid:
                    st.success(f"✅ **Promise Kept:** Stated promise date was **{promised_date_str}** and invoice is marked **PAID**.")
                else:
                    st.info(f"⏳ **Active Promise-to-Pay:** Payment promised on **{promised_date_str}** (Pending due date).")
            else:
                st.caption("No promise-to-pay date recorded for this invoice yet.")

            # Form to record or update promise to pay
            actions = inv.get("actions", [])
            if actions:
                latest_action = actions[0]
                with st.expander("📝 Record / Update Promise to Pay Date"):
                    with st.form(f"promise_form_{invoice_id}"):
                        new_promised_date = st.date_input("Promised Payment Date", value=today_date)
                        target_action_id = st.selectbox(
                            "Select Action to Attach Promise",
                            options=[a["id"] for a in actions],
                            format_func=lambda aid: f"Action #{aid} ({next((a['escalation_tier'] for a in actions if a['id'] == aid), '')})"
                        )
                        submitted = st.form_submit_button("Record Promise")
                        if submitted:
                            p_resp = requests.post(
                                f"{API_URL}/actions/{target_action_id}/promise",
                                json={"promised_date": new_promised_date.isoformat()}
                            )
                            if p_resp.status_code == 200:
                                st.success(f"Promise-to-pay date {new_promised_date.isoformat()} recorded successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to record promise: {p_resp.text}")
            else:
                st.caption("💡 Generate/plan an action first to record a buyer promise on the action.")
            
            st.markdown("---")

            # --- Invoice Details & MSMED Interest ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Buyer ID:** {inv.get('buyer_id')}")
                st.write(f"**Supplier:** {inv.get('supplier_name')}")
                st.write(f"**Status:** `{inv.get('status')}`")
            with col2:
                st.write(f"**Principal Amount:** ₹{inv.get('principal_amount', 0):,.2f}")
                st.write(f"**Invoice Date:** {inv.get('invoice_date')}")
                st.write(f"**Due Date:** {inv.get('due_date')}")
            with col3:
                interest_val = inv.get('interest_owed', 0)
                st.metric("Statutory MSMED Interest", f"₹{interest_val:,.2f}")
                if inv.get('actual_payment_date'):
                    st.write(f"**Payment Date:** {inv.get('actual_payment_date')}")

            # --- Pipeline Diagnostic Section ---
            st.markdown("### 🔍 Payment Degradation → Root Cause → Recovery Action")
            diag_col1, diag_col2, diag_col3 = st.columns(3)
            
            with diag_col1:
                st.markdown("**1. Payment Degradation**")
                risk_tier = inv.get("risk_tier") or "Unscored"
                risk_prob = inv.get("risk_probability")
                prob_str = f" ({risk_prob*100:.1f}%)" if risk_prob is not None else ""
                st.write(f"Risk Tier: **{risk_tier.upper()}{prob_str}**")
                if st.button("Score Invoice Risk", key=f"score_btn_{invoice_id}"):
                    s_res = requests.post(f"{API_URL}/invoices/{invoice_id}/score")
                    if s_res.status_code == 200:
                        st.success("Scored successfully!")
                        st.rerun()
                    else:
                        st.error(f"Scoring failed: {s_res.text}")

            with diag_col2:
                st.markdown("**2. Root Cause (SHAP Top Features)**")
                shap_str = inv.get("shap_top_features")
                if shap_str:
                    try:
                        shap_data = json.loads(shap_str)
                        for feat, val in shap_data.items():
                            st.write(f"- `{feat}`: {val:+.3f}")
                    except Exception:
                        st.write(shap_str)
                else:
                    st.caption("Score invoice to inspect root-cause features.")

            with diag_col3:
                st.markdown("**3. Recovery Action**")
                if actions:
                    act = actions[0]
                    st.write(f"Tier: **{act.get('escalation_tier')}**")
                    st.write(f"Channel: `{act.get('channel')}`")
                    st.write(f"Approved: {'✅ Yes' if act.get('approved') else '⏳ Pending'}")
                    st.write(f"Sent: {'✅ Sent' if act.get('sent') else '❌ Not Sent'}")
                else:
                    st.caption("No action planned yet.")
                    if st.button("Plan Recovery Action", key=f"plan_btn_{invoice_id}"):
                        p_res = requests.post(f"{API_URL}/invoices/{invoice_id}/plan-action")
                        if p_res.status_code == 200:
                            st.success("Action planned!")
                            st.rerun()
                        else:
                            st.error(f"Planning failed: {p_res.text}")

            # --- Audit Trail ---
            st.markdown("### 📜 Audit Trail")
            invoice_logs = []
            if audit_resp.status_code == 200:
                invoice_logs.extend(audit_resp.json())
            if action_audit_resp.status_code == 200:
                action_ids = [a["id"] for a in actions]
                action_logs = [l for l in action_audit_resp.json() if l.get("entity_id") in action_ids]
                invoice_logs.extend(action_logs)
                
            # Sort by created_at desc
            invoice_logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            if invoice_logs:
                for log in invoice_logs:
                    with st.expander(f"{log['created_at']} — [{log['entity_type'].upper()}] {log['event']}"):
                        st.write(log['details'])
            else:
                st.info("No audit events found for this invoice.")
            
        else:
            st.warning("Invoice not found.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ----------------- Tab 3: Backtest Results -----------------
with tab3:
    st.header("Agent vs Baseline Backtest")
    st.caption("⚠️ **Synthetic Backtest:** These metrics represent simulated recoveries based on historical batch data, not real-world collected funds.")
    
    if st.button("Run New Backtest Simulation"):
        with st.spinner("Running simulation across batch..."):
            try:
                res = requests.post(f"{API_URL}/backtest/run")
                if res.status_code == 200:
                    st.success("Backtest completed successfully!")
                else:
                    st.error(f"Failed to run backtest: {res.text}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
    st.markdown("---")
    
    try:
        latest = requests.get(f"{API_URL}/backtest/latest")
        if latest.status_code == 200:
            data = latest.json()
            st.write(f"**Last Run:** {data['run_at']}")
            st.info(data['notes'])
            
            st.markdown("""
            **Interpretation:** The agent and the day-1 ablation perform near-identically on advance-notice and recovery-rate because these metrics are driven by first-contact timing, and per §5's escalation rules, only the statutory_notice tier (31+ days overdue) is risk-gated — nudge fires on a fixed day-count regardless of the model's score. This backtest therefore isolates the value of early contact rather than risk-based prioritization specifically. A metric that would isolate the model's actual contribution — e.g., precision/recall of which invoices genuinely warranted statutory_notice escalation versus which resolved with a lighter touch — is noted as future work.
            """)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Baseline (45-Day Naive)")
                st.metric("Mean Days of Advance Notice", f"{data['baseline_metric_recovery_days']:.1f} days")
                st.metric("Recovery Rate", f"{data['baseline_metric_recovery_rate']*100:.1f}%")
                
            with col2:
                st.subheader("Ablation (Day 1 Flat)")
                st.metric("Mean Days of Advance Notice", f"{data['ablation_metric_recovery_days']:.1f} days", 
                          delta=f"{data['ablation_metric_recovery_days'] - data['baseline_metric_recovery_days']:.1f} days vs Baseline")
                
                ab_rec_diff = (data['ablation_metric_recovery_rate'] - data['baseline_metric_recovery_rate']) * 100
                st.metric("Recovery Rate", f"{data['ablation_metric_recovery_rate']*100:.1f}%",
                          delta=f"{ab_rec_diff:.1f}% vs Baseline")
                          
            with col3:
                st.subheader("VasoolAI Agent")
                st.metric("Mean Days of Advance Notice", f"{data['agent_metric_recovery_days']:.1f} days", 
                          delta=f"{data['agent_metric_recovery_days'] - data['ablation_metric_recovery_days']:.1f} days vs Ablation")
                
                rec_diff = (data['agent_metric_recovery_rate'] - data['ablation_metric_recovery_rate']) * 100
                st.metric("Recovery Rate", f"{data['agent_metric_recovery_rate']*100:.1f}%",
                          delta=f"{rec_diff:.1f}% vs Ablation")
        else:
            st.info("No backtest runs found. Run a simulation to see results.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
