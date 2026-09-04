"""
Feature Engineering Engine for Razorpay Sentinel
Implements strict stateful historical feature extraction without future data leakage.
Features:
- Historical MCC amount mean & std calculated from training window
- Point-in-time rolling velocity
- Point-in-time device/IP multi-account entropy
- Point-in-time bipartite graph centrality
"""

import os
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime

class FeaturePipeline:
    def __init__(self):
        self.mcc_stats = {}
        self.fitted = False
        
    def fit(self, train_df):
        """Fits historical statistics strictly on the training partition."""
        mcc_grouped = train_df.groupby("mcc")["amount"].agg(["mean", "std"]).reset_index()
        for _, row in mcc_grouped.iterrows():
            mean_val = float(row["mean"])
            std_val = float(row["std"]) if not np.isnan(row["std"]) and row["std"] > 0 else 1.0
            self.mcc_stats[str(row["mcc"])] = {"mean": mean_val, "std": std_val}
        self.fitted = True

    def extract_point_in_time_features(self, df, history_df=None):
        """
        Extracts features for transactions using ONLY past transactions (point-in-time).
        history_df: historical transactions prior to df (for test/inference time).
        """
        df = df.copy()
        df["dt"] = pd.to_datetime(df["timestamp"])
        
        # Combine historical context with current window for rolling state
        if history_df is not None:
            full_context = pd.concat([history_df.copy(), df.copy()]).reset_index(drop=True)
            full_context["dt"] = pd.to_datetime(full_context["timestamp"])
            full_context = full_context.sort_values(by="dt").reset_index(drop=True)
            start_idx = len(history_df)
        else:
            full_context = df.sort_values(by="dt").reset_index(drop=True)
            start_idx = 0

        # Pre-initialize output lists
        night_txns = []
        amt_zscores = []
        micro_txns = []
        dev_shared_counts = []
        ip_shared_counts = []
        cust_10m_counts = []
        dev_10m_counts = []
        ip_10m_counts = []
        graph_dev_degrees = []
        graph_cluster_sizes = []

        # Point-in-time graph accumulator
        G = nx.Graph()

        # Iterate point-in-time strictly forward
        for i in range(len(full_context)):
            row = full_context.iloc[i]
            cur_time = row["dt"]
            
            # Update historical bipartite graph with current transaction
            cust = f"cust:{row['customer_id']}"
            dev = f"dev:{row['device_id']}"
            ip = f"ip:{row['ip_address']}"
            G.add_edge(cust, dev)
            G.add_edge(cust, ip)
            if row.get("vpa"):
                G.add_edge(cust, f"vpa:{row['vpa']}")
                
            if i >= start_idx:
                # 1. Temporal night flag (1 AM - 5 AM IST)
                hour = cur_time.hour
                night_txns.append(1 if (1 <= hour <= 5) else 0)
                
                # 2. Historical MCC Z-Score (Zero leakage)
                mcc_key = str(row["mcc"])
                stats = self.mcc_stats.get(mcc_key, {"mean": 1000.0, "std": 500.0})
                zscore = (row["amount"] - stats["mean"]) / stats["std"]
                amt_zscores.append(float(zscore))
                
                # 3. Micro transaction indicator (< INR 100)
                micro_txns.append(1 if row["amount"] < 100.0 else 0)
                
                # 4. Strict past-only rolling 10m window
                window_10m = cur_time - pd.Timedelta(minutes=10)
                # Look strictly back in time
                past_window = full_context.iloc[:i]
                past_10m = past_window[past_window["dt"] >= window_10m]
                
                cust_10m_counts.append(int((past_10m["customer_id"] == row["customer_id"]).sum()))
                dev_10m_counts.append(int((past_10m["device_id"] == row["device_id"]).sum()))
                ip_10m_counts.append(int((past_10m["ip_address"] == row["ip_address"]).sum()))
                
                # 5. Point-in-time device/IP account sharing count
                dev_past_custs = past_window[past_window["device_id"] == row["device_id"]]["customer_id"].nunique()
                ip_past_custs = past_window[past_window["ip_address"] == row["ip_address"]]["customer_id"].nunique()
                dev_shared_counts.append(max(1, dev_past_custs))
                ip_shared_counts.append(max(1, ip_past_custs))
                
                # 6. Point-in-time graph metrics
                dev_deg = G.degree(dev) if dev in G else 1
                try:
                    comp = nx.node_connected_component(G, cust)
                    c_size = len(comp)
                except Exception:
                    c_size = 1
                graph_dev_degrees.append(dev_deg)
                graph_cluster_sizes.append(c_size)

        # Build feature DataFrame
        result_df = full_context.iloc[start_idx:].copy().reset_index(drop=True)
        result_df["is_night_txn"] = night_txns
        result_df["amt_mcc_zscore"] = amt_zscores
        result_df["is_micro_txn"] = micro_txns
        result_df["device_shared_cust_count"] = dev_shared_counts
        result_df["ip_shared_cust_count"] = ip_shared_counts
        result_df["cust_txn_count_10m"] = cust_10m_counts
        result_df["device_txn_count_10m"] = dev_10m_counts
        result_df["ip_txn_count_10m"] = ip_10m_counts
        result_df["graph_device_degree"] = graph_dev_degrees
        result_df["graph_cluster_size"] = graph_cluster_sizes
        
        # Payment method one-hot
        result_df["method_upi"] = (result_df["method"] == "upi").astype(int)
        result_df["method_card"] = (result_df["method"] == "card").astype(int)
        result_df["method_netbanking"] = (result_df["method"] == "netbanking").astype(int)
        
        feature_cols = [
            "amount",
            "account_age_days",
            "is_night_txn",
            "amt_mcc_zscore",
            "is_micro_txn",
            "device_shared_cust_count",
            "ip_shared_cust_count",
            "cust_txn_count_10m",
            "device_txn_count_10m",
            "ip_txn_count_10m",
            "graph_device_degree",
            "graph_cluster_size",
            "method_upi",
            "method_card",
            "method_netbanking"
        ]
        
        return result_df, feature_cols
