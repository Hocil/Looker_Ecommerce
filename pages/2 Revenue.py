import streamlit as st
import pandas as pd
import koreanize_matplotlib
import matplotlib.pyplot as plt
from data import load_all_data
from charts.revenue_charts import (
    create_monthly_revenue_chart,
    create_purchase_frequency_chart,
    create_revenue_contribution_chart,
    create_revenue_distribution_chart,
    create_top_revenue_chart,
    create_category_aov_chart
)
# ---------------- 페이지 기본 설정 ----------------
st.set_page_config(
    page_title="💰 Revenue 분석",
    layout="wide"
)

# 제목, 설명 (title)
st.title("💰 매출(Revenue) 분석")
st.write("매출 관련 주요 지표(KPI) 및 트렌드를 분석합니다.")

all_data = load_all_data()
users = all_data["users"]
products = all_data["products"]
orders = all_data["orders"]
order_items = all_data["order_items"]

# ---------------- 사이드바 ----------------
st.sidebar.header("Filters")

## 1. 기간 필터
selected_year = st.sidebar.selectbox("Year", [2023])
selected_months = st.sidebar.multiselect(
    "Month",
    options=list(range(1, 13)),
    default=list(range(1, 13))
)

## 2. 주문 상태 필터
status_filter = st.sidebar.multiselect(
    "Order Status",
    options=orders["status"].unique().tolist(),
    default="Complete" )

## 3. 사용자 필터
gender_filter = st.sidebar.selectbox("Gender", ["All", "M", "F"])

# 연령대 구간 정의
age_bins = [0, 20, 30, 40, 50, 60, 100]
age_labels = ["<20", "20s", "30s", "40s", "50s", "60+"]
users["age_group"] = pd.cut(users["age"], bins=age_bins, labels=age_labels, right=False)

age_filter = st.sidebar.multiselect(
    "Age Group",
    options=age_labels,
    default=age_labels)

traffic_filter = st.sidebar.multiselect(
    "Traffic Source",
    options=users["traffic_source"].dropna().unique().tolist(),
    default=users["traffic_source"].dropna().unique().tolist())

## 4. 상품 필터
category_filter = st.sidebar.multiselect(
    "Category",
    options=products["category"].unique().tolist(),
    default=products["category"].unique().tolist())

brand_filter = st.sidebar.multiselect(
    "Brand",
    options=products["brand"].unique().tolist(),
    default=products["brand"].unique().tolist())


# ---------------- 필터 적용 ----------------
# 1) 기간 필터 적용
orders["year"] = pd.to_datetime(orders["created_at"]).dt.year
orders["month"] = pd.to_datetime(orders["created_at"]).dt.month
orders_filtered = orders[
    (orders["year"] == selected_year) &
    (orders["month"].isin(selected_months)) &
    (orders["status"].isin(status_filter))]

# 2) 사용자 필터 적용
users_filtered = users.copy()
if gender_filter != "All":
    users_filtered = users_filtered[users_filtered["gender"] == gender_filter]
users_filtered = users_filtered[
    (users_filtered["age_group"].isin(age_filter)) &
    (users_filtered["traffic_source"].isin(traffic_filter))]

# 3) 상품 필터 적용
products_filtered = products[
    (products["category"].isin(category_filter)) &
    (products["brand"].isin(brand_filter))]



# 4) order_items 필터 적용
order_items_filtered = order_items[
    order_items["order_id"].isin(orders_filtered["order_id"])]
order_items_filtered = order_items_filtered[
    order_items_filtered["product_id"].isin(products_filtered["id"])]
order_items_filtered = order_items_filtered[
    order_items_filtered["user_id"].isin(users_filtered["id"])]


# ---------------- KPI 계산 ----------------
# 모든 KPI를 order_items_filtered 기준으로 (필터 일관성)
total_revenue = order_items_filtered["sale_price"].sum()
total_orders = order_items_filtered["order_id"].nunique()
purchasing_users = order_items_filtered["user_id"].nunique()

# 전체 유저 수 (필터 반영된 users 기준)
total_users = users_filtered["id"].nunique()

# ARPU / ARPPU / AOV
arpu = total_revenue / total_users if total_users > 0 else 0
arppu = total_revenue / purchasing_users if purchasing_users > 0 else 0
aov = total_revenue / total_orders if total_orders > 0 else 0


# ---------------- KPI 카드 표시 ----------------
st.subheader("Revenue KPI 개요")
st.write("선택한 필터 조건에 따른 핵심 매출 지표입니다. 총 매출, 주문 수, 구매자 수와 같은 규모 지표와 ARPU, ARPPU, AOV와 같은 효율 지표를 포함합니다.")

# 윗줄 (규모 지표)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue (총 매출)", f"${total_revenue:,.2f}")
    # st.metric("Total Revenue", f"${current_rev:,.2f}", f"{delta_rev:+.2f}%")
with col2:
    st.metric("Total Orders (총 주문 수)", f"{total_orders:,}")
with col3:
    st.metric("Purchasing Users (총 구매자 수)", f"{purchasing_users:,}")

# 아랫줄 (효율 지표)
col4, col5, col6 = st.columns(3)
with col4:
    st.metric("ARPU (Average Revenue Per User)", f"${arpu:,.2f}")
with col5:
    st.metric("ARPPU (Average Revenue Per Paying User)", f"${arppu:,.2f}")
with col6:
    st.metric("AOV (Average Order Value, 객단가)", f"${aov:,.2f}")



# ---------------- 시간 흐름별 매출 추이 ----------------
st.subheader("Monthly Revenue Trend (시간 흐름별 매출 추이)")
st.write("선택한 기간 동안의 월별 총 매출 변화 추이를 보여줍니다. 계절적 요인이나 마케팅 활동에 따른 매출 변화를 파악할 수 있습니다.")

monthly_revenue_fig = create_monthly_revenue_chart(order_items_filtered)
if monthly_revenue_fig:
    st.pyplot(monthly_revenue_fig)
else:
    st.warning("매출 추이 데이터를 표시할 수 없습니다.")



# ---------------- 구매 빈도 & 고객 분포 ----------------
st.subheader("Purchase Frequency & Customer Distribution (구매빈도 및 고객분포)")
st.write("고객들의 구매 패턴과 매출 기여도를 다각도로 분석합니다. 충성 고객과 일반 고객의 특징을 파악할 수 있습니다.")

# ---------------- 레이아웃 (3열 구성) ----------------
col1, col2, col3 = st.columns(3)

with col1:
    purchase_freq_fig = create_purchase_frequency_chart(order_items_filtered)
    if purchase_freq_fig:
        st.pyplot(purchase_freq_fig)

with col2:
    revenue_contrib_fig = create_revenue_contribution_chart(order_items_filtered)
    if revenue_contrib_fig:
        st.pyplot(revenue_contrib_fig)

with col3:
    revenue_dist_fig = create_revenue_distribution_chart(order_items_filtered)
    if revenue_dist_fig:
        st.pyplot(revenue_dist_fig)



# ---------------- 카테고리/상품별 매출 ----------------
st.subheader("Category & Product Revenue Analysis (카테고리 / 상품별 매출)")
st.write("어떤 카테고리와 상품이 매출을 주도하는지, 카테고리별 평균 구매 금액(객단가)은 어떤지 분석합니다.")

# order_items + products 조인
order_items_merged = order_items_filtered.merge(
    products_filtered[["id", "category", "name"]],
    left_on="product_id", right_on="id", how="inner"
)

# ---------------- 레이아웃 (3열) ----------------
col1, col2, col3 = st.columns(3)

with col1:
    top_cat_rev_fig = create_top_revenue_chart(order_items_merged, by='category')
    if top_cat_rev_fig:
        st.pyplot(top_cat_rev_fig)

with col2:
    top_prod_rev_fig = create_top_revenue_chart(order_items_merged, by='product')
    if top_prod_rev_fig:
        st.pyplot(top_prod_rev_fig)

with col3:
    cat_aov_fig = create_category_aov_chart(order_items_merged)
    if cat_aov_fig:
        st.pyplot(cat_aov_fig)
