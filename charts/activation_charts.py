import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
from style_config import apply_common_style, PRIMARY_COLOR, HIGHLIGHT_COLOR, ACCENT_COLOR_1

@st.cache_data
def create_monthly_activation_chart(users_filtered, first_orders):
    """월별 활성화율 꺾은선 그래프를 생성합니다."""
    users_filtered["signup_month"] = users_filtered["created_at"].dt.to_period("M")
    merged = users_filtered.merge(first_orders, left_on="id", right_on="user_id", how="left")

    monthly_df = (
        merged.groupby("signup_month")
        .agg(total_users=("id","nunique"),
             activated_users=("first_order_month", lambda x: x.notna().sum())))
    monthly_df["activation_rate"] = monthly_df["activated_users"] / monthly_df["total_users"] * 100

    fig, ax = plt.subplots(figsize=(10,5))
    monthly_df["activation_rate"].plot(marker="o", ax=ax, color=PRIMARY_COLOR)
    plt.ylabel("Activation Rate (%)")
    plt.xlabel("Month")
    plt.xticks(rotation=45)
    apply_common_style(fig, ax, title="월별 활성화율 (%)")
    return monthly_df, fig

@st.cache_data
def create_activation_by_gender_chart(users_filtered):
    """성별 활성화율 막대그래프를 생성합니다."""
    gender_df = (
        users_filtered.groupby("gender")
        .agg(total_users=("id", "nunique"),
             activated_users=("activated", "sum"))
        .reset_index())
    gender_df["activation_rate"] = (gender_df["activated_users"] / gender_df["total_users"] * 100)

    fig, ax = plt.subplots(figsize=(5,4))
    bars = ax.bar(gender_df["gender"], gender_df["activation_rate"], color=HIGHLIGHT_COLOR)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha="center", va="bottom")
    ax.set_ylabel("Activation Rate (%)")
    apply_common_style(fig, ax, title="성별 활성화율")
    return gender_df, fig

@st.cache_data
def create_activation_by_traffic_source_chart(users_filtered):
    """유입 경로별 활성화율 막대그래프를 생성합니다."""
    channel_df = (
        users_filtered.groupby("traffic_source")
        .agg(total_users=("id", "nunique"),
             activated_users=("activated", "sum"))
        .reset_index())
    channel_df["activation_rate"] = (channel_df["activated_users"] / channel_df["total_users"] * 100)

    fig, ax = plt.subplots(figsize=(5,4))
    bars = ax.bar(channel_df["traffic_source"], channel_df["activation_rate"], color=PRIMARY_COLOR)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha="center", va="bottom")
    ax.set_ylabel("Activation Rate (%)")
    ax.set_xticklabels(channel_df["traffic_source"], rotation=45, ha="right")
    apply_common_style(fig, ax, title="유입 경로별 활성화율")
    return channel_df, fig

@st.cache_data
def create_activation_by_age_chart(users_filtered):
    """연령대별 활성화율 꺾은선 그래프를 생성합니다."""
    bins = [0, 20, 30, 40, 50, 60, 100]
    labels = ["<20", "20s", "30s", "40s", "50s", "60+"]
    users_filtered["age_group"] = pd.cut(users_filtered["age"], bins=bins, labels=labels, right=False)

    age_df = (
        users_filtered.groupby("age_group")
        .agg(total_users=("id", "nunique"),
             activated_users=("activated", "sum"))
        .reset_index()
    )
    age_df["activation_rate"] = (age_df["activated_users"] / age_df["total_users"] * 100)

    fig, ax = plt.subplots(figsize=(5,4))
    ax.plot(age_df["age_group"], age_df["activation_rate"], 
            marker="o", linestyle="-", color=ACCENT_COLOR_1)
    for i, val in enumerate(age_df["activation_rate"]):
        ax.text(i, val, f"{val:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Activation Rate (%)")
    apply_common_style(fig, ax, title="연령대별 활성화율")
    return age_df, fig

@st.cache_data
def create_first_purchase_category_chart(first_order_items):
    """첫 구매 카테고리 Top 5 막대그래프를 생성합니다."""
    if first_order_items.empty:
        return None, None
    
    category_counts = first_order_items["category"].value_counts().head(5)
    fig, ax = plt.subplots(figsize=(4,4))
    category_counts.plot(kind="bar", ax=ax, color=HIGHLIGHT_COLOR)
    ax.set_ylabel("Users")
    ax.set_xlabel("")
    for i, v in enumerate(category_counts):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    apply_common_style(fig, ax, title="첫 구매 카테고리 Top 5")
    return category_counts, fig

@st.cache_data
def create_ttfp_histogram(users_first_purchase):
    """첫 구매까지 걸린 시간(TTFP) 히스토그램을 생성합니다."""
    if users_first_purchase.empty:
        return None, None
        
    fig, ax = plt.subplots(figsize=(4,4))
    users_first_purchase["ttfp_days"].plot(
        kind="hist", bins=20, ax=ax, color=ACCENT_COLOR_1, alpha=0.7
    )
    ax.set_xlabel("Days")
    ax.set_ylabel("Users")
    apply_common_style(fig, ax, title="첫 구매까지 걸린 시간(일)")
    return users_first_purchase, fig