import streamlit as st
import pandas as pd
import koreanize_matplotlib
import matplotlib.pyplot as plt

from data import load_all_data
from charts.retention_charts import (
    create_purchase_distribution_chart, 
     create_advanced_cohort_heatmap,
    create_repeat_purchaser_chart, create_weekly_cohort_heatmap,
    create_daily_cohort_heatmap, create_weekday_repeat_purchase_charts,
    create_weekday_weekend_chart
)

all_data = load_all_data()




# --- 메인 대시보드 레이아웃 ---

st.set_page_config(
    page_title="🔁 Retention 분석",
    layout="wide"
)
st.title("🔁 고객 유지(Retention) 분석")

# --- 데이터 로딩 ---
all_data = load_all_data()

if not all_data :
    st.error("주문(order_items) 데이터를 불러오는데 실패했습니다.")
else:

    events = all_data["events"]
    order_items = all_data["order_items"]
    users = all_data["users"]
    orders = all_data["orders"]
    products = all_data["products"]
    products_master = products.copy()


    events_master = events.copy()
    order_items_master = order_items.copy()
    users_master = users.copy()
    orders_master = orders.copy()

    raw_data_schema={
            'user_id': 'session_id', 'event_name': 'event_type', 'event_timestamp': 'created_at'
        }
    
    valid_status = ['Complete', 'Returned', 'Cancelled']
    valid_orders = order_items[order_items['status'].isin(valid_status)].copy()

    # 유저별 구매 내역 정렬
    valid_orders = valid_orders.sort_values(['user_id', 'created_at'])
    

    valid_status = ['Complete', 'Returned', 'Cancelled']
    valid_orders = order_items[order_items['status'].isin(valid_status)].copy()
    user_purchase_counts = valid_orders.groupby('user_id')['order_id'].nunique()

    st.header("사용자별 구매 횟수 분포")
    st.write("각 사용자가 몇 번의 구매를 했는지 분포를 통해 충성 고객과 일회성 고객의 비율을 파악할 수 있습니다.")

    order_items_master = all_data["order_items"].copy()
    products_master = all_data["products"].copy()

    # --- 메인 대시보드 레이아웃 ---
    st.header("고객 리텐션 분석 (Cohort)")

            # --- 사이드바: 컨트롤 패널 ---
    st.sidebar.header("컨트롤 패널")
    st.sidebar.subheader("날짜 필터")
    start_date = st.sidebar.date_input("시작일", orders_master['created_at'].min())
    end_date = st.sidebar.date_input("종료일", orders_master['created_at'].max())
            
    st.sidebar.divider()
    st.sidebar.subheader("차트 옵션")
    # max_age_option = st.sidebar.slider("최대 경과 개월 수:", 1, 24, 12, help="히트맵에 표시할 최대 재구매 경과 개월 수를 선택합니다.")
    show_annotations = st.sidebar.checkbox("히트맵에 리텐션 값(%) 표시", value=True)

    tab1, tab2, tab3  = st.tabs(["📊 구매 횟수 및 리텐션", "🗓️ 월/주/일별 코호트 분석", "📅 요일별 재구매 패턴"])


    with tab1:
        st.subheader("사용자별 구매 횟수 분포")
        st.write("전체 사용자 중 재구매자와 일회성 구매자의 비율을 파악합니다. 막대그래프는 특정 횟수만큼 구매한 사용자의 수를 보여줍니다.")

        if not all_data or "order_items" not in all_data:
            st.error("주문(order_items) 데이터를 불러오는데 실패했습니다.")
        else:
            order_items = all_data["order_items"]
            
            # 차트 생성 함수 호출
            dist_fig, dist_data = create_purchase_distribution_chart(orders_master)
            
            if dist_fig:
                # 컬럼을 사용해 차트와 데이터를 나란히 표시
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.pyplot(dist_fig)
                with col2:
                    st.write("#### 데이터 요약")
                    st.dataframe(dist_data)
        
        st.divider()

        # if not all_data:
        #     st.error("데이터를 불러오는데 실패했습니다.")
        # else:
            

        #     # --- 핵심 수정 부분 ---

        #     # --- 첫 번째 분석: 전체 리텐션 ---
        #     st.subheader("전체 고객 리텐션 (기간 필터 적용)")
            
        #     # 날짜 필터링
        #     start_datetime = pd.to_datetime(start_date).tz_localize('UTC')
        #     end_datetime = pd.to_datetime(end_date).tz_localize('UTC') + pd.Timedelta(days=1)
        #     filtered_orders = orders_master[
        #         (orders_master['created_at'] >= start_datetime) & 
        #         (orders_master['created_at'] < end_datetime)
        #     ]

        #     # 전체 리텐션 차트 생성 및 표시
        #     heatmap_fig, cohort_df = create_retention_heatmap(filtered_orders, show_annotations)
        #     if heatmap_fig:
        #         st.pyplot(heatmap_fig)
        #         with st.expander("상세 데이터 보기"):
        #             st.dataframe(cohort_df.style.format("{:.2%}"))
        #     else:
        #         st.warning("선택된 기간에 분석할 데이터가 없습니다.")

        #     # --- 두 분석 사이에 구분선 추가 ---
        #     st.divider()

            # --- 두 번째 분석: 카테고리별 리텐션 ---
            # st.subheader("카테고리별 고객 리텐션")
            
            # 카테고리 선택 필터 (너비 조절을 위해 컬럼 사용)
            # filter_col, _ = st.columns([1, 2])
            # with filter_col:
            #     available_categories = sorted(products_master['category'].unique())
            #     selected_category = st.selectbox(
            #         "분석할 카테고리를 선택하세요:", 
            #         available_categories,
            #         index=available_categories.index('Intimates') if 'Intimates' in available_categories else 0
            #     )
            
            # # 카테고리별 리텐션 차트 생성 및 표시
            # cat_heatmap_fig, cat_cohort_df = create_category_cohort_heatmap(
            #     orders_master, 
            #     products_master,
            #     selected_category,
            #     show_annotations
            # )
            # if cat_heatmap_fig:
            #     st.pyplot(cat_heatmap_fig)
            #     with st.expander("상세 데이터 보기"):
            #         st.dataframe(cat_cohort_df.style.format("{:.2%}"))
            # else:
            #     st.warning(f"'{selected_category}' 카테고리에 해당하는 데이터가 없습니다.")


    with tab2:
        st.subheader("월별 첫 구매 고객 재구매율 분석")
        st.write("각 월별로 발생한 총 구매 중, 기존 고객(재구매자)의 구매가 차지하는 비율을 보여줍니다. 이 비율이 높을수록 고객 충성도가 높다고 해석할 수 있습니다.")

        repeat_fig, repeat_df = create_repeat_purchaser_chart(orders_master)

        if repeat_fig:
            st.pyplot(repeat_fig)
            with st.expander("상세 데이터 보기"):
                st.dataframe(repeat_df[['returning_users','purchasers','repeat_purchaser_rate']])
        else:
            # 함수 내부에서 이미 경고 메시지를 표시함
            pass

        st.subheader("월별 코호트 재구매율 히트맵")
        st.write("특정 월에 첫 구매를 한 고객 그룹(코호트)이 시간이 지남에 따라 얼마나 다시 구매하는지 추적합니다. 각 행은 첫 구매월 그룹, 각 열은 첫 구매 후 경과한 개월 수를 의미합니다.")
        filter_col, _ = st.columns([1, 2])
        # with filter_col:
        #     # 2. st.slider를 사용하여 필터를 메인 페이지에 배치합니다.
        #     max_age_option = st.slider(
        #         "최대 경과 개월 수:", 
        #         min_value=1, 
        #         max_value=12, 
        #         value=12, 
        #         help="히트맵에 표시할 최대 재구매 경과 개월 수를 선택합니다."
        #     )
        
        # 고급 코호트 분석 함수 호출
        cohort_fig, cohort_df = create_advanced_cohort_heatmap(
            orders_master, 
            12, 
            show_annotations
        )

        if cohort_fig:
            st.pyplot(cohort_fig)
            with st.expander("상세 데이터 보기"):
                # .style.format()은 PeriodIndex에서 오류가 발생할 수 있으므로 안전하게 처리
                try:
                    st.dataframe(cohort_df.style.format("{:.2%}"))
                except Exception:
                    st.dataframe(cohort_df)
        else:
            # 함수 내부에서 st.warning으로 이미 메시지를 보여주므로 여기서는 pass
            pass

                # 수정: 함수 호출 시 year 인자 제거
        

        st.divider()

        st.subheader("주간 코호트 재구매율")
        st.write("월별 분석보다 더 세분화하여, 특정 주에 첫 구매를 한 고객 그룹이 매주 얼마나 재방문하여 구매하는지 추적합니다. 단기적인 변화나 특정 이벤트의 효과를 분석하는 데 유용합니다.")

        # --- 필터 위젯 ---
        # 데이터에서 선택 가능한 월 목록 동적 생성
        temp_df = orders_master.copy()
        # 2023년 데이터만 필터링
        temp_df = temp_df[pd.to_datetime(temp_df['created_at']).dt.year == 2023]
        temp_df['cohort_month'] = pd.to_datetime(temp_df['created_at']).dt.to_period('M').astype(str)
        available_months = sorted(temp_df['cohort_month'].unique(), reverse=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            selected_month = st.selectbox("분석할 코호트 월 선택:", available_months)
        with col2:
            week_options = ['All'] + list(range(1, 6))
            selected_week = st.selectbox("주차 필터 (Wn):", week_options, help="해당 월의 n번째 주에 시작된 코호트만 필터링합니다.")

        col_slider, _ = st.columns([2, 1])
        with col_slider:
            max_age_option = st.slider("최대 경과 주 수:", 1, 52, 12)

        show_annotations = st.checkbox("히트맵에 값(%) 표시", value=True)
        st.divider()

        # --- 차트 생성 및 표시 ---
        if selected_month:
            weekly_fig, weekly_df = create_weekly_cohort_heatmap(
                orders_master, 
                selected_month,
                selected_week,
                max_age_option, 
                show_annotations
            )

            if weekly_fig:
                st.pyplot(weekly_fig)
                with st.expander("상세 데이터 보기"):
                    st.dataframe(weekly_df.style.format("{:.2%}"))
            else:
                # 함수 내부에서 이미 경고 메시지를 표시함
                pass

        # st.divider()
        # st.subheader("일별 코호트 재구매율")

        # col1, col2, col3 = st.columns([1, 1, 2])
        # with col1:
        #     selected_month2 = st.selectbox("분석할 코호트 월 선택:", available_months,key='source_selectbox_tab2')
        # with col2:
        #     # 월~W5, 전체(All)
        #     week_options = ['All'] + [i for i in range(1, 6)]
        #     selected_week = st.selectbox("주차 필터 (Wn):", week_options)

        # col_slider, _ = st.columns([2, 1])
        # with col_slider:
        #     max_age_option = st.slider("최대 경과 일 수:", 1, 60, 30)

        # st.divider()

        # # --- 차트 생성 및 표시 ---
        # if selected_month:
        #     daily_fig, daily_df = create_daily_cohort_heatmap(
        #         orders_master, 
        #         selected_month2,
        #         selected_week,
        #         max_age_option, 
        #         show_annotations
        #     )

        #     if daily_fig:
        #         st.pyplot(daily_fig)
        #         with st.expander("상세 데이터 보기"):
        #             st.dataframe(daily_df.style.format("{:.2%}"))
        #     else:
        #         # 함수 내부에서 이미 경고 메시지를 표시함
        #         pass
  

    with tab3:
        st.subheader("요일에 따른 재구매 패턴 심층 분석")
        st.write("사용자의 첫 구매 요일과 실제 재구매가 발생한 요일 간의 관계를 분석합니다. 특정 요일에 첫 구매를 유도하는 것이 재구매율에 영향을 미치는지 파악할 수 있습니다.")

        # 새로 만든 함수 호출
        weekday_fig, order_data, cohort_data = create_weekday_repeat_purchase_charts(orders_master, start_date, end_date)

        if weekday_fig:
            st.pyplot(weekday_fig)
            
            with st.expander("상세 데이터 보기"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("#### 재구매 발생 요일 기준")
                    st.dataframe(order_data[['Weekday', 'Repeat_Orders', 'Exposure', 'Repeat_Rate']].style.format({'Repeat_Rate': '{:.2%}'}))
                with col2:
                    st.write("#### 첫 구매 요일 기준")
                    st.dataframe(cohort_data[['Weekday', 'Repeat_Orders', 'Exposure', 'Repeat_Rate']].style.format({'Repeat_Rate': '{:.2%}'}))
        else:
            # 함수 내부에서 이미 경고 메시지를 표시함
            pass

        st.divider()
        
        # --- ✨ [섹션 추가] 주중/주말 재구매율 비교 ---
        st.subheader("주중 vs 주말 재구매율 비교")
        st.write("전체 재구매 활동이 주중과 주말 중 어느 시기에 더 활발하게 일어나는지 비교 분석합니다.")
        weekday_fig, weekday_tbl = create_weekday_weekend_chart(orders_master, start_date, end_date)
        
        if weekday_fig:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.write("#### 분석 요약 테이블")
                st.dataframe(weekday_tbl, hide_index=True)
            with col2:
                st.pyplot(weekday_fig)
        else:
            st.warning("주중/주말 분석을 위한 데이터가 부족합니다.")


    
    