import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from matplotlib.ticker import StrMethodFormatter 
import koreanize_matplotlib
from style_config import apply_common_style, HIGHLIGHT_COLOR,SECONDARY_COLOR, SEQUENTIAL_PALETTE, PRIMARY_COLOR, ACCENT_COLOR_2

@st.cache_data
def create_purchase_distribution_chart(order_items_df):
    """사용자별 구매 횟수 분포를 계산하고 막대그래프를 생성합니다."""
    
    # 'Complete' 상태인 주문만 필터링
    completed_orders = order_items_df[order_items_df['status'] == 'Complete']
    
    if completed_orders.empty:
        st.warning("분석할 완료된 주문 데이터가 없습니다.")
        return None, None
        
    # 사용자별 구매 횟수 계산 (user_id별로 그룹화 후 order_id의 고유 개수 계산)
    user_purchase_counts = completed_orders.groupby('user_id')['order_id'].nunique()
    
    # 구매 횟수별 사용자 수 분포 계산
    purchase_dist = user_purchase_counts.value_counts().sort_index()

    # --- Matplotlib 차트 생성 ---
    fig, ax = plt.subplots(figsize=(12, 7))
    purchase_dist.plot(kind='bar', ax=ax, color=HIGHLIGHT_COLOR)
    
    ax.set_xlabel("사용자당 총 구매 횟수", fontsize=12)
    ax.set_ylabel("사용자 수", fontsize=12)
    ax.tick_params(axis='x', rotation=0)
    
    fig.tight_layout()
    
    return fig, purchase_dist


@st.cache_data
# 수정: year 파라미터 제거
def create_advanced_cohort_heatmap(orders_df, max_age_m, show_annotations=True):
    """
    정교한 방식으로 코호트 재구매율을 계산하고 히트맵을 생성합니다.
    """
    # (앞부분 로직은 동일)
    use_cols = [c for c in ['user_id', 'created_at', 'status'] if c in orders_df.columns]
    # if not use_cols or 'user_id' not in use_cols or 'created_at' not in use_cols:
    #     st.warning("분석에 필요한 'user_id', 'created_at' 컬럼이 데이터에 없습니다.")
    #     return None, None
    src = orders_df.loc[:, use_cols].copy()
    if 'status' in src.columns:
        src['status'] = src['status'].astype(str).str.strip().str.lower()
        src = src[src['status'] == 'complete']
        src = src.drop(columns=['status'])
    # if src.empty:
    #     st.warning("상태가 'Complete'인 주문이 없습니다.")
    #     return None, None
    src = src[src['user_id'].notna()].copy()
    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at'])
    if src.empty:
        st.warning("유효한 주문 시간이 있는 데이터가 없습니다.")
        return None, None
    last_month = src['created_at'].dt.to_period('M').max()
    last_i = last_month.year * 12 + last_month.month

    # 사용자별 첫 구매월 산출
    first = (
        src.groupby('user_id', as_index=False)['created_at']
        .min().rename(columns={'created_at':'first_time'})
    )
    first['cohort_month'] = first['first_time'].dt.to_period('M')
    first['cohort_year']  = first['cohort_month'].dt.year

    first_2023 = first[first['cohort_year'] == 2023].copy()
    
    # 수정: 연도 필터링 로직 제거 (모든 코호트 사용)
    # first_year = first[first['cohort_year'] == year].copy()
    # if first_year.empty: ...
        
    cohort_size = first_2023.groupby('cohort_month')['user_id'].nunique().rename('cohort_size')

    # 주문에 코호트 라벨 붙이기
    lab = src.merge(first_2023[['user_id','cohort_month']], on='user_id', how='inner')
    if lab.empty:
        st.warning("코호트 그룹의 주문 내역이 없습니다.")
        return None, None
    lab['order_month'] = lab['created_at'].dt.to_period('M')

    # (이하 계산 로직은 이전과 동일)
    cm_i = lab['cohort_month'].dt.year * 12 + lab['cohort_month'].dt.month
    om_i = lab['order_month'].dt.year * 12 + lab['order_month'].dt.month
    lab['cohort_age_m'] = om_i - cm_i
    lab = lab[(lab['cohort_age_m'] >= 0) & (lab['cohort_age_m'] <= max_age_m)].copy()

    cohort_months = np.sort(first_2023['cohort_month'].unique()) # 2023년 데이터만 사용
    age_vals = np.arange(0, max_age_m + 1)
    grid = pd.MultiIndex.from_product([cohort_months, age_vals], names=['cohort_month','cohort_age_m']).to_frame(index=False)
    grid['cm_i'] = grid['cohort_month'].dt.year * 12 + grid['cohort_month'].dt.month
    grid['order_i'] = grid['cm_i'] + grid['cohort_age_m']
    grid = grid[grid['order_i'] <= last_i].drop(columns=['cm_i','order_i'])

    counts = (lab.groupby(['cohort_month','cohort_age_m'])['user_id']
            .nunique().rename('active_users').reset_index())
    counts = grid.merge(counts, on=['cohort_month','cohort_age_m'], how='left').fillna({'active_users': 0})

    counts = counts.merge(cohort_size, on='cohort_month', how='left')
    counts['retention_rate'] = counts['active_users'] / counts['cohort_size'] 

    heat = counts.pivot(index='cohort_month', columns='cohort_age_m', values='retention_rate')
    heat = heat.sort_index().sort_index(axis=1)
    if 0 in heat.columns:
        heat = heat.loc[:, heat.columns != 0]

    idx_period = heat.index.copy()
    base_labels = idx_period.astype(str)
    n_map = cohort_size.reindex(idx_period).fillna(0).astype(int).map(lambda x: f"{x:,}")
    row_labels = base_labels + ' · N=' + n_map
    heat.index = row_labels
    heat_pct = heat * 100

    # 히트맵 시각화
    fig, ax = plt.subplots(figsize=(12, max(4, 0.6 * len(heat_pct.index))))

    sns.heatmap(
        heat_pct, annot=show_annotations, fmt=".1f", cmap=SEQUENTIAL_PALETTE,
        cbar_kws={'label': '재구매율 (%)'}, linewidths=.3, linecolor='white', ax=ax
    )
    ax.set_xlabel("첫 구매 후 경과 개월 수")
    ax.set_ylabel("코호트 월 (첫 구매월 · N=표본크기)")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    # 제목에 2023년 명시
    apply_common_style(fig, ax, title="2023년 월별 코호트 재구매율 히트맵 (Age≥1)")
    fig.tight_layout()

    return fig, heat

def create_repeat_purchaser_chart(orders_df):
    """
    2023년 월별 재구매자 비율을 분석하고 이중 축 그래프를 생성합니다.
    """
    # (앞부분 데이터 처리 로직은 동일)
    use_cols = [c for c in ['user_id', 'created_at', 'status'] if c in orders_df.columns]
    orders = orders_df.loc[:, use_cols].copy()
    orders = orders[orders['user_id'].notna()].copy()
    orders['created_at'] = pd.to_datetime(orders['created_at'], utc=True, errors='coerce')
    orders = orders.dropna(subset=['created_at'])
    if 'status' in orders.columns:
        # --- 수정: 필터링할 주문 상태 확장 ---
        orders['status'] = orders['status'].astype(str).str.strip().str.lower()
        orders = orders[orders['status'] == 'complete'].drop(columns=['status'])
    if orders.empty:
        st.warning("상태가 'Complete'인 주문이 없습니다.")
        return None, None

    first_time = orders.groupby('user_id', as_index=False)['created_at'].min().rename(columns={'created_at': 'first_time'})
    first_time['cohort_month'] = first_time['first_time'].dt.to_period('M')
    purch = orders[['user_id','created_at']].copy()
    purch['order_month'] = purch['created_at'].dt.to_period('M')
    purch = purch.drop_duplicates(['user_id','order_month'])
    purch = purch.merge(first_time[['user_id','cohort_month']], on='user_id', how='left')
    purch['is_returning'] = purch['cohort_month'] < purch['order_month']
    by_month = purch.groupby('order_month')['is_returning'].agg(returning_users='sum', purchasers='count').sort_index()
    by_month['rate_raw'] = by_month['returning_users'] / by_month['purchasers']
    by_month['repeat_purchaser_rate'] = by_month['rate_raw'].round(3)

    # 수정: 2023년으로 연도 고정
    m2023 = by_month.loc[by_month.index.year == 2023].copy()
    if m2023.empty:
        st.warning("2023년 데이터가 없습니다.")
        return None, None
    m2023.index = m2023.index.astype(str)

    # (이하 시각화 코드는 이전과 동일)
    fig, ax1 = plt.subplots(figsize=(13, 5))
    x = np.arange(len(m2023))
    months = m2023.index.to_list()
    bars = ax1.bar(x, m2023['purchasers'], width=0.6, color=HIGHLIGHT_COLOR, alpha=0.9, label='총 구매자 수')
    ax1.set_ylabel('총 구매자 수')
    ax1.set_xlabel('주문월 (YYYY-MM)')
    ax1.set_xticks(x); ax1.set_xticklabels(months, rotation=45, ha='right')
    ax2 = ax1.twinx()
    rate_pct = m2023['rate_raw'] * 100.0
    ax2.plot(x, rate_pct, marker='o', linewidth=2, color=PRIMARY_COLOR, markerfacecolor='white', label='재구매자 비율')
    ax2.set_ylabel('재구매자 비율 (%)')
    ax2.set_ylim(0, max(5, np.ceil(rate_pct.max()/5)*5))
    for rect, n in zip(bars, m2023['purchasers']):
        ax1.text(rect.get_x() + rect.get_width()/2, rect.get_height()*0.5, f"{int(n):,}", ha='center', va='center', color='black', fontsize=9, fontweight='bold')
    for xi, rp in zip(x, rate_pct):
        ax2.annotate(f"{rp:.1f}%", xy=(xi, rp), xytext=(0, 6), textcoords='offset points', ha='center', va='bottom', fontsize=9, color='tab:blue', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.8))
    is_nov_dec = [m.endswith(('-11','-12')) for m in months]
    is_jan_oct = [not f for f in is_nov_dec]
    if any(is_jan_oct):
        early_ret = m2023.loc[is_jan_oct, 'returning_users'].sum()
        early_tot = m2023.loc[is_jan_oct, 'purchasers'].sum()
        early_avg_w = (early_ret / early_tot) * 100.0
        ax2.hlines(early_avg_w, -0.5, len(x)-0.5, colors='gray', linestyles='dashed', linewidth=1.5, label='1-10월 평균 (가중)')
    if any(is_nov_dec):
        late_ret  = m2023.loc[is_nov_dec, 'returning_users'].sum()
        late_tot  = m2023.loc[is_nov_dec, 'purchasers'].sum()
        late_avg_w  = (late_ret / late_tot)  * 100.0
        ax2.hlines(late_avg_w, -0.5, len(x)-0.5, colors='orange', linestyles='dashed', linewidth=1.5, label='11-12월 평균 (가중)')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(1.055, 1.0))
    apply_common_style(fig, ax1, title="2023년 월별 재구매자 비율")
    fig.tight_layout(rect=[0,0,0.86,1])

    return fig, m2023

@st.cache_data
def create_daily_cohort_heatmap(orders_df, selected_month, selected_week, max_age_d, show_annotations=True):
    """
    일 단위 코호트 재구매율을 계산하고 월/주 필터를 적용하여 히트맵을 생성합니다.
    """
    # --- 제공해주신 코드 로직을 스트림릿 함수에 맞게 수정 ---
    
    # 0) 원천 정리
    use_cols = [c for c in ['user_id', 'created_at', 'status'] if c in orders_df.columns]
    src = orders_df.loc[:, use_cols].copy()
    src = src[src['user_id'].notna()]
    src['status'] = src['status'].astype(str).str.strip().str.lower()
    src = src[src['status'] == 'complete'].drop(columns=['status'])
    if src.empty:
        st.warning("상태가 'Complete'인 주문이 없습니다.")
        return None, None
    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at']).sort_values(['user_id','created_at'])
    if src.empty:
        st.warning("유효한 주문 시간이 있는 데이터가 없습니다.")
        return None, None
    src['order_day'] = src['created_at'].dt.floor('D')
    last_day = src['order_day'].max()

    # 1) 코호트(첫 구매 일자) 계산
    first = (
        src.groupby('user_id', as_index=False)['order_day']
        .min().rename(columns={'order_day':'cohort_day'})
    )
    first_2023 = first[first['cohort_day'].dt.year == 2023].copy()
    first['cohort_month'] = first['cohort_day'].dt.to_period('M').astype(str)
    
    # 수정: 선택된 월/주로 코호트 필터링
    cohorts_filtered = first_2023[first_2023['cohort_month'] == selected_month]
    if selected_week != 'All':
        cohorts_filtered = cohorts_filtered[cohorts_filtered['cohort_week_of_month'] == selected_week]
    
    if cohorts_filtered.empty:
        st.warning(f"선택된 조건에 맞는 코호트 그룹이 없습니다.")
        return None, None
        
    cohort_size = cohorts_filtered.groupby('cohort_day')['user_id'].nunique().rename('cohort_size')

    # (이하 계산 로직은 이전과 동일하나, 'cohorts_filtered'를 사용)
    lab = src.merge(cohorts_filtered[['user_id','cohort_day']], on='user_id', how='inner')
    lab['age_d'] = (lab['order_day'] - lab['cohort_day']).dt.days
    lab = lab[(lab['age_d'] >= 0) & (lab['age_d'] <= max_age_d)].copy()
    cohort_days = np.sort(cohorts_filtered['cohort_day'].unique())
    age_vals = np.arange(0, max_age_d+1)
    grid = pd.MultiIndex.from_product([cohort_days, age_vals], names=['cohort_day','age_d']).to_frame(index=False)
    grid['order_day'] = grid['cohort_day'] + pd.to_timedelta(grid['age_d'], unit='D')
    grid = grid[grid['order_day'] <= last_day].drop(columns=['order_day'])
    counts = (lab.groupby(['cohort_day','age_d'])['user_id']
            .nunique().rename('active_users').reset_index())
    counts = grid.merge(counts, on=['cohort_day','age_d'], how='left').fillna({'active_users':0})
    counts = counts.merge(cohort_size, on='cohort_day', how='left')
    counts['retention_rate'] = counts['active_users'] / counts['cohort_size']

    # 시각화 데이터 준비 (Age=0 제외)
    min_age_d = 1
    col_range = list(range(min_age_d, max_age_d + 1))
    heat = counts.pivot(index='cohort_day', columns='age_d', values='retention_rate').sort_index().reindex(columns=col_range)
    if heat.empty:
        st.warning("선택된 조건의 재구매 데이터가 없습니다.")
        return None, None
        
    # 라벨 생성
    def make_row_labels(days_index: pd.Index) -> pd.Series:
        idx = pd.Series(days_index, index=days_index)
        week_start = idx.dt.normalize() - pd.to_timedelta(idx.dt.dayofweek, unit='D')
        wom = ((week_start.dt.day - 1) // 7 + 1)
        dow_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}
        dow_eng = idx.dt.dayofweek.map(dow_map)
        date_str = idx.dt.date.astype(str)
        return date_str + ' (' + dow_eng + ', W' + wom.astype(str) + ')'
        
    idx_dt = heat.index
    base_lbl = make_row_labels(idx_dt)
    n_map = cohort_size.reindex(idx_dt).fillna(0).astype(int).map(lambda x: f"{x:,}")
    heat.index = base_lbl + ' · N=' + n_map
    heat_pct = heat * 100

    # Figure 높이 동적 조절 (행당 할당 높이를 1.2로 대폭 증가)
    base_height = 8
    row_height_factor = 1.2  # 수정: 각 행의 높이를 더욱 확보
    fig_h = max(base_height, len(heat_pct.index) * row_height_factor)
    
    # Figure 너비 동적 조절
    base_width = 12
    col_width_factor = 0.9
    fig_w = max(base_width, len(heat_pct.columns) * col_width_factor)
    
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    
    month_max = heat.max().max() if not heat.empty else 0.01
    vmax = float(month_max * 100.0) if month_max > 0 else 1.0

    sns.heatmap(
        heat_pct, 
        annot=show_annotations, 
        fmt=".1f",
        cmap=SEQUENTIAL_PALETTE,
        vmin=0, 
        vmax=vmax,
        linewidths=.5, # 선 굵기
        linecolor='white',
        cbar_kws={'label': '재구매율 (%)'}, 
        ax=ax,
        # 수정: annot_kws를 사용하여 annotation 글꼴 크기를 14로 증가
        annot_kws={"fontsize": 20} 
    )
    ax.set_xlabel(f"첫 구매 후 경과 일 수 ({min_age_d}–{max_age_d})", fontsize=30)
    ax.set_ylabel("코호트", fontsize=14)
    ax.tick_params(axis='both', which='major', labelsize=20) # 축 틱 라벨 크기 일괄 조절
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    apply_common_style(fig, ax, title=f"{selected_month} 일일 코호트 재구매율 (Age≥1)")
    fig.tight_layout()

    return fig, heat

# --- Helper 함수들 (분석 함수 내부에 포함시키거나 전역으로 둠) ---
def fmt_pct3(x):
    if pd.isna(x): return "NA"
    return f"{x*100:.3f}%"

def agg_weekday(series_wd, df):
    g = (df.groupby(series_wd, as_index=False).agg(Repeat_Orders=('active_users','sum'), Exposure=('cohort_size','sum')))
    g = (g.set_index(series_wd.name).reindex(range(7)).fillna(0.0).reset_index().rename(columns={'index': series_wd.name}))
    g['Repeat_Rate'] = np.where(g['Exposure'] > 0, g['Repeat_Orders'] / g['Exposure'], np.nan)
    g['Weekday'] = g[series_wd.name].map({0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'})
    return g.sort_values(series_wd.name).reset_index(drop=True)

def set_padded_ylim(ax, *series, low_pad=0.15, high_pad=0.25, min_range=1e-6):
    vals = np.concatenate([np.array([v for v in s if pd.notna(v)]) for s in series if len(s)])
    if vals.size == 0: return
    y_min, y_max = float(vals.min()), float(vals.max())
    rng = max(y_max - y_min, min_range)
    ax.set_ylim(max(0.0, y_min - low_pad*rng), y_max + high_pad*rng)

@st.cache_data
def create_weekday_repeat_purchase_charts(orders_df, start_date, end_date):
    """
    요일별 재구매 패턴을 분석하고 3개의 차트를 포함한 Figure를 생성합니다.
    """
    # (앞부분 로직은 동일)
    use_cols = [c for c in ['user_id','created_at','status'] if c in orders_df.columns]
    # if not use_cols or 'user_id' not in use_cols or 'created_at' not in use_cols:
    #     st.warning("분석에 필요한 'user_id', 'created_at' 컬럼이 데이터에 없습니다.")
    #     return None, None
    src = orders_df.loc[:, use_cols].copy()
    src = src[src['user_id'].notna()]
    src['status'] = src['status'].astype(str).str.strip().str.lower()
    src = src[src['status'] == 'complete'].drop(columns=['status'])
    if src.empty:
        raise ValueError("status == 'Complete' 조건을 만족하는 주문이 없습니다.")

    # 시간 파싱 + 일자 단위
    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at']).sort_values(['user_id','created_at'])
    if src.empty:
        raise ValueError("회원/시간 파싱 후 사용 가능한 주문이 없습니다.")

    src['order_day'] = src['created_at'].dt.floor('D')
    last_day = src['order_day'].max()

    # 사용자별 첫 구매월 산출
    first = (
    src.groupby('user_id', as_index=False)['order_day']
       .min().rename(columns={'order_day':'cohort_day'})
    )
    first_2023 = first[first['cohort_day'].dt.year == 2023].copy()
    cohort_size = first_2023.groupby('cohort_day')['user_id'].nunique().rename('cohort_size')

    # 3) 주문에 코호트 라벨 조인 + 코호트 에이지(주)
    lab = src.merge(first_2023[['user_id','cohort_day']], on='user_id', how='inner')
    lab['age_d'] = (lab['order_day'] - lab['cohort_day']).dt.days
    lab = lab[(lab['age_d'] >= 0) & (lab['age_d'] <= 31)].copy()

    # 4) 관측 가능한 셀만 유지 (오른쪽 검열 제거)
    cohort_days = np.sort(first_2023['cohort_day'].unique())
    age_vals    = np.arange(0, 31+1)  # 계산은 Age 0 포함
    grid = pd.MultiIndex.from_product([cohort_days, age_vals],
                                    names=['cohort_day','age_d']).to_frame(index=False)
    grid['order_day'] = grid['cohort_day'] + pd.to_timedelta(grid['age_d'], unit='D')
    grid = grid[grid['order_day'] <= last_day].drop(columns=['order_day'])

    # 5) (cohort_week_idx, age_w)별 활성 사용자 수(고유 user_id)
    counts = (lab.groupby(['cohort_day','age_d'])['user_id']
            .nunique().rename('active_users').reset_index())
    counts = grid.merge(counts, on=['cohort_day','age_d'], how='left').fillna({'active_users':0})

    # 6) Repeat Purchase Rate 계산
    counts = counts.merge(cohort_size, on='cohort_day', how='left')
    counts['retention_rate'] = counts['active_users'] / counts['cohort_size']  # 내부 변수명 유지


    # --- 제공해주신 코드 로직 (Prep, Aggregations) ---
    df = counts.copy()
    df = df[df['age_d'] >= 1].copy()  # exclude same-day
    df['cohort_day'] = pd.to_datetime(df['cohort_day'], utc=True, errors='coerce')
    df = df.dropna(subset=['cohort_day'])
        
    # Weekday keys
    df['repurch_date'] = df['cohort_day'] + pd.to_timedelta(df['age_d'], unit='D')
    df['order_wd']     = df['repurch_date'].dt.dayofweek     # 구매(재구매) 발생 요일
    df['cohort_wd']    = df['cohort_day'].dt.dayofweek       # 첫 구매(코호트 시작) 요일
    WD_LABELS = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}
        
    # ---------------- Aggregations ----------------
    order_grp  = agg_weekday(df['order_wd'],  df)   # 구매일 기준
    cohort_grp = agg_weekday(df['cohort_wd'], df)   # 코호트 시작일 기준
        


    # --- 시각화 ---

    # fig, (ax_line_both,) = plt.subplots(1, 1, figsize=(18, 5.5), constrained_layout=True)
    fig, ax_line_both = plt.subplots(1, 1, figsize=(18, 5.5), constrained_layout=True)

    x = np.arange(7)
    week_labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    # 1) 그릴 때만 퍼센트 단위로 변환 (0~1 → 0~100)
    order_rate_pct  = order_grp['Repeat_Rate']  * 100
    cohort_rate_pct = cohort_grp['Repeat_Rate'] * 100

    # 2) 라인 그래프
    ax_line_both.plot(x, order_rate_pct,  marker='o', color=PRIMARY_COLOR,   label='재구매일 기준')
    ax_line_both.plot(x, cohort_rate_pct, marker='o', color=ACCENT_COLOR_2,  label='첫구매일 기준')

    # 3) 축/레이블
    ax_line_both.set(
        ylabel="재구매율 (%)",
        xticks=x,
        xticklabels=week_labels
    )

    # 🔹 y축 범위/눈금 직접 세팅
    all_vals = np.r_[order_rate_pct.values, cohort_rate_pct.values]
    max_val  = float(np.nanmax(all_vals)) if all_vals.size else 0.1

    # 예: 최대값이 0.15% 정도면 0.20%까지 보이게
    ylim_max = max(0.20, np.ceil(max_val * 10) / 10)   # 0.1 단위 올림
    ax_line_both.set_ylim(0, ylim_max)

    # 0.00%, 0.05%, 0.10% ... 이런 식으로 보이게
    yticks = np.linspace(0, ylim_max, 5)
    ax_line_both.set_yticks(yticks)

    # 🔹 소수 둘째 자리까지 보여주기 (0.08% 등)
    ax_line_both.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}%"))

    ax_line_both.legend(loc='best')
    apply_common_style(fig, ax_line_both, title="요일별 재구매율")

    return fig, order_grp, cohort_grp
    # # --- 시각화 ---

    # fig, (ax_line_both,) = plt.subplots(1, 1, figsize=(18, 5.5), constrained_layout=True)
    
    # x = np.arange(7)
    # week_labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    # # 1) 그릴 때만 퍼센트 단위로 변환 (0~1 → 0~100)
    # order_rate_pct  = order_grp['Repeat_Rate']  * 100
    # cohort_rate_pct = cohort_grp['Repeat_Rate'] * 100

    # # 2) 라인 그래프 그리기
    # ax_line_both.plot(
    #     x,
    #     order_rate_pct,
    #     marker='o',
    #     color=PRIMARY_COLOR,
    #     label='재구매일 기준'
    # )
    # ax_line_both.plot(
    #     x,
    #     cohort_rate_pct,
    #     marker='o',
    #     color=ACCENT_COLOR_2,
    #     label='첫구매일 기준'
    # )

    # # 3) 축/레이블 설정
    # ax_line_both.set(
    #     ylabel="재구매율 (%)",
    #     xticks=x,
    #     xticklabels=week_labels
    # )

    # # 4) y축 포맷을 '숫자 + %' 형태로 직접 지정
    # ax_line_both.yaxis.set_major_formatter(StrMethodFormatter("{x:.1f}%"))

    # # 5) y축 범위는 퍼센트 값 기준으로 여유 있게 패딩
    # set_padded_ylim(ax_line_both, order_rate_pct.values, cohort_rate_pct.values)

    # ax_line_both.legend(loc='best')
    # apply_common_style(fig, ax_line_both, title="요일별 재구매율")
    
    # return fig, order_grp, cohort_grp

    # --- 시각화 ---
    # fig, (  ax_line_both) = plt.subplots(1, 1, figsize=(18, 5.5), constrained_layout=True)
    
    # x = np.arange(7)
    # week_labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    # # Plot 3: Combined lines
    # ax_line_both.plot(x, order_grp['Repeat_Rate'], marker='o', color=PRIMARY_COLOR, label='재구매일 기준')
    # ax_line_both.plot(x, cohort_grp['Repeat_Rate'], marker='o', color=ACCENT_COLOR_2, label='첫구매일 기준')
    # ax_line_both.set(ylabel="재구매율 (%)", xticks=x, xticklabels=week_labels)
    # ax_line_both.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=1))
    # set_padded_ylim(ax_line_both, order_grp['Repeat_Rate'].values, cohort_grp['Repeat_Rate'].values)
    # ax_line_both.legend(loc='best')
    # apply_common_style(fig, ax_line_both, title="요일별 재구매율")
    
    # return fig, order_grp, cohort_grp

@st.cache_data
def create_hourly_hau_repeat_rate_chart(orders_df):
    """
    2023년 기준 시간대별 HAU(유니크 구매자 수)와 재구매율을 함께 보여주는 라인 차트 생성.
    """
    # 필요한 컬럼만 사용
    use_cols = [c for c in ['user_id', 'created_at', 'status'] if c in orders_df.columns]
    src = orders_df.loc[:, use_cols].copy()
    src = src[src['user_id'].notna()]

    # 주문 상태 필터
    if 'status' in src.columns:
        src['status'] = src['status'].astype(str).str.strip().str.lower()
        src = src[src['status'] == 'complete'].drop(columns=['status'])

    if src.empty:
        st.warning("상태가 'Complete'인 주문이 없습니다.")
        return None, None

    # 시간 파싱
    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at'])
    if src.empty:
        st.warning("유효한 주문 시간이 없습니다.")
        return None, None

    # 2023년 데이터만 사용
    src_2023 = src[src['created_at'].dt.year == 2023].copy()
    if src_2023.empty:
        st.warning("2023년 주문 데이터가 없습니다.")
        return None, None

    # 사용자별 첫 구매 시각
    first = (
        src_2023.groupby('user_id', as_index=False)['created_at']
        .min()
        .rename(columns={'created_at': 'first_time'})
    )

    lab = src_2023.merge(first, on='user_id', how='inner')
    lab['is_repeat'] = lab['created_at'] > lab['first_time']
    lab['hour'] = lab['created_at'].dt.hour  # 0~23시

    # 0~23시 전체를 인덱스로 맞추기
    hours_idx = pd.Index(range(24), name='hour')
    agg = (
        lab.groupby('hour')
           .agg(
               HAU=('user_id', 'nunique'),
               total_orders=('user_id', 'count'),
               repeat_orders=('is_repeat', 'sum')
           )
           .reindex(hours_idx, fill_value=0)
           .reset_index()
    )

    # 재구매율 계산
    agg['repeat_rate'] = np.where(
        agg['total_orders'] > 0,
        agg['repeat_orders'] / agg['total_orders'],
        np.nan
    )

    # 19–23시는 재구매율 관측 불가로 처리 (라인 끊기게 NaN)
    agg.loc[agg['hour'].between(19, 23), 'repeat_rate'] = np.nan

    # ---------------- 시각화 ----------------
    fig, ax1 = plt.subplots(figsize=(12, 5))

    x = agg['hour']

    # 왼쪽 축: HAU
    line1 = ax1.plot(
        x,
        agg['HAU'],
        marker='o',
        linewidth=2,
        color=HIGHLIGHT_COLOR,
        label='HAU (유니크 구매자 수)'
    )
    ax1.set_xlabel("시간대 (시)")
    ax1.set_ylabel("HAU (유니크 구매자 수)")

    # 오른쪽 축: 재구매율
    ax2 = ax1.twinx()
    line2 = ax2.plot(
        x,
        agg['repeat_rate'],
        marker='s',
        linewidth=2,
        color=PRIMARY_COLOR,
        label='재구매율'
    )
    ax2.set_ylabel("재구매율 (%)")
    ax2.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=1))

    # 범례 합치기
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')

    apply_common_style(fig, ax1, title="2023년 HAU & 시간대별 재구매율")
    fig.tight_layout()

    return fig, agg



# Helper 함수들
def fmt_pct3(x):
    if pd.isna(x): return "NA"
    return f"{x*100:.3f}%"

# @st.cache_data
# def create_weekday_weekend_chart(orders_df, start_date, end_date):
#     """
#     선택된 기간의 데이터를 기반으로 주중/주말 재구매 패턴을 분석하고 시각화합니다.
#     """
#     # (앞부분 로직은 동일)
#     use_cols = [c for c in ['user_id','created_at','status'] if c in orders_df.columns]

#     src = orders_df.loc[:, use_cols].copy()
#     src = src[src['user_id'].notna()]
#     src['status'] = src['status'].astype(str).str.strip().str.lower()
#     src = src[src['status'] == 'complete'].drop(columns=['status'])
#     if src.empty:
#         raise ValueError("status == 'Complete' 조건을 만족하는 주문이 없습니다.")

#     # 시간 파싱 + 일자 단위
#     src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
#     src = src.dropna(subset=['created_at']).sort_values(['user_id','created_at'])
#     if src.empty:
#         raise ValueError("회원/시간 파싱 후 사용 가능한 주문이 없습니다.")

#     src['order_day'] = src['created_at'].dt.floor('D')
#     last_day = src['order_day'].max()

#     # 사용자별 첫 구매월 산출
#     first = (
#     src.groupby('user_id', as_index=False)['order_day']
#        .min().rename(columns={'order_day':'cohort_day'})
#     )
#     first_2023 = first[first['cohort_day'].dt.year == 2023].copy()
#     cohort_size = first_2023.groupby('cohort_day')['user_id'].nunique().rename('cohort_size')

#     # 3) 주문에 코호트 라벨 조인 + 코호트 에이지(주)
#     lab = src.merge(first_2023[['user_id','cohort_day']], on='user_id', how='inner')
#     lab['age_d'] = (lab['order_day'] - lab['cohort_day']).dt.days
#     lab = lab[(lab['age_d'] >= 0) & (lab['age_d'] <= 31)].copy()

#     # 4) 관측 가능한 셀만 유지 (오른쪽 검열 제거)
#     cohort_days = np.sort(first_2023['cohort_day'].unique())
#     age_vals    = np.arange(0, 31+1)  # 계산은 Age 0 포함
#     grid = pd.MultiIndex.from_product([cohort_days, age_vals],
#                                     names=['cohort_day','age_d']).to_frame(index=False)
#     grid['order_day'] = grid['cohort_day'] + pd.to_timedelta(grid['age_d'], unit='D')
#     grid = grid[grid['order_day'] <= last_day].drop(columns=['order_day'])

#     # 5) (cohort_week_idx, age_w)별 활성 사용자 수(고유 user_id)
#     counts = (lab.groupby(['cohort_day','age_d'])['user_id']
#             .nunique().rename('active_users').reset_index())
#     counts = grid.merge(counts, on=['cohort_day','age_d'], how='left').fillna({'active_users':0})

#     # 6) Repeat Purchase Rate 계산
#     counts = counts.merge(cohort_size, on='cohort_day', how='left')
#     counts['retention_rate'] = counts['active_users'] / counts['cohort_size']  # 내부 변수명 유지


#     # --- 제공해주신 코드 로직 (Prep, Aggregations) ---
#     df = counts.copy()
#     df = df[df['age_d'] >= 1].copy()
#     if df.empty:
#         st.warning("재구매 데이터(Age≥1)가 없습니다.")
#         return None, None
        
#     df['cohort_day'] = pd.to_datetime(df['cohort_day'], utc=True, errors='coerce')
#     df = df.dropna(subset=['cohort_day'])
#     df['repurch_date'] = df['cohort_day'] + pd.to_timedelta(df['age_d'], unit='D')
#     df['repurch_wd'] = df['repurch_date'].dt.dayofweek
#     df['is_weekend'] = df['repurch_wd'].isin({5,6})

#     g = (df.groupby('is_weekend', as_index=False)
#            .agg(Repeaters=('active_users','sum'), Exposure=('cohort_size','sum')))
#     g['Rate'] = np.where(g['Exposure']>0, g['Repeaters']/g['Exposure'], np.nan)
#     # ✨ 표/그래프 라벨: 토+일 -> 토-일
#     g['Group'] = np.where(g['is_weekend'], '주말 (토-일)', '주중 (월-금)')
#     g = g.sort_values('is_weekend').reset_index(drop=True)

#     # ✨ 테이블 생성: 재구매율 소수 셋째 자리까지
#     tbl = pd.DataFrame({
#         '구분': g['Group'],
#         '재구매자 수': g['Repeaters'].astype(int),
#         '전체 코호트 크기': g['Exposure'].astype(int),
#         '재구매율 (%)': (g['Rate']*100).round(3)   # 예: 0.074, 0.083
#     })

#     # ✨ 막대 차트 생성 (파랑 + 하늘색 계열 가정)
#     fig, ax = plt.subplots(figsize=(7, 5))
#     bars = ax.bar(
#         g['Group'],
#         g['Rate'],
#         color=[PRIMARY_COLOR, HIGHLIGHT_COLOR],
#         edgecolor='none'
#     )


#     # 눈금은 그대로 0.00%, 0.02%, 0.04%, 0.06%, 0.08% 유지
#     ax.set_yticks([0.0, 0.0002, 0.0004, 0.0006, 0.0008])

#     # y축 범위: 최소 0.08%는 보장하되, 실제 최대값보다 조금 여유 있게
#     max_rate = float(np.nanmax(g['Rate'])) if len(g) else 0.0
#     ymax = max(0.0008, max_rate * 1.1)  # 실제 값보다 10% 정도 여유
#     ax.set_ylim(0, ymax)

#     # 눈금은 그대로 0.00%, 0.02%, 0.04%, 0.06%, 0.08% 유지
#     ax.set_yticks([0.0, 0.0002, 0.0004, 0.0006, 0.0008])

#     # 🔹 막대 안쪽에 라벨 넣기 (그래프 안에서 보이도록)
#     for rect, r in zip(bars, g['Rate']):
#         ax.annotate(
#             f"{r*100:.3f}%",
#             xy=(rect.get_x() + rect.get_width()/2, r),
#             xytext=(0, -10),                # 아래쪽으로 10pt 내리기
#             textcoords='offset points',
#             ha='center',
#             va='top',                       # 위를 기준으로 안쪽에 붙이기
#         )

#     ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=2))
#     ax.set_ylabel("재구매율 (%)")
#     apply_common_style(fig, ax, title="주문일 기준 주중 vs 주말 재구매율 비교")
#     fig.tight_layout()

#     return fig, tbl

@st.cache_data
def create_weekday_weekend_chart(orders_df, start_date, end_date):
    """
    선택된 기간의 데이터를 기반으로 주중/주말 재구매 패턴을 분석하고 시각화합니다.
    """

    use_cols = [c for c in ['user_id','created_at','status'] if c in orders_df.columns]

    src = orders_df.loc[:, use_cols].copy()
    src = src[src['user_id'].notna()]
    src['status'] = src['status'].astype(str).str.strip().str.lower()
    src = src[src['status'] == 'complete'].drop(columns=['status'])
    if src.empty:
        st.warning("status == 'Complete' 조건을 만족하는 주문이 없습니다.")
        return None, None

    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at']).sort_values(['user_id','created_at'])

    src['order_day'] = src['created_at'].dt.floor('D')

    # 사용자별 첫 구매일
    first = (
        src.groupby('user_id', as_index=False)['order_day']
           .min().rename(columns={'order_day':'cohort_day'})
    )
    first_2023 = first[first['cohort_day'].dt.year == 2023].copy()
    cohort_size = first_2023.groupby('cohort_day')['user_id'].nunique().rename('cohort_size')

    # 코호트 조인
    lab = src.merge(first_2023[['user_id','cohort_day']], on='user_id', how='inner')
    lab['age_d'] = (lab['order_day'] - lab['cohort_day']).dt.days
    lab = lab[(lab['age_d'] >= 1) & (lab['age_d'] <= 31)].copy()

    # 재구매 발생일
    lab['repurch_date'] = lab['cohort_day'] + pd.to_timedelta(lab['age_d'], unit='D')
    lab['repurch_wd'] = lab['repurch_date'].dt.dayofweek
    lab['is_weekend'] = lab['repurch_wd'].isin({5, 6})

    g = (
        lab.groupby('is_weekend', as_index=False)
           .agg(Repeaters=('user_id','nunique'),
                Exposure=('cohort_day','count'))
    )

    g['Rate'] = g['Repeaters'] / g['Exposure']
    g['Group'] = np.where(g['is_weekend'], '주말 (토-일)', '주중 (월-금)')
    g = g.sort_values('is_weekend').reset_index(drop=True)

    # 📊 테이블 데이터 만들기
    tbl = pd.DataFrame({
        '구분': g['Group'],
        '재구매자 수': g['Repeaters'].astype(int),
        '전체 코호트 크기': g['Exposure'].astype(int),
        '재구매율 (%)': (g['Rate'] * 100).round(3)
    })

    # 그래프: % 스케일로 맞추기
    fig, ax = plt.subplots(figsize=(7, 4.8))

    rate_pct = g['Rate'] * 100  # ← 0.074 → 7.4% 형태 변환

    bars = ax.bar(
        g['Group'],
        rate_pct,
        color=[PRIMARY_COLOR, HIGHLIGHT_COLOR],
        edgecolor='none'
    )

    # Y축 범위 자동 설정 (다른 그래프와 비슷한 느낌)
    ymax = max(rate_pct.max() * 1.25, 0.1)
    ax.set_ylim(0, ymax)

    # 퍼센트 포맷(0.05%, 0.08% 등)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100.0, decimals=2))
    ax.set_ylabel("재구매율 (%)")

    # ✔ 바 레이블 (중앙 위, 검정색)
    for rect, val in zip(bars, rate_pct):
        ax.annotate(
            f"{val:.3f}%",
            xy=(rect.get_x() + rect.get_width() / 2, val),
            xytext=(0, 5),
            textcoords="offset points",
            ha='center',
            va='bottom',
            fontsize=11,
            color='black'
        )

    # 스타일 통일
    apply_common_style(fig, ax, title="주문일 기준 주중 vs 주말 재구매율 비교")
    fig.tight_layout()

    return fig, tbl


@st.cache_data
def create_weekly_cohort_heatmap(orders_df, selected_month, selected_week, max_age_w, show_annotations=True):
    """
    선택된 월/주에 시작된 주간 코호트의 재구매율을 분석하고 히트맵을 생성합니다.
    """
    # --- 제공해주신 코드 로직을 스트림릿 함수에 맞게 수정 ---
    
    # 0) 원천 정리
    use_cols = [c for c in ['user_id', 'created_at', 'status'] if c in orders_df.columns]
    src = orders_df.loc[:, use_cols].copy()
    if 'status' in src.columns:
        src['status'] = src['status'].astype(str).str.strip().str.lower()
        src = src[src['status'] == 'complete']
        src = src.drop(columns=['status'])
    

    src = src[src['user_id'].notna()].copy()
    src['created_at'] = pd.to_datetime(src['created_at'], utc=True, errors='coerce')
    src = src.dropna(subset=['created_at']).sort_values(['user_id','created_at'])
    if src.empty:
        st.warning("유효한 주문 시간이 있는 데이터가 없습니다.")
        return None, None
        
    src['week_start'] = src['created_at'].dt.normalize() - pd.to_timedelta(src['created_at'].dt.dayofweek, unit='D')
    REF = pd.Timestamp('1970-01-05', tz='UTC')   # 월요일
    src['week_idx'] = ((src['week_start'] - REF).dt.days // 7).astype(int)
    last_week_idx = int(src['week_idx'].max())

    # 1) 첫 구매(코호트) 계산
    first = (
        src.groupby('user_id', as_index=False)['created_at']
        .min().rename(columns={'created_at':'first_time'})
    )
    first['cohort_week_start'] = first['first_time'].dt.normalize() - pd.to_timedelta(first['first_time'].dt.dayofweek, unit='D')
    first['cohort_week_idx']   = ((first['cohort_week_start'] - REF).dt.days // 7).astype(int)

    # ── 표시용 라벨: 'YYYY-MM Wn (YYYY-Www)' ──
    iso = first['cohort_week_start'].dt.isocalendar()
    first['cohort_week_lbl'] = iso['year'].astype(str) + '-W' + iso['week'].astype(str).str.zfill(2)
    first['cohort_month']    = first['cohort_week_start'].dt.to_period('M').astype(str)
    first['week_of_month']   = ((first['cohort_week_start'].dt.day - 1) // 7 + 1).astype(int)
    first['cohort_mweek_lbl'] = (
        first['cohort_month'] + ' W' + first['week_of_month'].astype(str)
        + ' (' + first['cohort_week_lbl'] + ')'
    )

    # 2) 2023년 코호트만 사용 (ISO year 기준)
    first_2023 = first[iso['year'] == 2023].copy()
    if first_2023.empty:
        raise ValueError(f"{2023}년 주 코호트가 없습니다. (status=='Complete' 기준)")

    
    # 수정: 선택된 월/주로 코호트 필터링
    cohorts_filtered = first_2023[first_2023['cohort_month'] == selected_month]
    if selected_week != 'All':
        cohorts_filtered = cohorts_filtered[cohorts_filtered['week_of_month'] == selected_week]
    
    if cohorts_filtered.empty:
        st.warning(f"선택된 조건에 맞는 코호트 그룹이 없습니다.")
        return None, None
        
    # 코호트 분모(해당 주 첫구매 회원 수)
    cohort_size = cohorts_filtered.groupby('cohort_week_idx')['user_id'].nunique().rename('cohort_size')  

    # (이하 계산 로직은 이전과 동일하나, 'cohorts_filtered'를 사용)
    lab = src.merge(cohorts_filtered[['user_id','cohort_week_idx']], on='user_id', how='inner')
    if lab.empty: return None, None
    lab['age_w'] = lab['week_idx'] - lab['cohort_week_idx']
    lab = lab[(lab['age_w'] >= 0) & (lab['age_w'] <= 12)].copy()
    cohort_weeks = np.sort(cohorts_filtered['cohort_week_idx'].unique())
    age_vals = np.arange(0, 12+1)
    grid = pd.MultiIndex.from_product([cohort_weeks, age_vals], names=['cohort_week_idx','age_w']).to_frame(index=False)
    grid = grid[(grid['cohort_week_idx'] + grid['age_w']) <= last_week_idx].copy()
    counts = lab.groupby(['cohort_week_idx','age_w'])['user_id'].nunique().rename('active_users').reset_index()
    counts = grid.merge(counts, on=['cohort_week_idx','age_w'], how='left').fillna({'active_users':0})
    counts = counts.merge(cohort_size, on='cohort_week_idx', how='left')
    counts['retention_rate'] = counts['active_users'] / counts['cohort_size']
    heat = counts.pivot(index='cohort_week_idx', columns='age_w', values='retention_rate').sort_index().sort_index(axis=1)
    if 0 in heat.columns:
        heat = heat.loc[:, heat.columns != 0]

    lbl_map = (cohorts_filtered[['cohort_week_idx','cohort_mweek_lbl']].drop_duplicates().set_index('cohort_week_idx')['cohort_mweek_lbl'])
    cohort_idx = heat.index.copy()
    base_labels = cohort_idx.map(lbl_map)
    n_map = cohort_size.reindex(cohort_idx).fillna(0).astype(int).map(lambda x: f"{x:,}")
    row_labels = base_labels + ' · N=' + n_map
    heat.index = row_labels
    heat_pct = heat * 100

    # 히트맵 시각화
    fig, ax = plt.subplots(figsize=(12, max(4, 0.7 * len(heat_pct))))
    sns.heatmap(
        heat_pct, annot=show_annotations, fmt=".1f", cmap=SEQUENTIAL_PALETTE,
        cbar_kws={'label':'재구매율 (%)'}, linewidths=.3, linecolor='white', ax=ax)
    ax.set_xlabel("첫 구매 후 경과 주 수")
    ax.set_ylabel("코호트 주 (YYYY-MM Wn (ISO 주) · N)")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    # 제목을 피드백에 맞게 단순화 진행
    apply_common_style(fig, ax, title="2023년 주간 코호트 재구매율 히트맵")
    fig.tight_layout()

    return fig, heat
