import streamlit as st
import pandas as pd
import koreanize_matplotlib
import matplotlib.pyplot as plt
from data import load_all_data

st.set_page_config(
    page_title="Activation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded")

# 제목 및 설명 (title)
st.title("✨ 사용자 첫 구매 전환 분석")
st.markdown("### 가입 이후 → 첫 구매 완료 기준 Activation 현황")

# 데이터 로드
all_data = load_all_data()
users = all_data["users"]
products = all_data["products"]
orders = all_data["orders"]
order_items = all_data["order_items"]
events = all_data["events"]
inventory_items = all_data["inventory_items"]

# # 데이터 로드
# @st.cache_data
# def load_data(base_path="data/"):
#     users = pd.read_csv(base_path + "users.csv")
#     products = pd.read_csv(base_path + "products.csv")
#     orders = pd.read_csv(base_path + "orders.csv")
#     order_items = pd.read_csv(base_path + "order_items.csv")
#     events = pd.read_csv(base_path + "events_sample.csv")
#     inventory_items = pd.read_csv(base_path + "inventory_items.csv")
#     return users, products, orders, order_items, events, inventory_items

# users, products, orders, order_items, events, inventory_items = load_data()

# @st.cache_data
# def preprocess_dates(users, orders, order_items, events, inventory_items):
#     date_cols = {
#         "users": ["created_at"],
#         "orders": ["created_at", "returned_at", "shipped_at", "delivered_at"],
#         "order_items": ["created_at", "shipped_at", "delivered_at", "returned_at"],
#         "events": ["created_at"],
#         "inventory_items": ["created_at", "sold_at"]}

#     for df_name, cols in date_cols.items():
#         for col in cols:
#             globals()[df_name][col] = pd.to_datetime(globals()[df_name][col], errors="coerce")

#     return users, orders, order_items, events, inventory_items

# users, orders, order_items, events, inventory_items = preprocess_dates(
#     users, orders, order_items, events, inventory_items)

# # [2023년 데이터만 추출]
# orders_years = orders.copy()
# users = users[(users['created_at'] >= "2023-01-01") & (users['created_at'] <= "2023-12-31")]
# orders = orders[(orders['created_at'] >= "2023-01-01") & (orders['created_at'] <= "2023-12-31")]
# order_items = order_items[(order_items['created_at'] >= "2023-01-01") & (order_items['created_at'] <= "2023-12-31")]
# events = events[(events['created_at'] >= "2023-01-01") & (events['created_at'] <= "2023-12-31")]
# inventory_items = inventory_items[(inventory_items['created_at'] >= "2023-01-01") & (inventory_items['created_at'] <= "2023-12-31")]


# -----------------------------------사이드바(필터) 설정-----------------------------------
st.sidebar.header("Filters")

# 상태 설정 (필요시 수정진행하기)
valid_status = ["Complete"]
orders_complete = orders[orders["status"] == "Complete"]

# 기간 선택
# selected_year = st.sidebar.selectbox("Year", [2023])

month_options = list(range(1, 13))
month_options_display = [f"{m}월" for m in month_options]
month_filter = st.sidebar.multiselect(
    "Month",
    options=["All"] + month_options_display,
    default=["All"]
)

# 선택 로직
if "All" in month_filter:
    selected_month = month_options
else:
    # 문자열 "1월" → 숫자 1 변환
    selected_month = [int(m.replace("월", "")) for m in month_filter]

# 성별 선택
gender_filter = st.sidebar.selectbox("Gender", ["All", "M", "F"])

# 채널 선택
# traffic_filter = st.sidebar.multiselect(
#     "Traffic Source",
#     options=users["traffic_source"].unique(),
#     default=list(users["traffic_source"].unique()))

traffic_options = users["traffic_source"].dropna().unique().tolist()
traffic_filter = st.sidebar.multiselect(
    "Traffic Source",
    options=["All"] + traffic_options,
    default=["All"])

if "All" in traffic_filter:
    traffic_filter = traffic_options  # 전체 대체



# -------------------- 필터 적용 --------------------
users_filtered = users.copy()

# 성별 필터
if gender_filter != "All":
    users_filtered = users_filtered[users_filtered["gender"] == gender_filter]

# 채널 필터
users_filtered = users_filtered[users_filtered["traffic_source"].isin(traffic_filter)]

# 카테고리 필터
# category_filter = st.sidebar.multiselect(
#     "Category",
#     options=products["category"].unique(),
#     default=list(products["category"].unique()))
category_options = products["category"].dropna().unique().tolist()
category_filter = st.sidebar.multiselect(
    "Category",
    options=["All"] + category_options,
    default=["All"]
)

if "All" in category_filter:
    category_filter = category_options  # 전체로 대체


#  월 필터 적용 (회원가입 기준)
users_filtered["month"] = users_filtered["created_at"].dt.month
users_filtered = users_filtered[users_filtered["month"].isin(selected_month)]

# ------------------------Tab

# 탭 정의
tab1, tab2, tab3 = st.tabs(["📈 활성화 요약", "👥 사용자 특성 분석", "🛒 첫 구매 패턴분석"])

# 1️⃣ Overview 탭
with tab1:
    st.subheader("사용자 활성화 요약")
    st.info("전체 유입 대비 활성 유저 추이를 확인할 수 있습니다.")

    # -----------------------------------[KPI 카드 표시]--------------------------------------------


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

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 가입자 수", total_users)
    with col2:
        st.metric("첫 구매(활성화) 사용자 수", activated_users)
    with col3:
        st.metric("활성화율", f"{activation_rate:.2f}%")

    st.markdown("---")


    # ----------------------------- Time to First Purchase 요약 통계 -----------------------------
    st.subheader("가입 -> 첫 구매까지 소요일수 요약")
    st.info("TTFP : 사용자가 회원가입한 시점부터 첫 구매가 이루어질 때까지 걸린 시간(일 단위)")
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
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("평균 소요 일수", f"{ttfp_mean:.1f}일")
    with col2:
        st.metric("중앙값 소요 일수", f"{ttfp_median:.1f}일")
    with col3:
        st.metric("최대 소요 일수", f"{ttfp_max:.0f}일")


# ------------------------------------------------------------------------------
    st.markdown("---")

    # 가입 월
    users_filtered["signup_month"] = users_filtered["created_at"].dt.to_period("M")

    # 가입자 + 첫구매월 병합
    merged = users_filtered.merge(first_orders, left_on="id", right_on="user_id", how="left")


    # 월별 Activation 계산
    monthly_df = (
        merged.groupby("signup_month")
        .agg(total_users=("id","nunique"),
            activated_users=("first_order_month", lambda x: x.notna().sum())))
    monthly_df["activation_rate"] = monthly_df["activated_users"] / monthly_df["total_users"] * 100

    # # ----------------------------- 월별 Total vs Activated Users -----------------------------
    # st.subheader("월별 유입 vs 활성 유저 추이")
    # st.info("Total Users와 Activated Users의 월별 추이 비교")

    # # st.pyplot(fig)
    # fig, ax1 = plt.subplots(figsize=(10,5))
    # ax2 = ax1.twinx()

    # # 전체 유저 수
    # l1 = ax1.plot(monthly_df.index.astype(str), monthly_df["total_users"], 
    #             color="lightgray", marker="o", markersize=6, linewidth=2, label="전체 유저")

    # # 활성 유저 수
    # l2 = ax2.plot(monthly_df.index.astype(str), monthly_df["activated_users"], 
    #             color="royalblue", marker="o", markersize=6, linewidth=2, label="활성 유저")

    # # 축 및 제목
    # ax1.set_xlabel("월")
    # ax1.set_ylabel("전체 유저 수", color="gray")
    # ax2.set_ylabel("활성 유저 수", color="royalblue")
    # ax1.set_title("월별 전체 유저 vs 활성 유저 추이", fontsize=13)
    # ax1.tick_params(axis='x', rotation=45)
    # ax1.grid(axis="y", linestyle="--", alpha=0.6)
    # ax1.yaxis.set_major_locator(plt.MaxNLocator(6))


    # # Legend 통합
    # lines = l1 + l2
    # labels = [line.get_label() for line in lines]
    # ax1.legend(lines, labels, loc="upper right", frameon=True)

    # st.pyplot(fig)

        # ----------------------------- 월별 Total vs Activated Users -----------------------------
    st.subheader("월별 전체 유저 vs 활성 유저 추이")
    st.info("가입 후 첫 구매를 완료한 활성 유저와 전체 유저의 월별 추이 비교")

    # Figure 생성
    fig, ax1 = plt.subplots(figsize=(8,4.5), dpi=100)
    ax2 = ax1.twinx()

    # ---------- 데이터 시각화 ----------
    # 전체 유저 수 (회색)
    l1 = ax1.plot(
        monthly_df.index.astype(str),
        monthly_df["total_users"],
        color="#B0B0B0",
        marker="o",
        markersize=5,
        linewidth=2.2,
        label="전체 유저 수"
    )

    # 활성 유저 수 (파랑)
    l2 = ax2.plot(
        monthly_df.index.astype(str),
        monthly_df["activated_users"],
        color="royalblue",
        marker="o",
        markersize=6,
        linewidth=2.2,
        label="활성 유저 수"
    )

    # ---------- 축, 제목, 격자 ----------
    ax1.set_title("월별 전체 유저 vs 활성 유저 추이", fontsize=13, fontweight="bold", pad=10)
    ax1.set_xlabel("월", fontsize=10)
    ax1.set_ylabel("전체 유저 수", color="#6C6C6C", fontsize=10)
    ax2.set_ylabel("활성 유저 수", color="royalblue", fontsize=10)

    # 눈금 및 격자 스타일
    ax1.tick_params(axis="x", rotation=45)
    ax1.tick_params(axis="y", colors="#6C6C6C")
    ax2.tick_params(axis="y", colors="royalblue")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.yaxis.set_major_locator(plt.MaxNLocator(6))

    # ---------- 값 라벨 표시 (활성 유저 수: 파랑 / 전체 유저 수: 회색) ----------

    # 활성 유저 수 라벨 (오른쪽 Y축)
    for i, v in enumerate(monthly_df["activated_users"]):
        ax2.text(
            i, v + (v * 0.02),
            f"{v:,}",
            ha="center", va="bottom",
            fontsize=8, color="royalblue", fontweight="bold"
        )

    # 전체 유저 수 라벨 (왼쪽 Y축)
    for i, v in enumerate(monthly_df["total_users"]):
        ax1.text(
            i, v - (v * 0.004),  # 살짝 아래로
            f"{v:,}",
            ha="center", va="top",
            fontsize=8, color="gray", fontweight="bold"
        )


    # ---------- 범례 (통합) ----------
    lines = l1 + l2
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="lower right", frameon=True, fontsize=9)

    # ---------- 미세 조정 ----------
    for spine in ["top", "right"]:
        ax1.spines[spine].set_visible(False)
    ax2.spines["top"].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)


# 2️⃣ Demographic 탭
with tab2:
    st.subheader("사용자 특성별 Activation 분석")
    st.info("연령대, 채널별 Activation Rate를 비교합니다.")
    
    # ----------------------------- 유저 특성별 Activation 분석 -----------------------------------
    # //사전작업//
    # Activation 여부 계산: users + orders 조인
    activated_ids = (
        orders.loc[orders["status"].isin(valid_status), ["user_id"]]
        .drop_duplicates()
        .rename(columns={"user_id": "id"})
    )

    # users_filtered에 'activated' 플래그 추가
    users_filtered = users_filtered.copy()
    users_filtered["activated"] = users_filtered["id"].isin(activated_ids["id"])


    # ----------------------------- 성별별 Activation Rate
    # 성별별 집계 (상호작용) (성별-1)
    gender_df = (
        users_filtered.groupby("gender")
        .agg(total_users=("id", "nunique"),
            activated_users=("activated", "sum"))
        .reset_index())

    gender_df["activation_rate"] = (
        gender_df["activated_users"] / gender_df["total_users"] * 100)

    fig, ax = plt.subplots(figsize=(6,4))
    bars = ax.bar(gender_df["gender"], gender_df["activation_rate"], color="skyblue")

    #  수치 표시
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha="center", va="bottom")


    # ----------------------------- 채널별 Activation Rate (traffic_source)
    channel_df = (
        users_filtered.groupby("traffic_source")
        .agg(total_users=("id", "nunique"),
            activated_users=("activated", "sum"))
        .reset_index())

    channel_df["activation_rate"] = (channel_df["activated_users"] / channel_df["total_users"] * 100)

    fig, ax = plt.subplots(figsize=(8,4))
    bars = ax.bar(channel_df["traffic_source"], channel_df["activation_rate"], color="steelblue")

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval, f"{yval:.1f}%", ha="center", va="bottom")

    # ----------------------------- 연령대별 Activation Rate (Age Binning)
    # 연령대 구간 분할 (users_filtered 기준)
    bins = [0, 20, 30, 40, 50, 60, 100]
    labels = ["<20", "20s", "30s", "40s", "50s", "60+"]
    users_filtered["age_group"] = pd.cut(users_filtered["age"], bins=bins, labels=labels, right=False)

    age_df = (
        users_filtered.groupby("age_group")
        .agg(total_users=("id", "nunique"),
            activated_users=("activated", "sum"))
        .reset_index()
    )

    age_df["activation_rate"] = (
        age_df["activated_users"] / age_df["total_users"] * 100)


    # ----------------------------- 성별, 채널, 연령대 레이아웃 -----------------------------
    col1, col2 = st.columns(2)

    # 1) 채널별 Activation Rate

    # 트래픽소스 내림차순 정렬
    channel_df = channel_df.sort_values("activation_rate", ascending=False)

    # 1) 연령대별 월별 Activation Rate (Multi-line)
# -------------------- (1) 연령대별 월별 활성화 추이 --------------------
    with col1:
        st.subheader("연령대별 월별 활성화 추이")

        fig, ax = plt.subplots(figsize=(6,4))
        plt.subplots_adjust(left=0.12, right=0.98, top=0.90, bottom=0.18)

        # 1. 나이 구간 설정
        bins = [0, 20, 30, 40, 50, 60, 100]
        labels = ["<20", "20s", "30s", "40s", "50s", "60+"]
        users_filtered["age_group"] = pd.cut(users_filtered["age"], bins=bins, labels=labels, right=False)

        # 2. 연령대 + 가입월 기준 집계
        age_month_df = (
            merged.merge(users_filtered[["id", "age_group"]], left_on="id", right_on="id", how="left")
            .groupby(["signup_month", "age_group"])
            .agg(total_users=("id","nunique"),
                activated_users=("first_order_month", lambda x: x.notna().sum()))
            .reset_index()
        )

        # 3. 활성화율 계산
        age_month_df["activation_rate"] = (
            age_month_df["activated_users"] / age_month_df["total_users"] * 100
        )

        # 4. 피벗 테이블 생성 (행:월, 열:연령대)
        pivot_df = age_month_df.pivot(index="signup_month", columns="age_group", values="activation_rate")
        pivot_df.index = pivot_df.index.to_timestamp()
        # 5. 라인 그래프 생성
        fig, ax = plt.subplots(figsize=(6,4), dpi=100)

        for col in pivot_df.columns:
            ax.plot(
                pivot_df.index,
                pivot_df[col],
                marker="o",
                linewidth=2,
                markersize=6,
                label=col
            )

        # 스타일 및 제목
        # ax.set_title("연령대별 월별 활성화 추이", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("가입 월", fontsize=10)
        ax.set_ylabel("활성화율 (%)", fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(title="연령대", bbox_to_anchor=(1.05, 1), loc="upper left", frameon=False)

        # # 각 포인트 수치 표시
        # for i, col in enumerate(pivot_df.columns):
        #     for x, y in zip(pivot_df.index, pivot_df[col]):
        #         ax.text(x, y + 0.5, f"{y:.1f}%", ha="center", va="bottom", fontsize=8)

        # 테두리 정리
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)

    
    # -------------------- (2) 유입 경로별 활성화율 --------------------
    with col2:
        st.subheader("유입 경로별 활성화율")

        # fig, ax = plt.subplots(figsize=(5,4), dpi=100)
        fig, ax = plt.subplots(figsize=(6,4))
        plt.subplots_adjust(left=0.22, right=0.98, top=0.90, bottom=0.10)

        bars = ax.barh(
            channel_df["traffic_source"],
            channel_df["activation_rate"],
            color="royalblue",
            alpha=0.85,
            edgecolor="white"
        )

        # 제목 및 축 설정
        # ax.set_title("유입 경로별 활성화율", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("활성화율 (%)", fontsize=10)
        ax.set_ylabel("유입 경로", fontsize=10)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.invert_yaxis()

        # 수치 라벨 (막대 끝 오른쪽)
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.8,  # 👉 살짝 오른쪽으로 이동
                bar.get_y() + bar.get_height()/2,
                f"{width:.1f}%",
                ha="left", va="center",
                fontsize=9,
                color="black",
                fontweight="bold"
            )

        # 테두리 정리
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        plt.tight_layout()
        st.pyplot(fig)

    # ----------------------------- 첫 구매 패턴 -----------------------------------
with tab3:
    st.subheader("첫 구매 패턴 분석")
    st.info("사용자별 첫 구매 금액, 카테고리, 구매 시점 등을 시각화합니다.")

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
    first_order_items = (
        order_items.merge(
            first_orders[["order_id", "user_id", "created_at"]],
            on="order_id", how="inner"
        )
        .merge(products, left_on="product_id", right_on="id", how="left")
    )

    # 카테고리 필터 적용
    first_order_items = first_order_items[first_order_items["category"].isin(category_filter)]


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

        # st.markdown("<div class='big-metric'>Avg First Purchase</div>", unsafe_allow_html=True)
        # st.markdown(f"<div class='big-value'>${avg_price:.2f}</div>", unsafe_allow_html=True)

        st.markdown("<div class='big-metric'>첫 구매 금액 (Median)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-value'>${median_price:.2f}</div>", unsafe_allow_html=True)

# ------------------- 그래프 (2개) 카테고리 TOP5, 첫구매 시점분포 -------------------

    # 1. first_order_items 생성
    first_order_items = (
        order_items.merge(
            first_orders[["order_id", "user_id", "created_at"]],
            on="order_id", how="inner"
        )
        .merge(products, left_on="product_id", right_on="id", how="left")
    )

    # user_id 충돌 정리
    if "user_id_x" in first_order_items.columns:
        first_order_items["user_id"] = first_order_items["user_id_x"]
    elif "user_id_y" in first_order_items.columns:
        first_order_items["user_id"] = first_order_items["user_id_y"]

    # 카테고리 필터 적용
    first_order_items = first_order_items[first_order_items["category"].isin(category_filter)]

    # 2. 시각화 영역
    with col2:
        g1, g2 = st.columns(2)  # 왼쪽: TOP5 / 오른쪽: 첫 구매 시점 분포

        # -------------------- (1) 카테고리 TOP5 --------------------
        with g1:
            category_counts = (
                first_order_items.groupby("category")["user_id"]
                .nunique()
                .sort_values(ascending=False)
                .head(5)
            )

            fig, ax = plt.subplots(figsize=(4.5, 4))
            bars = ax.bar(
                category_counts.index,
                category_counts.values,
                color="royalblue",
                alpha=0.85,
                edgecolor="white",
                linewidth=0.7
            )

            ax.set_title("첫 구매 상위 5개 카테고리", fontsize=12, fontweight="bold", pad=10)
            ax.set_ylabel("고유 유저 수", fontsize=10)
            ax.set_xlabel("카테고리", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            # 값 표시 (bar_label 사용)
            ax.bar_label(
                bars,
                labels=[f"{v:,}" for v in category_counts.values],
                padding=3,
                fontsize=9,
                color="black",
                fontweight="bold"
            )

            plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)

            plt.tight_layout()
            st.pyplot(fig)

        # -------------------- (2) 첫 구매까지 걸린 기간 분포 --------------------
        # with g2:
        #     fig, ax = plt.subplots(figsize=(4.5, 4))
        #     n, bins, patches = ax.hist(
        #         users_first_purchase["ttfp_days"],
        #         bins=20,
        #         color="#3CB371",
        #         alpha=0.8,
        #         edgecolor="white",
        #         linewidth=0.6
        #     )

        #     ax.set_title("첫 구매까지 걸린 기간 분포", fontsize=12, fontweight="bold", pad=10)
        #     ax.set_xlabel("소요일자 (일 단위)", fontsize=10)
        #     ax.set_ylabel("고유 유저 수", fontsize=10)
        #     ax.grid(axis="y", linestyle="--", alpha=0.4)

        #     # 평균선 추가
        #     mean_ttfp = users_first_purchase["ttfp_days"].mean()
        #     ax.axvline(mean_ttfp, color="red", linestyle="--", linewidth=1.5)

        #     # 👉 평균선 오른쪽으로 살짝 띄운 위치에 텍스트 표시
        #     offset = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.015  # 전체 x축의 1.5% 정도 오른쪽
        #     ax.text(
        #         mean_ttfp + offset,     
        #         ax.get_ylim()[1] * 0.9,   
        #         f"평균 {mean_ttfp:.1f}일",
        #         color="red",
        #         fontsize=9,
        #         ha="left",
        #         va="bottom",
        #         fontweight="bold"
        #     )

        #     for spine in ["top", "right"]:
        #         ax.spines[spine].set_visible(False)

        #     plt.tight_layout()
        #     st.pyplot(fig)


        with g2:
        # -------------------- 첫 구매까지 걸린 기간 분포 --------------------
            fig, ax = plt.subplots(figsize=(4, 3.8))

            # 히스토그램
            n, bins, patches = ax.hist(
                users_first_purchase["ttfp_days"],
                bins=20,
                color="#3CB371",
                alpha=0.8,
                edgecolor="white",
                linewidth=0.6
            )

            # 평균선
            mean_ttfp = users_first_purchase["ttfp_days"].mean()
            ax.axvline(mean_ttfp, color="red", linestyle="--", linewidth=1.5)

            # 평균 텍스트
            ax.text(
                mean_ttfp * 1.02,
                ax.get_ylim()[1] * 0.9,
                f"평균 {mean_ttfp:.1f}일",
                color="red",
                fontsize=9,
                fontweight="bold"
            )

            # 제목 + 축 라벨 + 그리드
            ax.set_title("첫 구매까지 걸린 기간 분포", fontsize=12, fontweight="bold", pad=15)
            ax.set_xlabel("소요일자 (일 단위)", fontsize=10, labelpad=8)
            ax.set_ylabel("고유 유저 수", fontsize=10, labelpad=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            # 외곽선 정리
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)

            # 여백 확보
            plt.subplots_adjust(top=0.88, bottom=0.18, left=0.15, right=0.97)
            st.pyplot(fig, use_container_width=True, clear_figure=True)