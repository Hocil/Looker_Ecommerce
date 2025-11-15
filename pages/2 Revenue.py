import streamlit as st
import pandas as pd
import koreanize_matplotlib
import matplotlib.pyplot as plt
from data import load_all_data

# 데이터 로드
all_data = load_all_data()
users = all_data["users"]
products = all_data["products"]
orders = all_data["orders"]
order_items = all_data["order_items"]
events = all_data["events"]
inventory_items = all_data["inventory_items"]

# ---------------- 페이지 기본 설정 ----------------
st.set_page_config(
    page_title="매출 분석",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded")

# 제목, 설명 (title)
st.title("💰 매출 분석")
st.markdown("### Revenue(매출) 현황")

# # ---------------- 사이드바 ----------------
# st.sidebar.header("Filters")

# ## 1. 기간 필터 (연도 제거 → 월만)
# months = list(range(1, 13))
# months_with_all = ["All"] + months
# selected_months = st.sidebar.multiselect(
#     "Month",
#     options=months_with_all,
#     default=["All"]
# )
# # All 선택 시 전체 월로 처리
# if "All" in selected_months:
#     selected_months = months


# ## 2. 주문 상태 필터
# status_filter = st.sidebar.multiselect(
#     "Order Status",
#     options=orders["status"].unique().tolist(),
#     default="Complete"
# )

# ## 3. 사용자 필터
# gender_filter = st.sidebar.selectbox("Gender", ["All", "M", "F"])

# # 연령대 구간 정의
# age_bins = [0, 20, 30, 40, 50, 60, 100]
# age_labels = ["<20", "20s", "30s", "40s", "50s", "60+"]
# users["age_group"] = pd.cut(users["age"], bins=age_bins, labels=age_labels, right=False)

# age_options = ["All"] + age_labels
# age_filter = st.sidebar.multiselect(
#     "Age Group",
#     options=age_options,
#     default=["All"]
# )
# if "All" in age_filter:
#     age_filter = age_labels


# # 트래픽 소스 필터
# traffic_sources = users["traffic_source"].dropna().unique().tolist()
# traffic_options = ["All"] + traffic_sources
# traffic_filter = st.sidebar.multiselect(
#     "Traffic Source",
#     options=traffic_options,
#     default=["All"]
# )
# if "All" in traffic_filter:
#     traffic_filter = traffic_sources


# ## 4. 상품 필터
# categories = products["category"].dropna().unique().tolist()
# category_options = ["All"] + categories
# category_filter = st.sidebar.multiselect(
#     "Category",
#     options=category_options,
#     default=["All"]
# )
# if "All" in category_filter:
#     category_filter = categories


# brands = products["brand"].dropna().unique().tolist()
# brand_options = ["All"] + brands
# brand_filter = st.sidebar.multiselect(
#     "Brand",
#     options=brand_options,
#     default=["All"]
# )
# if "All" in brand_filter:
#     brand_filter = brands

# ---------------- 사이드바 ----------------
st.sidebar.header("컨트롤 패널")

## 1. 기간 필터 (연도 제거 → 월만)
selected_months = st.sidebar.multiselect(
    "월 선택",   # ✔ Month → 월 선택
    options=months_with_all,
    default=["All"]
)

## 2. 주문 상태 필터
status_filter = st.sidebar.multiselect(
    "주문 상태",   # ✔ Order Status → 주문 상태
    options=orders["status"].unique().tolist(),
    default="Complete"
)

## 3. 사용자 필터
gender_filter = st.sidebar.selectbox(
    "성별",   # ✔ Gender → 성별
    ["All", "M", "F"]
)

age_filter = st.sidebar.multiselect(
    "연령대",   # ✔ Age Group → 연령대
    options=age_options,
    default=["All"]
)

traffic_filter = st.sidebar.multiselect(
    "유입 경로",   # ✔ Traffic Source → 유입 경로
    options=traffic_options,
    default=["All"]
)

## 4. 상품 필터
category_filter = st.sidebar.multiselect(
    "카테고리",   # ✔ Category → 카테고리
    options=category_options,
    default=["All"]
)

brand_filter = st.sidebar.multiselect(
    "브랜드",   # ✔ Brand → 브랜드
    options=brand_options,
    default=["All"]
)



# ---------------- 필터 적용 ----------------
# 1) 기간 필터 적용
orders["month"] = pd.to_datetime(orders["created_at"]).dt.month
orders_filtered = orders[
    (orders["month"].isin(selected_months)) &
    (orders["status"].isin(status_filter))
]

# 2) 사용자 필터 적용
users_filtered = users.copy()
if gender_filter != "All":
    users_filtered = users_filtered[users_filtered["gender"] == gender_filter]

users_filtered = users_filtered[
    (users_filtered["age_group"].isin(age_filter)) &
    (users_filtered["traffic_source"].isin(traffic_filter))
]

# 3) 상품 필터 적용
products_filtered = products[
    (products["category"].isin(category_filter)) &
    (products["brand"].isin(brand_filter))
]

# 4) order_items 필터 적용
order_items_filtered = order_items[
    order_items["order_id"].isin(orders_filtered["order_id"])
]
order_items_filtered = order_items_filtered[
    order_items_filtered["product_id"].isin(products_filtered["id"])
]
order_items_filtered = order_items_filtered[
    order_items_filtered["user_id"].isin(users_filtered["id"])
]


# ---------------- 탭 정의 ----------------
tab1, tab2, tab3 = st.tabs(["📈 매출 요약 및 추이 분석", "👥 고객 매출 기여도 분석", "🛍️ 카테고리·상품별 매출 분석"])

# 1️⃣ Revenue Overview
with tab1:
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
    st.subheader("매출 요약")

    # 윗줄 (규모 지표)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue (총 매출)", f"${total_revenue:,.2f}")
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


    st.markdown("---")
    # ---------------- 시간 흐름별 매출 추이 ----------------
    st.subheader("시간 흐름별(월별) 매출 추이")

    # 월별 매출 집계
    monthly_revenue = (
        order_items_filtered
        .groupby(order_items_filtered["created_at"].dt.to_period("M"))["sale_price"]
        .sum()
        .reset_index()
    )

    # Period → datetime 변환
    monthly_revenue["created_at"] = monthly_revenue["created_at"].dt.to_timestamp()

    # 그래프
    fig, ax = plt.subplots(figsize=(8,4), dpi=100)

    # 라인 및 포인트
    ax.plot(
        monthly_revenue["created_at"],
        monthly_revenue["sale_price"],
        marker="o",
        markersize=7,
        markerfacecolor="white",
        markeredgecolor="steelblue",
        color="royalblue",
        linewidth=2.5
    )

    # 영역 음영 (fill_between)
    ax.fill_between(
        monthly_revenue["created_at"],
        monthly_revenue["sale_price"],
        color="lightblue",
        alpha=0.3
    )

    # 제목, 축 라벨
    ax.set_title("월별 매출 추이", fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("월별", fontsize=11)
    ax.set_ylabel("매출액 ($)", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # 여유 공간
    ymax = monthly_revenue["sale_price"].max()
    ax.set_ylim(0, ymax * 1.15)

    # 데이터 라벨
    for i, v in enumerate(monthly_revenue["sale_price"]):
        ax.text(
            monthly_revenue["created_at"].iloc[i],
            v + (ymax * 0.03),
            f"${v:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="black",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none")
        )

    # 눈금 스타일
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='both', labelsize=9)

    st.pyplot(fig)


# 2️⃣ Customer Insights
with tab2:
    # ---------------- 구매 빈도 & 고객 분포 ----------------
    st.subheader("구매빈도 및 고객분포")
    st.info("구매횟수 별 유저비율, 고객 매출 기여도, 고객 매출분포")

    # 유저별 구매 횟수 (필터 일치 위해 order_items_filtered에서 고유 주문 수 집계)
    user_order_counts = (
        order_items_filtered.groupby("user_id")["order_id"].nunique().reset_index()
    )
    user_order_counts.rename(columns={"order_id": "num_orders"}, inplace=True)

    # 1) 구매 횟수별 유저 비율
    purchase_freq = user_order_counts["num_orders"].value_counts().sort_index()

    # 2) 고객 매출 기여도 (상위 10%)
    user_revenue = (
        order_items_filtered.groupby("user_id")["sale_price"].sum().reset_index()
        .sort_values("sale_price", ascending=False)
        .reset_index(drop=True)
    )
    total_rev_users = user_revenue["sale_price"].sum()
    import math
    top_10pct_count = max(1, math.ceil(len(user_revenue) * 0.10)) if len(user_revenue) > 0 else 0
    top_10pct_revenue = user_revenue.head(top_10pct_count)["sale_price"].sum()
    top_10pct_ratio = (top_10pct_revenue / total_rev_users * 100) if total_rev_users > 0 else 0

    # ---------------- 레이아웃 (3열 구성) ----------------
    col1, col2, col3 = st.columns(3)


    # ① 주문 횟수별 고객 분포
    with col1:
        fig, ax = plt.subplots(figsize=(5,4))
        if not purchase_freq.empty:
            bars = ax.bar(
                purchase_freq.index,
                purchase_freq.values,
                color="royalblue",
                alpha=0.85,
                edgecolor="white",
                linewidth=0.7
            )
            ax.set_title("주문 횟수별 고객 분포", fontsize=12, fontweight="bold", pad=10)
            ax.set_xlabel("주문 횟수", fontsize=10)
            ax.set_ylabel("고객 수", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.setp(ax.get_xticklabels(), rotation=0)

            # 값 라벨
            ax.bar_label(bars, labels=[f"{v:,}" for v in purchase_freq.values], padding=3, fontsize=8)

            # 테두리 깔끔히
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        st.pyplot(fig)


    # ② 상위 10% 고객 매출 기여도 (파이차트)
    with col2:
        fig, ax = plt.subplots(figsize=(5,4))
        if top_10pct_count > 0 and total_rev_users > 0:
            labels = ["상위 10%", "기타 고객"]
            values = [top_10pct_revenue, total_rev_users - top_10pct_revenue]
            explode = (0.08, 0)

            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=["#FFB347", "#D3D3D3"],
                explode=explode,
                shadow=True,
                textprops={'fontsize': 9}
            )

            # 퍼센트 텍스트 스타일
            for autotext in autotexts:
                autotext.set_color("black")
                autotext.set_fontweight("bold")

            ax.set_title("상위 10% 고객 매출 기여도", fontsize=12, fontweight="bold", pad=10)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        st.pyplot(fig)


    # ③ 고객별 매출 분포 (히스토그램)
    with col3:
        fig, ax = plt.subplots(figsize=(5,4))
        if not user_revenue.empty:
            n, bins, patches = ax.hist(
                user_revenue["sale_price"],
                bins=15,
                color="#3CB371",
                alpha=0.8,
                edgecolor="white",
                linewidth=0.5
            )
            ax.set_title("고객별 매출 분포", fontsize=12, fontweight="bold", pad=10)
            ax.set_xlabel("고객별 매출액 ($)", fontsize=10)
            ax.set_ylabel("고객 수", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            # 평균선 표시
            mean_val = user_revenue["sale_price"].mean()
            ax.axvline(mean_val, color="red", linestyle="--", linewidth=1.5)
            ax.text(
                mean_val,
                ax.get_ylim()[1]*0.9,
                f"평균 ${mean_val:,.0f}",
                color="red",
                fontsize=8,
                ha="center"
            )

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        st.pyplot(fig)


# 3️⃣ Category Insights
with tab3:
    # ---------------- 카테고리/상품별 매출 ----------------
    st.subheader("카테고리 및 상품별 매출 분석")
    st.info("카테고리별 매출 Top10, 상품별 매출 Top10, 카테고리별 객단가 (AOV)")

    # order_items + products 조인
    order_items_merged = order_items_filtered.merge(
        products_filtered[["id", "category", "name"]],
        left_on="product_id", right_on="id", how="inner"
    )

    # 원본 인덱스로 집계
    cat_rev_full = order_items_merged.groupby("category")["sale_price"].sum().sort_values(ascending=False)
    cat_ord_full = order_items_merged.groupby("category")["order_id"].nunique()
    cat_aov_full = (cat_rev_full / cat_ord_full).dropna()

    # Top10만 시각화용으로 복사 + 축약 라벨 적용
    import textwrap
    cat_rev_plot = cat_rev_full.head(10).copy()
    cat_rev_plot.index = [textwrap.shorten(str(c), width=25, placeholder="...") for c in cat_rev_plot.index]

    prod_rev_plot = (
        order_items_merged.groupby("name")["sale_price"].sum()
        .sort_values(ascending=False).head(10).copy()
    )
    prod_rev_plot.index = [textwrap.shorten(str(p), width=25, placeholder="...") for p in prod_rev_plot.index]

    # AOV는 상위 카테고리로 보여주고, 라벨만 축약
    cat_aov_plot = cat_aov_full.sort_values(ascending=False).head(10).copy()
    cat_aov_plot.index = [textwrap.shorten(str(c), width=25, placeholder="...") for c in cat_aov_plot.index]

    # ---------------- 레이아웃 (3열) ----------------
    col1, col2, col3 = st.columns(3)
    # ① 매출 상위 10개 카테고리
    with col1:
        fig, ax = plt.subplots(figsize=(5,4))
        if not cat_rev_plot.empty:
            bars = ax.barh(
                cat_rev_plot.index,
                cat_rev_plot.values,
                color="royalblue",
                alpha=0.85,
                edgecolor="white"
            )
            ax.set_title("매출 상위 10개 카테고리", fontsize=12, fontweight="bold", pad=10)
            ax.set_xlabel("매출액 ($)", fontsize=10)
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            ax.invert_yaxis()

            # 값 표시
            ax.bar_label(bars, fmt="$%d", label_type="edge", fontsize=8, padding=3)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        plt.tight_layout()
        st.pyplot(fig)


        # ② 매출 상위 10개 상품
    with col2:
        fig, ax = plt.subplots(figsize=(5,4))
        if not prod_rev_plot.empty:
            bars = ax.barh(
                prod_rev_plot.index,
                prod_rev_plot.values,
                color="#FFA500",
                alpha=0.85,
                edgecolor="white"
            )
            ax.set_title("매출 상위 10개 상품", fontsize=12, fontweight="bold", pad=10)
            ax.set_xlabel("매출액 ($)", fontsize=10)
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            ax.invert_yaxis()

            # 값 표시
            ax.bar_label(bars, fmt="$%d", label_type="edge", fontsize=8, padding=3)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        plt.tight_layout()
        st.pyplot(fig)


    # ③ 카테고리별 평균 주문 금액 (AOV)
    with col3:
        fig, ax = plt.subplots(figsize=(5,4))
        if not cat_aov_plot.empty:
            bars = ax.bar(
                cat_aov_plot.index,
                cat_aov_plot.values,
                color="#3CB371",
                alpha=0.8,
                edgecolor="white"
            )
            ax.set_title("카테고리별 평균 주문 금액 (AOV)", fontsize=12, fontweight="bold", pad=10)
            ax.set_ylabel("평균 주문 금액 ($)", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            # 값 표시
            ax.bar_label(bars, fmt="$%d", label_type="edge", fontsize=8, padding=3)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
        else:
            ax.text(0.5, 0.5, "데이터가 없습니다", ha="center", va="center", fontsize=10)
            ax.axis("off")
        # plt.tight_layout()
        st.pyplot(fig)

