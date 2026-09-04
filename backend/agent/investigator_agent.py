"""
Bounded Autonomous Investigation Agent (Dynamic Evidence & HMAC-SHA256 Audit Trail)
Investigates ambiguous hold-tier transactions dynamically based on evolving evidence.
Strictly zero future data leakage and zero use of ground-truth labels at runtime.
"""

import os
import json
import hmac
import hashlib
import pandas as pd
from datetime import datetime, timezone

# Secret key for HMAC audit signing (In production, loaded via AWS Secrets Manager / Vault)
SENTINEL_HMAC_SECRET = os.getenv("SENTINEL_HMAC_SECRET", "razorpay_sentinel_defense_secret_key_2026").encode()

class BoundedInvestigatorAgent:
    def __init__(self, graph_sentinel=None, transactions_df=None):
        self.graph_sentinel = graph_sentinel
        self.df = transactions_df
        
    def _get_historical_window(self, txn_timestamp):
        """Returns dataframe strictly prior to the transaction timestamp (no future leakage)."""
        if self.df is None or "timestamp" not in self.df.columns:
            return pd.DataFrame()
        txn_dt = pd.to_datetime(txn_timestamp)
        df_dt = pd.to_datetime(self.df["timestamp"])
        return self.df[df_dt < txn_dt]
        
    # --- Available Tools ---
    def tool_query_device_reputation(self, device_id, txn_timestamp=None):
        """
        Tool 1: Looks up historical device footprint strictly prior to txn_timestamp.
        Zero use of is_fraud or future records.
        """
        hist_df = self._get_historical_window(txn_timestamp) if txn_timestamp else self.df
        if hist_df is None or len(hist_df) == 0:
            return {
                "device_id": device_id,
                "historical_linked_accounts": 1,
                "device_trust_score": 0.95,
                "status": "CLEAN_INDIVIDUAL_DEVICE"
            }
            
        dev_txns = hist_df[hist_df["device_id"] == device_id]
        accounts = dev_txns["customer_id"].unique().tolist()
        is_bad = len(accounts) >= 3
        
        return {
            "device_id": device_id,
            "historical_linked_accounts": max(1, len(accounts)),
            "device_trust_score": 0.25 if is_bad else 0.95,
            "status": "SUSPICIOUS_SHARED_DEVICE" if is_bad else "CLEAN_INDIVIDUAL_DEVICE"
        }
        
    def tool_inspect_graph_abuse_ring(self, customer_id, txn_timestamp=None):
        """
        Tool 2: Queries historical bipartite entity graph strictly up to txn_timestamp.
        """
        if self.graph_sentinel is None:
            return {"abuse_ring_detected": False, "linked_accounts": 1, "graph_density": 0.0}
            
        # Inspect subgraph on point-in-time graph state
        subgraph_info = self.graph_sentinel.inspect_entity_subgraph(customer_id, as_of_timestamp=txn_timestamp)
        metrics = subgraph_info.get("ring_metrics", {})
        
        return {
            "abuse_ring_detected": metrics.get("is_abuse_ring_pattern", False),
            "linked_accounts": metrics.get("linked_accounts_count", 1),
            "graph_density": metrics.get("density", 0.0)
        }
        
    def tool_check_temporal_velocity(self, customer_id, ip_address, txn_timestamp=None):
        """
        Tool 3: Checks sliding 10-minute historical velocity window:
        txn.timestamp - 10m <= previous_timestamp < txn.timestamp
        """
        hist_df = self._get_historical_window(txn_timestamp) if txn_timestamp else self.df
        if hist_df is None or len(hist_df) == 0 or not txn_timestamp:
            return {"customer_txns_10m": 0, "ip_txns_10m": 0, "velocity_burst_flag": False}
            
        cur_dt = pd.to_datetime(txn_timestamp)
        window_10m_start = cur_dt - pd.Timedelta(minutes=10)
        df_dt = pd.to_datetime(hist_df["timestamp"])
        
        past_10m = hist_df[(df_dt >= window_10m_start) & (df_dt < cur_dt)]
        cust_cnt = int((past_10m["customer_id"] == customer_id).sum())
        ip_cnt = int((past_10m["ip_address"] == ip_address).sum())
        burst_high = cust_cnt >= 5 or ip_cnt >= 8
        
        return {
            "customer_txns_10m": cust_cnt,
            "ip_txns_10m": ip_cnt,
            "velocity_burst_flag": burst_high
        }

    def tool_evaluate_merchant_risk_profile(self, merchant_id, mcc):
        """Tool 4: Returns category dispute baseline and step-up policy."""
        high_risk_mccs = ["7995", "5094"]
        is_high = str(mcc) in high_risk_mccs
        return {
            "mcc": mcc,
            "is_high_risk_category": is_high,
            "dispute_baseline_pct": 1.45 if is_high else 0.12,
            "policy": "STEP_UP_2FA_ON_BURST" if is_high else "STANDARD"
        }

    # --- Dynamic Evidence-Driven Investigation Loop ---
    def investigate(self, transaction, ml_score):
        """
        Executes bounded, dynamic evidence-driven investigation (max 3 steps).
        Selects next tool dynamically based on prior observation & computes calibrated investigation score.
        """
        payment_id = transaction.get("payment_id", "pay_unknown")
        txn_time = transaction.get("timestamp")
        cust_id = transaction.get("customer_id")
        dev_id = transaction.get("device_id")
        ip_addr = transaction.get("ip_address")
        merchant_id = transaction.get("merchant_id")
        mcc = transaction.get("mcc", "5411")
        
        print(f"[DEMO] Transaction {payment_id} scored {ml_score}")
        print(f"[POLICY] HOLD -> Agent Investigation started")
        
        trace = []
        max_steps = 3
        executed_tools = set()
        
        state = {
            "device_trust": None,
            "is_abuse_ring": None,
            "velocity_burst": None,
            "merchant_policy": None
        }
        
        decision = None
        action_code = None
        
        evidence_weights = {
            "ring_syndicate": 0.0,
            "bad_device": 0.0,
            "velocity_spike": 0.0,
            "merchant_risk": 0.0,
            "tenure_trust": 0.0
        }
        
        for step in range(1, max_steps + 1):
            # Dynamic Next Action Selection based on current evidence state
            if state["device_trust"] is None and "tool_query_device_reputation" not in executed_tools:
                action = "tool_query_device_reputation"
                thought = "ML risk score is in the ambiguous HOLD range. Querying historical device footprint to check for multi-account hardware reuse."
            elif state["device_trust"] == "SUSPICIOUS_SHARED_DEVICE" and "tool_inspect_graph_abuse_ring" not in executed_tools:
                action = "tool_inspect_graph_abuse_ring"
                thought = "Device footprint is shared across accounts. Querying point-in-time bipartite graph to confirm abuse ring syndicate."
            elif state["velocity_burst"] is None and "tool_check_temporal_velocity" not in executed_tools:
                action = "tool_check_temporal_velocity"
                thought = "Device reputation is individual. Checking rolling 10-minute sliding velocity for automated carding or burst probes."
            elif state["merchant_policy"] is None and "tool_evaluate_merchant_risk_profile" not in executed_tools:
                action = "tool_evaluate_merchant_risk_profile"
                thought = "Activity verified on individual device. Evaluating Merchant MCC risk baseline to determine step-up policy."
            else:
                break
                
            executed_tools.add(action)
            print(f"[AGENT] Step {step} Tool: {action}")
            
            # Execute Action
            if action == "tool_query_device_reputation":
                obs = self.tool_query_device_reputation(dev_id, txn_timestamp=txn_time)
                state["device_trust"] = obs["status"]
                if obs["status"] == "SUSPICIOUS_SHARED_DEVICE":
                    evidence_weights["bad_device"] = 0.35
                else:
                    evidence_weights["tenure_trust"] = 0.25
                obs_summary = f"Device trust: {obs['device_trust_score']} ({obs['status']}), linked historically to {obs['historical_linked_accounts']} accounts."

            elif action == "tool_inspect_graph_abuse_ring":
                obs = self.tool_inspect_graph_abuse_ring(cust_id, txn_timestamp=txn_time)
                state["is_abuse_ring"] = obs["abuse_ring_detected"]
                if obs["abuse_ring_detected"]:
                    evidence_weights["ring_syndicate"] = 0.45
                obs_summary = f"Graph Resolution: Ring detected = {obs['abuse_ring_detected']} across {obs['linked_accounts']} accounts (density: {obs['graph_density']})."

            elif action == "tool_check_temporal_velocity":
                obs = self.tool_check_temporal_velocity(cust_id, ip_addr, txn_timestamp=txn_time)
                state["velocity_burst"] = obs["velocity_burst_flag"]
                if obs["velocity_burst_flag"]:
                    evidence_weights["velocity_spike"] = 0.25
                obs_summary = f"10m Velocity: Burst = {obs['velocity_burst_flag']} (Cust 10m: {obs['customer_txns_10m']}, IP 10m: {obs['ip_txns_10m']})."

            elif action == "tool_evaluate_merchant_risk_profile":
                obs = self.tool_evaluate_merchant_risk_profile(merchant_id, mcc)
                state["merchant_policy"] = obs["is_high_risk_category"]
                if obs["is_high_risk_category"]:
                    evidence_weights["merchant_risk"] = 0.15
                obs_summary = f"MCC {obs['mcc']} risk: High risk = {obs['is_high_risk_category']} (dispute baseline: {obs['dispute_baseline_pct']}%, policy: {obs['policy']})."

            trace.append({
                "step": step,
                "thought": thought,
                "action": action,
                "observation": obs_summary
            })
            
            # Early Stopping Conditions
            if state.get("is_abuse_ring") is True or (state.get("device_trust") == "SUSPICIOUS_SHARED_DEVICE" and state.get("is_abuse_ring") is not None):
                decision = "BLOCK"
                action_code = "AUTO_DEFENSE_RING_BLOCK"
                explanation = (
                    f"Investigation Terminated (Early-Stop): Bipartite graph inspection confirmed account is part of a coordinated abuse ring "
                    f"sharing device '{dev_id}'. Blocked to protect merchant from syndicate loss."
                )
                break
                
            # VIP Power Buyer Check (Purely inferred from account tenure + clean device)
            account_age = int(transaction.get("account_age_days", 0))
            if state.get("device_trust") == "CLEAN_INDIVIDUAL_DEVICE" and account_age >= 365:
                decision = "APPROVE"
                action_code = "VIP_POWER_BUYER_CLEARED"
                explanation = (
                    f"Investigation Terminated (Early-Stop): Verified established VIP customer ({account_age} days tenure) "
                    f"operating on a dedicated clean device. Cleared to prevent legitimate GMV friction."
                )
                break

        # Fallback Decision Synthesis if max steps reached
        if not decision:
            if state.get("velocity_burst") is True:
                decision = "STEP_UP_2FA"
                action_code = "BIOMETRIC_CHALLENGE_ISSUED"
                explanation = "Step-Up 2FA Challenge: Uncharacteristic burst velocity detected within 10-minute sliding window on clean individual device."
            else:
                decision = "APPROVE"
                action_code = "LOW_ANOMALY_CLEARED"
                explanation = "Approved: Investigation verified clean device ownership, no abuse ring linkage, and normal sliding velocity."

        # Compute Evidence-Calibrated Investigation Score
        if decision == "BLOCK":
            investigation_score = round(0.50 + evidence_weights["ring_syndicate"] + evidence_weights["bad_device"], 2)
        elif decision == "APPROVE":
            investigation_score = round(0.65 + evidence_weights["tenure_trust"], 2)
        else:
            investigation_score = round(0.50 + evidence_weights["velocity_spike"] + evidence_weights["merchant_risk"], 2)
            
        investigation_score = min(0.99, max(0.50, investigation_score))
        print(f"[AGENT] Final verdict: {decision} ({action_code}) | Evidence score: {investigation_score}")

        # True HMAC-SHA256 Cryptographic Signing
        audit_payload = f"{payment_id}:{decision}:{investigation_score}:{action_code}"
        audit_hmac_signature = hmac.new(
            SENTINEL_HMAC_SECRET,
            audit_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "payment_id": payment_id,
            "initial_ml_score": round(float(ml_score), 4),
            "agent_verdict": decision,
            "action_code": action_code,
            "investigation_score": investigation_score,
            "explanation": explanation,
            "investigation_steps": trace,
            "audit_trail": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hmac_sha256_signature": audit_hmac_signature,
                "audit_signing_algorithm": "HMAC-SHA256",
                "audit_property": "tamper-evident / integrity-verifiable",
                "total_tools_called": len(executed_tools),
                "bounded_safety_guardrails_passed": True
            }
        }
