"""
generate_data.py
-----------------
Generates a synthetic but statistically realistic fashion e-commerce dataset
that mimics user behavior on a platform like Myntra: sessions, funnel events
(view -> add_to_cart -> checkout -> purchase), returns, marketing spend, and
signup cohorts.

Output: data/raw_events.csv, data/users.csv, data/marketing_spend.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

np.random.seed(42)

OUT_DIR = os.path.dirname(__file__)

N_USERS = 8000
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)
CATEGORIES = ["Ethnic Wear", "Western Wear", "Footwear", "Accessories", "Beauty", "Kids"]
DEVICES = ["Mobile App", "Mobile Web", "Desktop"]
REGIONS = ["North", "South", "East", "West"]

# ---------- Users & signup cohorts ----------
def generate_users(n_users):
    signup_days = np.random.randint(0, (END_DATE - START_DATE).days, size=n_users)
    signup_dates = [START_DATE + timedelta(days=int(d)) for d in signup_days]
    region = np.random.choice(REGIONS, size=n_users, p=[0.28, 0.32, 0.18, 0.22])
    device_pref = np.random.choice(DEVICES, size=n_users, p=[0.62, 0.23, 0.15])
    acquisition_channel = np.random.choice(
        ["Paid Social", "Organic Search", "Referral", "Influencer", "Email/Push"],
        size=n_users, p=[0.34, 0.28, 0.14, 0.16, 0.08]
    )
    users = pd.DataFrame({
        "user_id": [f"U{100000+i}" for i in range(n_users)],
        "signup_date": signup_dates,
        "region": region,
        "device_pref": device_pref,
        "acquisition_channel": acquisition_channel,
    })
    users["signup_month"] = pd.to_datetime(users["signup_date"]).dt.to_period("M").astype(str)
    return users


def generate_events(users):
    """
    For each user, simulate a number of sessions after signup.
    Each session progresses through the funnel with category-dependent
    drop-off probabilities, and purchases have a category-dependent return rate.
    """
    # Category-level base conversion behavior (calibrated so overall funnel
    # looks like a realistic fashion e-commerce platform)
    cat_view_to_cart = {"Ethnic Wear": 0.38, "Western Wear": 0.34, "Footwear": 0.30,
                         "Accessories": 0.27, "Beauty": 0.31, "Kids": 0.29}
    cat_cart_to_checkout = {"Ethnic Wear": 0.55, "Western Wear": 0.50, "Footwear": 0.46,
                             "Accessories": 0.52, "Beauty": 0.58, "Kids": 0.48}
    cat_checkout_to_purchase = {"Ethnic Wear": 0.72, "Western Wear": 0.68, "Footwear": 0.63,
                                 "Accessories": 0.75, "Beauty": 0.78, "Kids": 0.70}
    # Higher for size-dependent categories -> this is the seed for Project 2's problem
    cat_return_rate = {"Ethnic Wear": 0.16, "Western Wear": 0.22, "Footwear": 0.27,
                        "Accessories": 0.06, "Beauty": 0.04, "Kids": 0.13}

    rows = []
    for _, u in users.iterrows():
        max_days_active = (END_DATE - pd.to_datetime(u["signup_date"])).days
        if max_days_active <= 0:
            continue
        # Engagement decays with an exponential-ish distribution of session counts
        n_sessions = np.random.poisson(lam=3.2)
        n_sessions = min(n_sessions, 25)

        for s in range(n_sessions):
            day_offset = np.random.randint(0, max_days_active + 1)
            session_date = pd.to_datetime(u["signup_date"]) + timedelta(days=int(day_offset))
            category = np.random.choice(CATEGORIES)
            device = np.random.choice(DEVICES, p=[0.62, 0.23, 0.15]) if np.random.rand() < 0.85 else u["device_pref"]

            # Funnel progression
            rows.append([u["user_id"], session_date, category, device, "view"])
            if np.random.rand() < cat_view_to_cart[category]:
                rows.append([u["user_id"], session_date, category, device, "add_to_cart"])
                if np.random.rand() < cat_cart_to_checkout[category]:
                    rows.append([u["user_id"], session_date, category, device, "checkout"])
                    if np.random.rand() < cat_checkout_to_purchase[category]:
                        order_value = float(np.round(np.random.gamma(shape=3.2, scale=550), 2))
                        returned = np.random.rand() < cat_return_rate[category]
                        rows.append([u["user_id"], session_date, category, device,
                                     f"purchase|{order_value}|{int(returned)}"])

    events = pd.DataFrame(rows, columns=["user_id", "event_date", "category", "device", "event_raw"])

    # Expand the purchase-encoded rows into proper columns
    def parse_event(e):
        if e.startswith("purchase"):
            _, ov, ret = e.split("|")
            return "purchase", float(ov), int(ret)
        return e, np.nan, np.nan

    parsed = events["event_raw"].apply(parse_event)
    events["event_type"] = parsed.apply(lambda x: x[0])
    events["order_value"] = parsed.apply(lambda x: x[1])
    events["returned"] = parsed.apply(lambda x: x[2])
    events.drop(columns=["event_raw"], inplace=True)
    return events


def generate_marketing_spend():
    """Monthly marketing spend by channel, used to compute CAC."""
    months = pd.period_range(START_DATE, END_DATE, freq="M").astype(str)
    channels = ["Paid Social", "Organic Search", "Referral", "Influencer", "Email/Push"]
    base_spend = {"Paid Social": 900000, "Organic Search": 150000, "Referral": 80000,
                  "Influencer": 400000, "Email/Push": 60000}
    rows = []
    for m in months:
        for c in channels:
            noise = np.random.uniform(0.85, 1.2)
            rows.append([m, c, round(base_spend[c] * noise, 2)])
    return pd.DataFrame(rows, columns=["month", "channel", "spend_inr"])


if __name__ == "__main__":
    print("Generating users...")
    users = generate_users(N_USERS)
    print("Generating events (this simulates the full funnel, may take ~10-20s)...")
    events = generate_events(users)
    print("Generating marketing spend...")
    spend = generate_marketing_spend()

    users.to_csv(os.path.join(OUT_DIR, "users.csv"), index=False)
    events.to_csv(os.path.join(OUT_DIR, "raw_events.csv"), index=False)
    spend.to_csv(os.path.join(OUT_DIR, "marketing_spend.csv"), index=False)

    print(f"Users: {len(users)} | Events: {len(events)} | Spend rows: {len(spend)}")
    print("Saved to data/users.csv, data/raw_events.csv, data/marketing_spend.csv")
