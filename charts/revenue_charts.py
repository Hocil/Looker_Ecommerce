import streamlit as st
import matplotlib.pyplot as plt
import math
import textwrap
import koreanize_matplotlib
from style_config import apply_common_style, PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR_1, HIGHLIGHT_COLOR

@st.cache_data
def create_monthly_revenue_chart(order_items_filtered):
    """월별 매출 추이 꺾은선 그래프를 생성합니다."""
    if order_items_filtered.empty:
        return None

    monthly_revenue = (
        order_items_filtered
        .groupby(order_items_filtered["created_at"].dt.to_period("M"))["sale_price"].sum().reset_index())
    monthly_revenue["created_at"] = monthly_revenue["created_at"].dt.to_timestamp()

    fig, ax = plt.subplots(figsize=(8,4), dpi=80)
    ax.plot(monthly_revenue["created_at"], monthly_revenue["sale_price"], marker="o", linestyle="-", color=PRIMARY_COLOR)
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($)")
    for i, v in enumerate(monthly_revenue["sale_price"]):
        ax.text(monthly_revenue["created_at"].iloc[i], v + (v*0.05), f"${v:,.0f}", ha="center", fontsize=8)
    apply_common_style(fig, ax, title="월별 매출 추이")
    return fig

@st.cache_data
def create_purchase_frequency_chart(order_items_filtered):
    """구매 횟수별 사용자 분포 막대그래프를 생성합니다."""
    if order_items_filtered.empty:
        return None
    
    user_order_counts = order_items_filtered.groupby("user_id")["order_id"].nunique().reset_index()
    user_order_counts.rename(columns={"order_id": "num_orders"}, inplace=True)
    purchase_freq = user_order_counts["num_orders"].value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(5,4))
    if not purchase_freq.empty:
        purchase_freq.plot(kind="bar", ax=ax, color=HIGHLIGHT_COLOR)
        ax.set_xlabel("Number of Orders")
        ax.set_ylabel("Number of Users")
        for i, v in enumerate(purchase_freq):
            ax.text(i, v + 1, str(v), ha="center", fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=0)
        apply_common_style(fig, ax, title="구매 횟수별 사용자 분포")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
    return fig

@st.cache_data
def create_revenue_contribution_chart(order_items_filtered):
    """상위 10% 고객의 매출 기여도 파이 차트를 생성합니다."""
    if order_items_filtered.empty:
        return None

    user_revenue = order_items_filtered.groupby("user_id")["sale_price"].sum().reset_index().sort_values("sale_price", ascending=False).reset_index(drop=True)
    total_rev_users = user_revenue["sale_price"].sum()
    top_10pct_count = max(1, math.ceil(len(user_revenue) * 0.10)) if len(user_revenue) > 0 else 0
    top_10pct_revenue = user_revenue.head(top_10pct_count)["sale_price"].sum()

    fig, ax = plt.subplots(figsize=(5,4))
    if top_10pct_count > 0 and total_rev_users > 0:
        labels = ["Top 10%", "Others"]
        values = [top_10pct_revenue, total_rev_users - top_10pct_revenue]
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=[SECONDARY_COLOR,"lightgrey"])
        apply_common_style(fig, ax, title="매출 기여도 (상위 10% vs 기타)")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
    return fig

@st.cache_data
def create_revenue_distribution_chart(order_items_filtered):
    """사용자별 매출 분포 히스토그램을 생성합니다."""
    if order_items_filtered.empty:
        return None
    
    user_revenue = order_items_filtered.groupby("user_id")["sale_price"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(5,4))
    if not user_revenue.empty:
        ax.hist(user_revenue["sale_price"], bins=20, color=ACCENT_COLOR_1, alpha=0.7)
        ax.set_xlabel("Revenue per User ($)")
        ax.set_ylabel("Number of Users")
        apply_common_style(fig, ax, title="사용자별 매출 분포")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.axis("off")
    return fig

@st.cache_data
def create_top_revenue_chart(order_items_merged, by='category'):
    """카테고리 또는 상품별 상위 10개 매출 막대그래프를 생성합니다."""
    if order_items_merged.empty:
        return None

    group_col = 'category' if by == 'category' else 'name'
    color = PRIMARY_COLOR if by == 'category' else SECONDARY_COLOR
    title = "카테고리별 매출 Top 10" if by == 'category' else "상품별 매출 Top 10"

    rev_plot = order_items_merged.groupby(group_col)["sale_price"].sum().sort_values(ascending=False).head(10).copy()
    rev_plot.index = [textwrap.shorten(str(c), width=25, placeholder="...") for c in rev_plot.index]

    fig, ax = plt.subplots(figsize=(5,4))
    if not rev_plot.empty:
        rev_plot.plot(kind="barh", ax=ax, color=color)
        ax.set_xlabel("Revenue ($)")
        ax.invert_yaxis()
        ax.tick_params(axis='y', labelsize=8)
        for i, v in enumerate(rev_plot):
            ax.text(v, i, f"${v:,.0f}", va="center", fontsize=8)
        apply_common_style(fig, ax, title=title)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center"); ax.axis("off")
    return fig

@st.cache_data
def create_category_aov_chart(order_items_merged):
    """카테고리별 객단가(AOV) 막대그래프를 생성합니다."""
    if order_items_merged.empty:
        return None
    
    cat_rev_full = order_items_merged.groupby("category")["sale_price"].sum()
    cat_ord_full = order_items_merged.groupby("category")["order_id"].nunique()
    cat_aov_full = (cat_rev_full / cat_ord_full).dropna()
    cat_aov_plot = cat_aov_full.sort_values(ascending=False).head(10).copy()
    cat_aov_plot.index = [textwrap.shorten(str(c), width=25, placeholder="...") for c in cat_aov_plot.index]

    fig, ax = plt.subplots(figsize=(5,4))
    if not cat_aov_plot.empty:
        cat_aov_plot.plot(kind="bar", ax=ax, color=ACCENT_COLOR_1)
        ax.set_ylabel("AOV ($)")
        for i, v in enumerate(cat_aov_plot):
            ax.text(i, v + (v*0.02), f"${v:,.0f}", ha="center", fontsize=8)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        apply_common_style(fig, ax, title="카테고리별 객단가(AOV)")
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center"); ax.axis("off")
    return fig