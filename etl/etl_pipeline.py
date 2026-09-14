"""
etl_pipeline.py
----------------
Transforms raw event-level data into analysis-ready tables:
  1. funnel_by_category   - view -> cart -> checkout -> purchase, by category
  2. funnel_by_device     - same funnel, by device
  3. cohort_retention      - monthly signup cohorts x months-since-signup retention matrix
  4. monthly_kpis          - AOV, CAC, repeat purchase rate, return rate, revenue by month
  5. channel_cac           - CAC and revenue per acquisition channel

Run: python etl/etl_pipeline.py
Reads from ../data/*.csv, writes processed tables to ../data/processed/
"""

import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
PROC_DIR = os.path.join(DATA_DIR, "processed")
os.makedirs(PROC_DIR, exist_ok=True)


def load_raw():
    users = pd.read_csv(os.path.join(DATA_DIR, "users.csv"), parse_dates=["signup_date"])
    events = pd.read_csv(os.path.join(DATA_DIR, "raw_events.csv"), parse_dates=["event_date"])
    spend = pd.read_csv(os.path.join(DATA_DIR, "marketing_spend.csv"))
    return users, events, spend


def build_funnel(events, group_col):
    stages = ["view", "add_to_cart", "checkout", "purchase"]
    counts = events[events["event_type"].isin(stages)].groupby([group_col, "event_type"]).size().unstack(fill_value=0)
    counts = counts.reindex(columns=stages, fill_value=0)
    conv = pd.DataFrame(index=counts.index)
    conv["view"] = counts["view"]
    conv["add_to_cart"] = counts["add_to_cart"]
    conv["checkout"] = counts["checkout"]
    conv["purchase"] = counts["purchase"]
    conv["view_to_cart_%"] = (conv["add_to_cart"] / conv["view"] * 100).round(1)
    conv["cart_to_checkout_%"] = (conv["checkout"] / conv["add_to_cart"] * 100).round(1)
    conv["checkout_to_purchase_%"] = (conv["purchase"] / conv["checkout"] * 100).round(1)
    conv["overall_view_to_purchase_%"] = (conv["purchase"] / conv["view"] * 100).round(2)
    return conv.reset_index()


def build_cohort_retention(users, events):
    purchases = events[events["event_type"] == "purchase"].merge(
        users[["user_id", "signup_month"]], on="user_id", how="left"
    )
    purchases["purchase_month"] = purchases["event_date"].dt.to_period("M")
    purchases["signup_period"] = pd.PeriodIndex(purchases["signup_month"], freq="M")
    purchases["months_since_signup"] = (
        (purchases["purchase_month"].dt.year - purchases["signup_period"].dt.year) * 12
        + (purchases["purchase_month"].dt.month - purchases["signup_period"].dt.month)
    )
    purchases = purchases[purchases["months_since_signup"] >= 0]

    cohort_sizes = users.groupby("signup_month")["user_id"].nunique()

    retention = (
        purchases.groupby(["signup_month", "months_since_signup"])["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "active_users"})
    )
    retention = retention.merge(cohort_sizes.rename("cohort_size"), on="signup_month")
    retention["retention_%"] = (retention["active_users"] / retention["cohort_size"] * 100).round(1)

    pivot = retention.pivot(index="signup_month", columns="months_since_signup", values="retention_%")
    return pivot.sort_index()


def build_monthly_kpis(users, events, spend):
    purchases = events[events["event_type"] == "purchase"].copy()
    purchases["month"] = purchases["event_date"].dt.to_period("M").astype(str)

    revenue = purchases.groupby("month")["order_value"].sum().rename("revenue_inr")
    orders = purchases.groupby("month").size().rename("orders")
    aov = (revenue / orders).round(2).rename("aov_inr")
    return_rate = (purchases.groupby("month")["returned"].mean() * 100).round(2).rename("return_rate_%")

    # repeat purchase rate: % of purchasing users in a month who have >1 lifetime order by that month
    purchases_sorted = purchases.sort_values("event_date")
    purchases_sorted["order_rank"] = purchases_sorted.groupby("user_id").cumcount() + 1
    repeat = purchases_sorted.groupby("month").apply(
        lambda df: (df["order_rank"] > 1).mean() * 100
    ).round(2).rename("repeat_purchase_rate_%")

    new_users = users.groupby("signup_month")["user_id"].nunique().rename("new_users")
    monthly_spend = spend.groupby("month")["spend_inr"].sum().rename("total_spend_inr")
    cac = (monthly_spend / new_users).round(2).rename("cac_inr")

    kpis = pd.concat([revenue, orders, aov, return_rate, repeat, new_users, monthly_spend, cac], axis=1)
    kpis = kpis.sort_index()
    return kpis.reset_index().rename(columns={"index": "month"})


def build_channel_cac(users, events, spend):
    purchases = events[events["event_type"] == "purchase"].merge(
        users[["user_id", "acquisition_channel"]], on="user_id", how="left"
    )
    revenue_by_channel = purchases.groupby("acquisition_channel")["order_value"].sum().rename("revenue_inr")
    users_by_channel = users.groupby("acquisition_channel")["user_id"].nunique().rename("acquired_users")
    spend_by_channel = spend.groupby("channel")["spend_inr"].sum().rename("total_spend_inr")
    df = pd.concat([users_by_channel, spend_by_channel, revenue_by_channel], axis=1)
    df["cac_inr"] = (df["total_spend_inr"] / df["acquired_users"]).round(2)
    df["revenue_per_user_inr"] = (df["revenue_inr"] / df["acquired_users"]).round(2)
    df["roi_x"] = (df["revenue_per_user_inr"] / df["cac_inr"]).round(2)
    return df.reset_index().rename(columns={"index": "acquisition_channel"})


if __name__ == "__main__":
    users, events, spend = load_raw()

    funnel_category = build_funnel(events, "category")
    funnel_device = build_funnel(events, "device")
    cohort_retention = build_cohort_retention(users, events)
    monthly_kpis = build_monthly_kpis(users, events, spend)
    channel_cac = build_channel_cac(users, events, spend)

    funnel_category.to_csv(os.path.join(PROC_DIR, "funnel_by_category.csv"), index=False)
    funnel_device.to_csv(os.path.join(PROC_DIR, "funnel_by_device.csv"), index=False)
    cohort_retention.to_csv(os.path.join(PROC_DIR, "cohort_retention.csv"))
    monthly_kpis.to_csv(os.path.join(PROC_DIR, "monthly_kpis.csv"), index=False)
    channel_cac.to_csv(os.path.join(PROC_DIR, "channel_cac.csv"), index=False)

    print("ETL complete. Processed tables written to data/processed/")
    print("\n--- Funnel by category ---")
    print(funnel_category.to_string(index=False))
    print("\n--- Channel CAC / ROI ---")
    print(channel_cac.to_string(index=False))
