# pages/Acquisition.py
import koreanize_matplotlib
import streamlit as st
import pandas as pd

# 데이터 로더는 별도 파일에서 관리 (좋은 방법입니다!)
from data import load_all_data
from charts.acquisition_charts import (
    create_mau_revenue_chart, create_sankey_chart, create_funnel_chart,
    create_traffic_distribution_chart, analyze_conversion_rate_by_source_2023,
    create_country_chart, create_gender_chart, create_age_chart,
    calculate_dau_by_month
) 
from style_config import PRIMARY_COLOR, SECONDARY_COLOR

# --- 메인 대시보드 레이아웃 ---
st.set_page_config(
    page_title="📈 Acquisition 분석",
    layout="wide"
)
st.title("📈 사용자 획득(Acquisition) 분석")
st.write("사용자 유입 및 전환 과정을 분석하여 비즈니스 성과를 파악합니다.")

# --- 데이터 로딩 ---
all_data = load_all_data()

if not all_data:
    st.error("데이터를 불러오는데 실패했습니다. `data` 폴더를 확인해주세요.")
else:
    events = all_data["events"]
    order_items = all_data["order_items"]
    users = all_data["users"]
    orders = all_data["orders"]

    events_master = events.copy()
    order_items_master = order_items.copy()
    users_master = users.copy()
    orders_master = orders.copy()

    # --- 사이드바: 컨트롤 패널 ---
    st.sidebar.header("컨트롤 패널")
    
    # --- 1. 날짜 필터 위젯 추가 ---
    st.sidebar.subheader("날짜 필터")
    start_date = st.sidebar.date_input(
        "시작일",
        events_master['created_at'].min(),
        min_value=events_master['created_at'].min(),
        max_value=events_master['created_at'].max()
    )
    end_date = st.sidebar.date_input(
        "종료일",
        events_master['created_at'].max(),
        min_value=events_master['created_at'].min(),
        max_value=events_master['created_at'].max()
    )

    # --- 날짜 필터링 ---
    start_datetime = pd.to_datetime(start_date).tz_localize('UTC')
    end_datetime = pd.to_datetime(end_date).tz_localize('UTC') + pd.Timedelta(days=1)

    events = events_master[
        (events_master['created_at'] >= start_datetime) &
        (events_master['created_at'] < end_datetime)
    ]
    order_items = order_items_master[
        (order_items_master['created_at'] >= start_datetime) &
        (order_items_master['created_at'] < end_datetime)
    ]
    users = users_master[
        (users_master['created_at'] >= start_datetime) &
        (users_master['created_at'] < end_datetime)
    ]
    orders = orders_master[
        (orders_master['created_at'] >= start_datetime) &
        (orders_master['created_at'] < end_datetime)
    ]


    # --- 메인 콘텐츠 ---

    # 1. 선택된 '전체 기간'에 대한 KPI 계산
    
    # 전체 기간 총 매출 계산
    valid_status = ['Complete'] # 실제 매출은 'Complete' 상태만 집계
    total_revenue = order_items['sale_price'][order_items['status'].isin(valid_status)].sum()

    # 전체 기간 총 순 방문자 수(Unique Users) 계산
    # MAU의 합계가 아닌, 전체 기간의 고유한 user_id 수를 계산해야 합니다.
    total_unique_users = events['user_id'].nunique()

    # 2. KPI 지표 표시 (수정된 값 사용)
    st.header(f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} 핵심 성과 지표")
    st.write("선택된 기간 동안의 총 매출과 순 방문자 수를 나타냅니다.")
    col1, col2 = st.columns(2)
    col1.metric("총 매출 (Total Revenue)", f"${total_revenue:,.2f}")
    col2.metric("총 순 방문자 수 (Unique Users)", f"{total_unique_users:,.0f} 명")
    
    st.divider()

    # 2. 탭을 사용하여 콘텐츠 분리
    tab1, tab2, tab3  = st.tabs(["🔍 퍼널 분석 (Funnel)", "🗺️ 유입 경로 분석", "📅 월별/일별 사용자 분석"])



    with tab1:

        st.subheader("주요 행동 전환 분석 (Funnel)")
        st.write("사용자가 제품 탐색부터 구매 완료까지 각 단계에서 얼마나 전환되는지를 시각적으로 보여줍니다. 각 단계 사이의 이탈률을 파악할 수 있습니다.")
        funnel_stages = [['department','product'],'cart','purchase']
        funnel_fig = create_funnel_chart(events, funnel_stages, start_date, end_date)
        if funnel_fig:
            st.plotly_chart(funnel_fig, use_container_width=True)
        else:
            st.warning("퍼널 차트를 생성할 수 없습니다.")

        st.divider()

        st.subheader("사용자 행동 흐름 (Sankey)")
        st.write("사용자들이 웹사이트/앱 내에서 어떤 순서로 페이지를 이동하고 행동하는지 흐름을 시각화하여 보여줍니다. 주요 사용자 경로와 이탈 지점을 파악하는 데 유용합니다.")
        sankey_fig = create_sankey_chart(events, start_date, end_date)
        if sankey_fig:
            st.plotly_chart(sankey_fig, use_container_width=True)
        else:
            st.warning("생키 차트를 생성할 수 없습니다.")

        

    with tab2:

        # --- 수정: 데이터프레임 스타일링 함수를 with 블록 바깥으로 이동하여 재사용 ---
        def highlight_top_rows(row):
            """상위 3개 행은 PRIMARY_COLOR, 나머지는 SECONDARY_COLOR로 배경색을 지정합니다."""
            # --- 수정: 상위 1개 항목만 강조하도록 변경 ---
            if row.name < 1:
                return [f'background-color: {PRIMARY_COLOR}; color: white'] * len(row)
            else:
                return [f'background-color: {SECONDARY_COLOR}; color: white'] * len(row)

        st.subheader("전체 유입 경로 분포")
        st.write("어떤 채널(e.g., Facebook, Google, Email)을 통해 사용자들이 유입되었는지 분포를 보여줍니다. 가장 효과적인 유입 채널을 파악할 수 있습니다.")
        dist_fig, dist_data = create_traffic_distribution_chart(users, start_date, end_date)
        if dist_fig:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.pyplot(dist_fig)
            with col2:
                st.write("#### 데이터 요약")
                # --- 수정: 스타일을 적용하기 전에 reset_index()를 호출하여 숫자 인덱스를 갖도록 함 ---
                # dist_data는 Series이므로 to_frame()으로 DataFrame으로 변환
                dist_df_for_display = dist_data.to_frame().reset_index()
                st.dataframe(dist_df_for_display.style.apply(highlight_top_rows, axis=1))
        else:
            st.warning("선택된 기간에 데이터가 없습니다.")

        st.divider()

        st.subheader("유입 경로별 인구통계 상세 분석")
        st.write("특정 유입 경로를 통해 들어온 사용자들의 국가, 성별, 연령대 등 인구통계학적 특성을 상세히 분석합니다.")

        # 1. 메인 화면에 필터 배치
        filter_col, _ = st.columns([1, 2])
        with filter_col:
            traffic_sources = ['All'] + sorted(users['traffic_source'].unique())
            selected_source = st.selectbox(
                "분석할 유입 경로 선택:", 
                traffic_sources,
                index=traffic_sources.index('Facebook') if 'Facebook' in traffic_sources else 0 
            )

        # 2. 필터 값에 따라 분기 처리
        if selected_source == 'All':
            st.info("상단 필터에서 분석하고 싶은 특정 유입 경로를 선택해주세요.")
        else:
            # --- 핵심 수정 부분 ---
            # 3. 각 차트 생성 함수에 selected_source를 인자로 '전달'
            country_fig, user_count, country_data = create_country_chart(users, start_date, end_date, selected_source)
            gender_fig = create_gender_chart(users, start_date, end_date, selected_source)
            age_fig, age_data = create_age_chart(users, start_date, end_date, selected_source)

            if user_count > 0:
                st.write(f"선택된 기간 동안 '{selected_source}'를 통해 유입된 사용자는 총 **{user_count}명**입니다.")
                
                # --- 수정: 차트와 데이터 테이블을 함께 표시 ---
                
                
            if country_fig:
                        st.plotly_chart(country_fig, use_container_width=True)
                        with st.expander("상세 데이터 보기"):
                            st.dataframe(country_data.style.apply(highlight_top_rows, axis=1))

                
            if age_fig:
                        st.pyplot(age_fig)
                        with st.expander("상세 데이터 보기"):
                            # age_data는 인덱스가 'age_group'으로 되어 있으므로 reset_index() 필요
                            st.dataframe(age_data.reset_index(drop=True).style.apply(highlight_top_rows, axis=1))

            else:
                st.warning(f"선택된 기간에 '{selected_source}'를 통해 유입된 사용자가 없습니다.")

        
    
    with tab3:
        st.subheader("월별 매출 및 활성 사용자 수 (MAU)")
        st.write("월별 총 매출과 해당 월에 한 번 이상 방문한 순수 사용자 수(MAU)의 추이를 함께 보여줍니다. 비즈니스의 성장성과 사용자 참여도를 동시에 파악할 수 있습니다.")
        mau_revenue_fig, _ = create_mau_revenue_chart(order_items, events, start_date, end_date)
        st.pyplot(mau_revenue_fig)

        st.divider()
        st.subheader("일일 활성 사용자 수 (DAU)")
        st.write("선택한 기간 동안 매일 방문한 순수 사용자 수(DAU)의 추이를 보여줍니다. 단기적인 사용자 활동성과 이벤트 효과 등을 파악하는 데 유용합니다.")
        # 데이터에서 선택 가능한 월 목록 생성 ('YYYY-MM' 형식)
        available_months = ['전체 기간'] + sorted(
            events_master['created_at'].dt.to_period('M').astype(str).unique(),
            reverse=True
        )
        
        # 컬럼을 사용해 필터의 너비를 조절
        filter_col, _ = st.columns([1, 3])
        with filter_col:
            # st.selectbox를 사용하여 메인 페이지에 필터 배치
            selected_month = st.selectbox(
                "분석할 월을 선택하세요:",
                available_months
            )
        

        # DAU 데이터 계산 시 selected_month 전달
        dau_data = calculate_dau_by_month(events_master, selected_month)

        if dau_data is not None and not dau_data.empty:
            st.line_chart(dau_data)
            
            with st.expander("상세 데이터 보기"):
                st.dataframe(dau_data)
        else:
            st.warning("선택된 기간에 데이터가 없습니다.")

        