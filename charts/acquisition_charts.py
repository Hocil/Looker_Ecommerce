import streamlit as st
import pandas as pd
from retentioneering.eventstream import Eventstream
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import koreanize_matplotlib
import calendar
from style_config import apply_common_style, PRIMARY_COLOR, SECONDARY_COLOR, CATEGORICAL_PALETTE, DIVERGING_PALETTE, ACCENT_COLOR_1
import plotly.express as px

raw_data_schema={
        'user_id': 'session_id', 'event_name': 'event_type', 'event_timestamp': 'created_at'
    }

# --- 🎨 차트 생성 함수들 (기능별로 분리 및 캐싱) ---

@st.cache_data
# ✨ 수정: start_date, end_date를 인자로 추가
def create_mau_revenue_chart(order_items_df, events_df, start_date, end_date):
    """월별 매출 및 MAU 이중 축 그래프를 생성합니다."""
    # ✨ 수정: 함수 내부에서 날짜 필터링 수행
    order_items_filtered = order_items_df
    events_filtered = events_df

    # (이하 로직은 필터링된 데이터를 사용하도록 수정)
    valid_status = ['Complete', 'Returned', 'Cancelled']
    sales_df = order_items_filtered[order_items_filtered['status'].isin(valid_status)].copy()
    sales_df['month'] = sales_df['created_at'].dt.to_period('M')
    monthly_revenue = sales_df.groupby('month')['sale_price'].sum()
    
    events_filtered['month'] = events_filtered['created_at'].dt.to_period('M')
    mau = events_filtered.groupby('month')['user_id'].nunique()

    combined_df = pd.DataFrame({'Revenue': monthly_revenue, 'MAU': mau}).fillna(0)
    if combined_df.empty: return plt.figure(), pd.DataFrame()
    combined_df.index = combined_df.index.strftime('%Y-%m')
    
    # (그래프 그리는 부분은 이전과 동일)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(combined_df.index, combined_df['Revenue'], color=PRIMARY_COLOR, alpha=0.7, label='매출')
    ax1.set_ylabel('매출 (USD)', color=PRIMARY_COLOR, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=PRIMARY_COLOR)
    ax1.yaxis.set_major_formatter(mticker.StrMethodFormatter('${x:,.0f}'))
    ax1.tick_params(axis='x', rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(combined_df.index, combined_df['MAU'], color=SECONDARY_COLOR, marker='o', linestyle='-', label='MAU')
    ax2.set_ylabel('월간 활성 사용자 수 (MAU)', color=SECONDARY_COLOR, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=SECONDARY_COLOR)
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    apply_common_style(fig, ax1, title='월별 매출 및 활성 사용자 수')
    fig.tight_layout()

    return fig, combined_df

@st.cache_data
# ✨ 수정: start_date, end_date를 인자로 추가
def create_sankey_chart(events_df,start_date, end_date):
    """retentioneering으로 생키 차트를 생성합니다."""
    # ✨ 수정: 함수 내부에서 날짜 필터링 수행
    events_filtered = events_df
    event_stream = Eventstream(events_filtered, raw_data_schema=raw_data_schema)
    fig = event_stream.step_sankey().plot()
    fig.update_traces(textfont=dict(color='black', family='Arial, sans-serif'))
    return fig

@st.cache_data
def create_funnel_chart(events_df, stages,start_date, end_date):
    """retentioneering으로 퍼널 차트를 생성합니다."""
    events_filtered = events_df
    event_stream = Eventstream(events_filtered, raw_data_schema=raw_data_schema)
    
    # --- ✨ 수정: 퍼널 차트 생성 및 색상 적용 ---
    fig = event_stream.funnel(stages = stages).plot()
    
    # Plotly Figure의 marker 속성을 업데이트하여 색상 리스트를 직접 지정
    # style_config에 정의된 색상들을 활용
    fig.update_traces(marker=dict(color=[PRIMARY_COLOR, ACCENT_COLOR_1, SECONDARY_COLOR]))
    fig.update_traces(textfont=dict(color='black', family='Arial, sans-serif'))
    return fig


# --- ✨ [함수 추가] 유입 경로 분석 함수들 ---
@st.cache_data
def create_traffic_distribution_chart(users_df, start_date, end_date):
    """선택된 기간의 전체 유입 경로 분포 막대그래프를 생성합니다."""

    users_filtered = users_df
    if users_filtered.empty: return None, None
    traffic_counts = users_filtered['traffic_source'].value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 6))

    # --- ✨ 수정: 상위 3개와 나머지를 구분하는 색상 팔레트 생성 ---
    palette = [PRIMARY_COLOR if i < 1 else SECONDARY_COLOR for i in range(len(traffic_counts))]
    sns.barplot(x=traffic_counts.index, y=traffic_counts.values, palette=palette, ax=ax)

    ax.set_xlabel('유입 경로 (Traffic Source)', fontsize=12)
    ax.set_ylabel('신규 사용자 수', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    apply_common_style(fig, ax, title='전체 고객 유입 경로 분포')
    fig.tight_layout()
    return fig, traffic_counts

@st.cache_data
def create_monthly_traffic_trends_chart(users_df, start_date, end_date):
    """선택된 기간의 월별 유입 경로 추이 꺾은선 그래프를 생성합니다."""

    users_filtered = users_df
    if users_filtered.empty: return None, None
    users_filtered['month'] = users_filtered['created_at'].dt.month
    traffic_over_time = users_filtered.groupby(['month', 'traffic_source']).size().unstack(fill_value=0)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    traffic_over_time.plot(kind='line', marker='o', ax=ax)
    month_names = [calendar.month_abbr[i] for i in traffic_over_time.index]
    ax.set_xticks(ticks=traffic_over_time.index)
    ax.set_xticklabels(labels=month_names)
    ax.set_xlabel('월', fontsize=12)
    ax.set_ylabel('신규 사용자 수', fontsize=12)
    ax.legend(title='Traffic Source')
    apply_common_style(fig, ax, title='월별 고객 유입 경로 추이')
    fig.tight_layout()
    return fig, traffic_over_time

@st.cache_data
def create_country_chart(users_df, start_date, end_date, traffic_source):
    """국가별 분포 지도 차트(Choropleth) 생성"""
    filtered_users = users_df[users_df['traffic_source'] == traffic_source]

    user_count = len(filtered_users)
    if user_count == 0:
        return None, 0, None

    country_counts = filtered_users['country'].value_counts().reset_index()
    country_counts.columns = ['country', 'user_count']

    fig = px.choropleth(
        country_counts,
        locations="country",
        locationmode='country names',
        color="user_count",
        hover_name="country",
        color_continuous_scale=px.colors.sequential.Blues,
        title="국가별 사용자 분포"
    )
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

    return fig, user_count, country_counts

@st.cache_data
def create_gender_chart(users_df, start_date, end_date, traffic_source):
    """성별 분포 파이 차트 생성"""

    # ✨ 수정: 날짜와 traffic_source로 필터링하는 코드 추가
    filtered_users = users_df[(users_df['traffic_source'] == traffic_source)]

    if filtered_users.empty: return None
    
    gender_counts = filtered_users['gender'].value_counts()
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=90, colors=[PRIMARY_COLOR, SECONDARY_COLOR])
    apply_common_style(fig, ax, title='성별 분포')
    return fig

@st.cache_data
def create_age_chart(users_df, start_date, end_date, traffic_source):
    """연령대별 분포 막대그래프 생성"""

    # ✨ 수정: 날짜와 traffic_source로 필터링하는 코드 추가
    filtered_users = users_df[users_df['traffic_source'] == traffic_source]

    if filtered_users.empty: return None

    age_bins = [10, 20, 30, 40, 50, 60, 70]
    age_labels = ['10-19', '20-29', '30-39', '40-49', '50-59', '60-69']
    filtered_users['age_group'] = pd.cut(filtered_users['age'], bins=age_bins, labels=age_labels, right=False, include_lowest=True)
    age_counts = filtered_users['age_group'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(5, 3))
    sns.barplot(x=age_counts.index, y=age_counts.values, ax=ax, palette=CATEGORICAL_PALETTE)
    ax.set_xlabel('연령대', fontsize=12)
    ax.set_ylabel('사용자 수')
    apply_common_style(fig, ax, title='연령대별 분포')
    fig.tight_layout()
    return fig, age_counts.reset_index()

@st.cache_data
# ==============================================================================
# 분석 함수 1: 유입 경로별 구매 전환율 분석
# ==============================================================================
def analyze_conversion_rate_by_source_2023(users_df, orders_df):
    """유입 경로별 구매 전환율을 분석하고, 결과 데이터프레임과 차트 Figure를 반환합니다."""
    try:
        users_copy = users_df.copy()
        orders_copy = orders_df.copy()

        users_2023 = users_copy
        orders_2023 = orders_copy

        total_users_by_source = users_2023['traffic_source'].value_counts().reset_index()
        total_users_by_source.columns = ['traffic_source', 'total_users']

        purchaser_ids_2023 = orders_2023['user_id'].unique()
        users_2023['is_purchaser'] = users_2023['id'].isin(purchaser_ids_2023)
        
        purchasing_users_by_source = users_2023[users_2023['is_purchaser'] == True]['traffic_source'].value_counts().reset_index()
        purchasing_users_by_source.columns = ['traffic_source', 'purchasing_users']

        conversion_df = pd.merge(total_users_by_source, purchasing_users_by_source, on='traffic_source', how='left')
        conversion_df['purchasing_users'] = conversion_df['purchasing_users'].fillna(0).astype(int)
        conversion_df['conversion_rate (%)'] = (conversion_df['purchasing_users'] / conversion_df['total_users']) * 100
        conversion_df = conversion_df.sort_values(by='conversion_rate (%)', ascending=False).reset_index(drop=True)

        # --- ✨ 수정: 상위 3개와 나머지를 구분하는 색상 팔레트 생성 ---
        # 상위 3개는 PRIMARY_COLOR, 나머지는 SECONDARY_COLOR로 설정
        palette = [PRIMARY_COLOR if i < 1 else SECONDARY_COLOR for i in range(len(conversion_df))]

        # 시각화 (Figure 객체 생성)
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(x='conversion_rate (%)', y='traffic_source', data=conversion_df, palette=DIVERGING_PALETTE,  ax=ax)
        sns.barplot(x='conversion_rate (%)', y='traffic_source', data=conversion_df, palette=palette,  ax=ax)
        ax.set_xlabel('Conversion Rate (%)', fontsize=12)
        ax.set_ylabel('Traffic Source', fontsize=12)
        for index, value in enumerate(conversion_df['conversion_rate (%)']):
            ax.text(value, index, f'{value:.2f}%', va='center')
        apply_common_style(fig, ax, title='유입 경로별 구매 전환율 (2023)')
        
        return conversion_df, fig

    except Exception as e:
        st.error(f"구매 전환율 분석 중 오류: {e}")
        return None, None
    
@st.cache_data
# ✨ 수정: start_date, end_date 대신 selected_month를 인자로 받도록 변경
def calculate_dau_by_month(events_df, selected_month):
    """선택된 월의 DAU 데이터를 계산하여 반환합니다."""
    
    if selected_month == '전체 기간':
        filtered_events = events_df
    else:
        # ✨ 수정: 선택된 'YYYY-MM' 문자열과 일치하는 데이터만 필터링
        filtered_events = events_df[
            events_df['created_at'].dt.to_period('M').astype(str) == selected_month
        ]
    
    if filtered_events.empty:
        return None

    dau = filtered_events.groupby(filtered_events['created_at'].dt.date)['user_id'].nunique()
    dau.index.name = "날짜"
    return dau