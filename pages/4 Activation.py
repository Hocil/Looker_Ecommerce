import streamlit as st
import pandas as pd
import koreanize_matplotlib
import matplotlib.pyplot as plt
from data import load_all_data
from charts.activation_charts import (
    create_monthly_activation_chart,
    create_activation_by_gender_chart,
    create_activation_by_traffic_source_chart,
    create_activation_by_age_chart,
    create_first_purchase_category_chart,
    create_ttfp_histogram
)
st.set_page_config(
    page_title="✨ Activation 분석",
    layout="wide"
)

# 제목 및 설명 (title)
st.title("✨ 활성화(Activation) 분석")
st.write("신규 가입자의 첫 구매 전환까지의 과정을 분석합니다.")

# 데이터 로드
all_data = load_all_data()
users = all_data["users"]
products = all_data["products"]
orders = all_data["orders"]
order_items = all_data["order_items"]
events = all_data["events"]
inventory_items = all_data["inventory_items"]

# -----------------------------------사이드바(필터) 설정-----------------------------------
st.sidebar.header("Filters")

valid_status = ["Complete"]
orders_complete = orders[orders["status"] == "Complete"]

# 기간 선택
selected_year = st.sidebar.selectbox("Year", [2023])
selected_month = st.sidebar.multiselect(
    "Month",
    options=list(range(1,13)),
    default=list(range(1,13)))

# 성별 선택
gender_filter = st.sidebar.selectbox("Gender", ["All", "M", "F"])

# 채널 선택
traffic_filter = st.sidebar.multiselect(
    "Traffic Source",
    options=users["traffic_source"].unique(),
    default=list(users["traffic_source"].unique()))

# -------------------- 필터 적용 --------------------
users_filtered = users.copy()

# 성별 필터
if gender_filter != "All":
    users_filtered = users_filtered[users_filtered["gender"] == gender_filter]

# 채널 필터
users_filtered = users_filtered[users_filtered["traffic_source"].isin(traffic_filter)]


# -----------------------------------[KPI 카드 표시]--------------------------------------------
st.subheader("Activation Overview (활성화 개요)")
st.write("선택한 기간 및 조건에 해당하는 전체 사용자 중 첫 구매를 완료하여 '활성화'된 사용자의 비율을 보여줍니다.")

total_users = users_filtered["id"].nunique()

activated_users = (
    orders.loc[orders["status"].isin(valid_status)]
    .merge(users_filtered[["id"]], left_on="user_id", right_on="id", how="inner")["user_id"]
    .nunique())

first_orders = (
    orders_complete
    .groupby("user_id")["created_at"].min()
    .dt.to_period("M")
    .reset_index()
    .rename(columns={"created_at": "first_order_month"}))
# 활성화율 계산
activation_rate = activated_users / total_users * 100

# st.metric("Total Users", total_users)
# st.metric("Activated Users", activated_users)
# st.metric("Activation Rate (%)", f"{activation_rate:.2f}%")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Users", total_users)
with col2:
    st.metric("Activated Users", activated_users)
with col3:
    st.metric("Activation Rate (%)", f"{activation_rate:.2f}%")

st.markdown("---")

# ----------------------------- Time to First Purchase 요약 통계 -----------------------------
st.subheader("Time to First Purchase (TTFP) 요약 통계")
st.write("사용자가 가입한 후 첫 구매를 하기까지 평균적으로 얼마나 걸리는지 일(Day) 단위로 보여줍니다. 이 시간이 짧을수록 온보딩 과정이 효과적임을 의미합니다.")
# first_orders는 첫 구매일만 담고 있음 (컬럼명: first_order_month)
# 유저별 첫 구매일자 & 첫 구매월 같이 생성
first_orders = (
    orders_complete
    .groupby("user_id")["created_at"].min()
    .reset_index()
    .rename(columns={"created_at": "first_order_date"})
)

# 월 단위 컬럼 추가
first_orders["first_order_month"] = first_orders["first_order_date"].dt.to_period("M")


# 가입일 대비 첫 구매일 계산
users_first_purchase = users_filtered.merge(
    first_orders,
    left_on="id",
    right_on="user_id",
    how="inner"
)
users_first_purchase["ttfp_days"] = (
    (users_first_purchase["first_order_date"] - users_first_purchase["created_at"]).dt.days
)

# 요약 통계 계산
ttfp_mean = users_first_purchase["ttfp_days"].mean()
ttfp_median = users_first_purchase["ttfp_days"].median()
ttfp_q25 = users_first_purchase["ttfp_days"].quantile(0.25)
ttfp_q75 = users_first_purchase["ttfp_days"].quantile(0.75)
ttfp_max = users_first_purchase["ttfp_days"].max()

# KPI 카드 형식으로 표시
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Avg TTFP", f"{ttfp_mean:.1f} days")
with col2:
    st.metric("Median TTFP", f"{ttfp_median:.1f} days")
with col3:
    st.metric("25%ile", f"{ttfp_q25:.1f} days")
with col4:
    st.metric("75%ile", f"{ttfp_q75:.1f} days")
with col5:
    st.metric("Max TTFP", f"{ttfp_max:.0f} days")


# ------------------------------------------------------------------------------

st.markdown("---")

# 가입 월
# users["signup_month"] = users["created_at"].dt.to_period("M")
users_filtered["signup_month"] = users_filtered["created_at"].dt.to_period("M")

# 가입자 + 첫구매월 병합
# merged = users.merge(first_orders, left_on="id", right_on="user_id", how="left")
merged = users_filtered.merge(first_orders, left_on="id", right_on="user_id", how="left")


# 월별 Activation 계산
monthly_df = (
    merged.groupby("signup_month")
    .agg(total_users=("id","nunique"),
         activated_users=("first_order_month", lambda x: x.notna().sum())))
monthly_df["activation_rate"] = monthly_df["activated_users"] / monthly_df["total_users"] * 100


# ----------------------------- Activation 관련 그래프 -----------------------------------
# // 그래프 1 - 월별 활성화율 //
st.subheader("가입 월별 활성화율 추이")
st.write("가입한 월을 기준으로, 해당 월 가입자들이 얼마나 첫 구매로 전환되었는지 비율의 변화를 보여줍니다. 데이터 수집 기간에 따라 최근 월의 활성화율은 낮게 나타날 수 있습니다.")
_, monthly_activation_fig = create_monthly_activation_chart(users_filtered, first_orders)
st.pyplot(monthly_activation_fig)

# ----------------------------- 유저 특성별 Activation 분석 -----------------------------------
# //사전작업//
st.subheader("사용자 특성별 활성화율 비교")
st.write("사용자의 인구통계학적 특성(성별, 연령대)과 유입 경로에 따라 첫 구매 전환율이 어떻게 다른지 비교 분석합니다.")
# Activation 여부 계산: users + orders 조인
activated_ids = (
    orders.loc[orders["status"].isin(valid_status), ["user_id"]]
    .drop_duplicates()
    .rename(columns={"user_id": "id"})
)

users_filtered = users_filtered.copy()
users_filtered["activated"] = users_filtered["id"].isin(activated_ids["id"])

# ----------------------------- 성별, 채널, 연령대 레이아웃 -----------------------------
col1, col2, col3 = st.columns(3)

# 1) 성별별 Activation Rate
with col1:
    st.write("#### 성별")
    _, gender_fig = create_activation_by_gender_chart(users_filtered)
    st.pyplot(gender_fig)

# 2) 채널별 Activation Rate
with col2:
    st.write("#### 유입 경로별")
    _, traffic_fig = create_activation_by_traffic_source_chart(users_filtered)
    st.pyplot(traffic_fig)

# 3) 연령대별 Activation Rate
with col3:
    st.write("#### 연령대별")
    _, age_fig = create_activation_by_age_chart(users_filtered)
    st.pyplot(age_fig)


# ----------------------------- 첫 구매 패턴 -----------------------------------
st.subheader("첫 구매 패턴 분석")
st.write("신규 사용자들이 첫 구매 시 어떤 특징을 보이는지 분석합니다. 평균 구매 금액, 주로 구매하는 상품 카테고리, 구매까지 걸리는 시간 분포를 통해 초기 고객 경험을 이해할 수 있습니다.")

# CSS 스타일 정의 (텍스트 크게 + 중앙정렬)
st.markdown("""
    <style>
    .big-metric {
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0 10px 0;
    }
    .big-value {
        font-size: 36px;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 40px;
    }
    </style>
""", unsafe_allow_html=True)

# 레이아웃: 2열 구성
col1, col2 = st.columns([1, 3])  # 왼쪽 좁게(1), 오른쪽 넓게(3)

# 필터된 orders만 사용 (users_filtered와 조인)
filtered_orders = orders[orders["user_id"].isin(users_filtered["id"])]

# 유저별 첫 구매 기록 가져오기
first_orders = (
    filtered_orders.loc[filtered_orders["status"].isin(valid_status)]
    .sort_values("created_at")
    .groupby("user_id")
    .first()
    .reset_index())

# 첫 구매 상품 정보
first_order_items = order_items.merge(
    first_orders[["order_id", "user_id", "created_at"]],
    on="order_id", how="inner"
).merge(products, left_on="product_id", right_on="id", how="left")

# 첫 구매 시점 (가입일 대비)
users_first_purchase = users_filtered.merge(
    first_orders[["user_id", "created_at"]],
    left_on="id", right_on="user_id", how="inner")
users_first_purchase["ttfp_days"] = (
    (users_first_purchase["created_at_y"] - users_first_purchase["created_at_x"]).dt.days)

# ------------------- KPI 카드 -------------------
with col1:
    avg_price = first_order_items["sale_price"].mean()
    median_price = first_order_items["sale_price"].median()

    st.markdown("<div class='big-metric'>Avg First Purchase</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-value'>${avg_price:.2f}</div>", unsafe_allow_html=True)

    st.markdown("<div class='big-metric'>Median First Purchase</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-value'>${median_price:.2f}</div>", unsafe_allow_html=True)

# ------------------- 그래프 (2개) 카테고리T5, 첫구매 시점분포 -------------------
with col2:
    g1, g2 = st.columns(2)  # 2개 분할

    # 1. 카테고리 TOP5
    with g1:
        _, category_fig = create_first_purchase_category_chart(first_order_items)
        if category_fig:
            st.pyplot(category_fig)

    # 2. 첫 구매 시점 분포
    with g2:
        _, ttfp_fig = create_ttfp_histogram(users_first_purchase)
        if ttfp_fig:
            st.pyplot(ttfp_fig)
