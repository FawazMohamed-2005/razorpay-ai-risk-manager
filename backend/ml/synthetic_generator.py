"""
Razorpay-Native Synthetic Transaction Generator (Interleaved & Realistic Time-Series)
"""

import os
import json
import random
import time
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

MERCHANTS = [
    {"merchant_id": "mer_zomato_blr", "mcc": "5812", "category": "Food & Dining", "avg_ticket": 450, "ticket_std": 200},
    {"merchant_id": "mer_swiggy_instamart", "mcc": "5411", "category": "Quick Commerce", "avg_ticket": 650, "ticket_std": 300},
    {"merchant_id": "mer_tanishq_online", "mcc": "5094", "category": "Luxury Jewelry", "avg_ticket": 45000, "ticket_std": 25000},
    {"merchant_id": "mer_flipkart_elec", "mcc": "5732", "category": "Electronics", "avg_ticket": 12000, "ticket_std": 8000},
    {"merchant_id": "mer_dream11_gaming", "mcc": "7995", "category": "Digital Gaming", "avg_ticket": 300, "ticket_std": 500},
    {"merchant_id": "mer_bookmyshow", "mcc": "7832", "category": "Entertainment", "avg_ticket": 850, "ticket_std": 400},
]

INDIAN_BANKS = ["HDFC", "ICICI", "SBIN", "UTIB", "KKBK", "YESB", "PUNB"]
VPA_HANDLES = ["okhdfcbank", "okaxis", "oksbi", "paytm", "ybl", "ibl"]
CITIES = ["Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad", "Jaipur"]

def generate_synthetic_dataset(num_records=2000, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    base_time = datetime(2026, 8, 20, 10, 0, 0)
    transactions = []
    
    # Generate continuous timeline over 10 days
    total_seconds = 10 * 86400
    
    legit_customers = [f"cust_legit_{i:04d}" for i in range(400)]
    legit_devices = [f"dev_fps_{uuid.uuid4().hex[:12]}" for _ in range(500)]
    legit_ips = [f"103.{random.randint(10, 250)}.{random.randint(1, 254)}.{random.randint(1, 254)}" for _ in range(350)]
    
    # 1. Base legitimate transactions
    num_legit = int(num_records * 0.78)
    for i in range(num_legit):
        cust_id = random.choice(legit_customers)
        dev_id = random.choice(legit_devices)
        ip_addr = random.choice(legit_ips)
        merchant = random.choice(MERCHANTS)
        
        method_roll = random.random()
        if method_roll < 0.72:
            method = "upi"
            bank = random.choice(INDIAN_BANKS)
            vpa = f"{cust_id.split('_')[-1]}@{random.choice(VPA_HANDLES)}"
            card_network, card_last4 = None, None
        elif method_roll < 0.92:
            method = "card"
            bank = random.choice(INDIAN_BANKS)
            vpa = None
            card_network = random.choice(["VISA", "MasterCard", "RuPay"])
            card_last4 = f"{random.randint(1000, 9999)}"
        else:
            method = "netbanking"
            bank = random.choice(INDIAN_BANKS)
            vpa = None
            card_network, card_last4 = None, None
            
        amount = max(60.0, float(np.random.normal(merchant["avg_ticket"], merchant["ticket_std"])))
        amount = round(amount, 2)
        
        txn_time = base_time + timedelta(seconds=random.randint(0, total_seconds))
        
        transactions.append({
            "payment_id": f"pay_syn_{uuid.uuid4().hex[:14]}",
            "timestamp": txn_time.isoformat(),
            "customer_id": cust_id,
            "merchant_id": merchant["merchant_id"],
            "mcc": merchant["mcc"],
            "category": merchant["category"],
            "amount": amount,
            "currency": "INR",
            "method": method,
            "bank": bank,
            "vpa": vpa,
            "card_network": card_network,
            "card_last4": card_last4,
            "device_id": dev_id,
            "ip_address": ip_addr,
            "location_city": random.choice(CITIES),
            "account_age_days": random.randint(45, 800),
            "user_chargeback_count": 0,
            "is_fraud": 0,
            "fraud_type": "LEGITIMATE",
            "is_adversarial_edge_case": False
        })
        
    # 2. Abuse Rings (Multiple waves across Day 1 to Day 9)
    for wave in range(4):
        ring_dev = f"dev_fps_syndicate_wave_{wave}"
        ring_ip_sub = f"45.112.{80 + wave}."
        ring_start = base_time + timedelta(days=wave * 2 + 1, hours=random.randint(10, 20))
        
        for k in range(35):
            cust_id = f"cust_ring_{wave}_{k % 8:02d}"
            ip_addr = f"{ring_ip_sub}{random.randint(10, 40)}"
            merchant = random.choice([m for m in MERCHANTS if m["mcc"] in ["7995", "5732", "5411"]])
            txn_time = ring_start + timedelta(seconds=k * 20 + random.randint(1, 8))
            amount = round(random.uniform(3500, 9500), 2)
            
            transactions.append({
                "payment_id": f"pay_syn_{uuid.uuid4().hex[:14]}",
                "timestamp": txn_time.isoformat(),
                "customer_id": cust_id,
                "merchant_id": merchant["merchant_id"],
                "mcc": merchant["mcc"],
                "category": merchant["category"],
                "amount": amount,
                "currency": "INR",
                "method": "upi",
                "bank": "SBIN",
                "vpa": f"ring_bot_{k%5}@{random.choice(VPA_HANDLES)}",
                "card_network": None,
                "card_last4": None,
                "device_id": ring_dev,
                "ip_address": ip_addr,
                "location_city": "Mumbai",
                "account_age_days": random.randint(1, 3),
                "user_chargeback_count": 0,
                "is_fraud": 1,
                "fraud_type": "ABUSE_RING_COORDINATED",
                "is_adversarial_edge_case": False
            })

    # 3. Carding Micro-Probing Spikes (Multiple waves)
    for wave in range(3):
        carding_start = base_time + timedelta(days=wave * 3 + 2, hours=random.randint(1, 4))
        for c in range(35):
            cust_id = f"cust_carder_w{wave}_{c // 8}"
            dev_id = f"dev_carding_box_{wave}_{c // 12}"
            ip_addr = f"185.220.101.{c % 6}"
            merchant = random.choice([m for m in MERCHANTS if m["mcc"] in ["5812", "7995"]])
            txn_time = carding_start + timedelta(seconds=c * 6 + random.randint(1, 3))
            amount = round(random.uniform(12.0, 85.0), 2)
            
            transactions.append({
                "payment_id": f"pay_syn_{uuid.uuid4().hex[:14]}",
                "timestamp": txn_time.isoformat(),
                "customer_id": cust_id,
                "merchant_id": merchant["merchant_id"],
                "mcc": merchant["mcc"],
                "category": merchant["category"],
                "amount": amount,
                "currency": "INR",
                "method": "card",
                "bank": "HDFC",
                "vpa": None,
                "card_network": "VISA",
                "card_last4": f"44{c % 10:02d}",
                "device_id": dev_id,
                "ip_address": ip_addr,
                "location_city": "Bengaluru",
                "account_age_days": 1,
                "user_chargeback_count": 0,
                "is_fraud": 1,
                "fraud_type": "VELOCITY_CARDING_SPIKE",
                "is_adversarial_edge_case": False
            })

    # 4. Account Takeovers (Spaced across timeline)
    for a in range(60):
        cust_id = f"cust_legit_{a * 4:04d}"
        dev_id = f"dev_hijack_new_{a}"
        ip_addr = f"194.38.20.{a % 15}"
        merchant = next(m for m in MERCHANTS if m["mcc"] == "5094")
        txn_time = base_time + timedelta(days=random.randint(1, 9), hours=random.randint(1, 5), minutes=random.randint(0, 59))
        amount = round(random.uniform(55000, 115000), 2)
        
        transactions.append({
            "payment_id": f"pay_syn_{uuid.uuid4().hex[:14]}",
            "timestamp": txn_time.isoformat(),
            "customer_id": cust_id,
            "merchant_id": merchant["merchant_id"],
            "mcc": merchant["mcc"],
            "category": merchant["category"],
            "amount": amount,
            "currency": "INR",
            "method": "netbanking",
            "bank": "HDFC",
            "vpa": None,
            "card_network": None,
            "card_last4": None,
            "device_id": dev_id,
            "ip_address": ip_addr,
            "location_city": "Delhi NCR",
            "account_age_days": 450,
            "user_chargeback_count": 0,
            "is_fraud": 1,
            "fraud_type": "ACCOUNT_TAKEOVER_SPIKE",
            "is_adversarial_edge_case": False
        })

    # 5. VIP Flash-Sale Edge Cases (High velocity, high amount, but trusted VIP device)
    for wave in range(2):
        vip_cust = f"cust_vip_powerbuyer_{wave}"
        vip_dev = f"dev_fps_apple_vip_pro_{wave}"
        flash_time = base_time + timedelta(days=wave * 4 + 3, hours=14, minutes=0)
        
        for v in range(25):
            merchant = next(m for m in MERCHANTS if m["mcc"] == "5732")
            txn_time = flash_time + timedelta(minutes=v * 2)
            amount = round(random.uniform(28000, 52000), 2)
            
            transactions.append({
                "payment_id": f"pay_syn_vip_{wave}_{uuid.uuid4().hex[:8]}",
                "timestamp": txn_time.isoformat(),
                "customer_id": vip_cust,
                "merchant_id": merchant["merchant_id"],
                "mcc": merchant["mcc"],
                "category": merchant["category"],
                "amount": amount,
                "currency": "INR",
                "method": "upi",
                "bank": "HDFC",
                "vpa": f"vip.{wave}@okhdfcbank",
                "card_network": None,
                "card_last4": None,
                "device_id": vip_dev,
                "ip_address": f"122.172.85.{wave*10 + 5}",
                "location_city": "Bengaluru",
                "account_age_days": 950,
                "user_chargeback_count": 0,
                "is_fraud": 0,
                "fraud_type": "VIP_FLASH_SALE_BURST",
                "is_adversarial_edge_case": True
            })
            
    df = pd.DataFrame(transactions)
    df["dt"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by="dt").reset_index(drop=True)
    df["timestamp"] = df["dt"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.drop(columns=["dt"])
    
    return df

if __name__ == "__main__":
    df = generate_synthetic_dataset(2000)
    print(f"Generated {len(df)} transactions.")
    print(f"Fraud distribution:\n{df['fraud_type'].value_counts()}")
    output_path = os.path.join(os.path.dirname(__file__), "transactions.json")
    df.to_json(output_path, orient="records", indent=2)
    print(f"Saved to {output_path}")
