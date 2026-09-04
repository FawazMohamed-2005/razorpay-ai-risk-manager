"""
Model Trainer & Evaluator for Razorpay Sentinel
Implements strict temporal train/test split, zero-leakage feature pipeline,
SMOTE balancing, XGBoost training, and honest financial/operational metrics.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
)
from features import FeaturePipeline

def train_and_evaluate():
    data_path = os.path.join(os.path.dirname(__file__), "transactions.json")
    df_raw = pd.read_json(data_path)
    df_raw["dt"] = pd.to_datetime(df_raw["timestamp"])
    df_raw = df_raw.sort_values(by="dt").reset_index(drop=True)
    
    # 1. 70/30 Temporal Split (Simulating real-world future deployment)
    split_idx = int(len(df_raw) * 0.70)
    train_raw = df_raw.iloc[:split_idx].copy()
    test_raw = df_raw.iloc[split_idx:].copy()
    
    print(f"Training set: {len(train_raw)} txns (Fraud: {train_raw['is_fraud'].sum()})")
    print(f"Held-out test set: {len(test_raw)} txns (Fraud: {test_raw['is_fraud'].sum()})")
    
    # 2. Fit feature pipeline strictly on train_raw (NO leakage)
    pipeline = FeaturePipeline()
    pipeline.fit(train_raw)
    
    # Extract features for training set
    train_df, feature_cols = pipeline.extract_point_in_time_features(train_raw)
    # Extract features for test set using train_raw as historical context strictly in the past
    test_df, _ = pipeline.extract_point_in_time_features(test_raw, history_df=train_raw)
    
    X_train = train_df[feature_cols]
    y_train = train_df["is_fraud"]
    
    X_test = test_df[feature_cols]
    y_test = test_df["is_fraud"]
    
    # 3. SMOTE Oversampling on training set ONLY
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    
    # 4. Train XGBoost Classifier
    model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="logloss"
    )
    model.fit(X_train_res, y_train_res)
    
    # 5. Predict probabilities on held-out test set
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.50).astype(int)
    
    # Calculate Core Metrics
    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    test_df["pred_prob"] = y_prob
    test_df["pred_label"] = y_pred
    
    # Financial Cost Ledger Calculation
    fraud_amount_prevented = float(test_df[(test_df["is_fraud"] == 1) & (test_df["pred_label"] == 1)]["amount"].sum())
    fraud_amount_missed = float(test_df[(test_df["is_fraud"] == 1) & (test_df["pred_label"] == 0)]["amount"].sum())
    false_positive_gmv_blocked = float(test_df[(test_df["is_fraud"] == 0) & (test_df["pred_label"] == 1)]["amount"].sum())
    estimated_fp_friction_cost = float(fp * 350.0) # INR 350 friction/support cost per false block
    
    net_fraud_savings = fraud_amount_prevented - (false_positive_gmv_blocked * 0.02) - estimated_fp_friction_cost
    
    metrics = {
        "held_out_test_records": len(test_df),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "financial_cost_ledger": {
            "fraud_amount_prevented_inr": round(fraud_amount_prevented, 2),
            "fraud_amount_missed_inr": round(fraud_amount_missed, 2),
            "false_positive_gmv_impact_inr": round(false_positive_gmv_blocked, 2),
            "estimated_fp_friction_cost_inr": round(estimated_fp_friction_cost, 2),
            "net_business_savings_inr": round(net_fraud_savings, 2)
        },
        "feature_importances": dict(zip(feature_cols, [round(float(v), 4) for v in model.feature_importances_]))
    }
    
    output_dir = os.path.dirname(__file__)
    joblib.dump(model, os.path.join(output_dir, "xgboost_sentinel.joblib"))
    joblib.dump(pipeline, os.path.join(output_dir, "feature_pipeline.joblib"))
    joblib.dump(feature_cols, os.path.join(output_dir, "feature_cols.joblib"))
    
    with open(os.path.join(output_dir, "evaluation_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("Model training & zero-leakage evaluation complete!")
    print(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    train_and_evaluate()
