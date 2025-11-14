import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data import load_all_data

# ---------------- 데이터 로드 ----------------
all_data = load_all_data()
users = all_data["users"]
products = all_data["products"]
orders = all_data["orders"]
order_items = all_data["order_items"]
events = all_data["events"]
inventory_items = all_data["inventory_items"]

# ---------------- 페이지 설정 ----------------
st.set_page_config(
    page_title="메인 페이지",
    page_icon="🏠"
)

st.image("data/cover2.jpg")

st.title("🛒 Looker Ecommerce")
st.write("왼쪽 사이드바에서 분석 페이지를 선택하세요.")

st.sidebar.success("분석할 페이지를 선택해주세요.")

# ---------------- 데이터셋 소개 ----------------
st.markdown("### 📂 분석 데이터 개요")

st.markdown("#### **데이터셋 이름:** Looker Ecommerce BigQuery Dataset")
st.markdown("#### [Kaggle Dataset 링크](https://www.kaggle.com/datasets/mustafakeser4/looker-ecommerce-bigquery-dataset)")
st.markdown("##### **데이터셋 목표:** 2024년 연말(11-12월) 재구매율 향상")

# ---------------- 데이터 개요 ----------------
st.markdown("### 1. 데이터 개요")
st.write("#### 테이블별 행/열 수")

summary = {
    "users": users.shape,
    "orders": orders.shape,
    "order_items": order_items.shape,
    "events": events.shape,
    "inventory_items": inventory_items.shape
}
st.write(pd.DataFrame(summary, index=["rows", "cols"]).T)

st.write("#### Users 데이터 샘플")
st.dataframe(users.head())

st.write("#### Orders 상태 비율")
fig, ax = plt.subplots()
orders["status"].value_counts().plot(kind="bar", ax=ax, color="skyblue")
ax.set_ylabel("Count")
plt.tight_layout()
st.pyplot(fig)

# ---------------- ERD ----------------
st.markdown("### 2. ERD (Entity Relationship Diagram)")
st.markdown("#### 2-1. 전체데이터 ERD")

erd = """
digraph {
    graph [rankdir=LR]

    users [shape=box, style=filled, color=lightblue, label="users"]
    orders [shape=box, style=filled, color=lightgreen, label="orders"]
    order_items [shape=box, style=filled, color=lightgreen, label="order_items"]
    products [shape=box, style=filled, color=lightyellow, label="products"]
    inventory_items [shape=box, style=filled, color=lightyellow, label="inventory_items"]
    distribution_centers [shape=box, style=filled, color=orange, label="distribution_centers"]
    events [shape=box, style=filled, color=lightpink, label="events"]

    users -> orders [label="user_id"]
    users -> order_items [label="user_id"]
    users -> events [label="user_id"]

    orders -> order_items [label="order_id"]

    products -> order_items [label="product_id"]
    products -> inventory_items [label="product_id"]

    inventory_items -> order_items [label="inventory_item_id"]

    distribution_centers -> products [label="distribution_center_id"]
    distribution_centers -> inventory_items [label="product_distribution_center_id"]
}
"""
st.graphviz_chart(erd)

st.markdown("#### 2-2. 사용데이터 ERD")
st.markdown("###### (분석에는 users, orders, order_items, events, inventory_items 테이블만 사용)")

erd_core = """
digraph {
    graph [rankdir=LR]

    users [shape=box, style=filled, color=lightblue, label="users"]
    orders [shape=box, style=filled, color=lightgreen, label="orders"]
    order_items [shape=box, style=filled, color=lightyellow, label="order_items"]
    events [shape=box, style=filled, color=lightpink, label="events"]
    inventory_items [shape=box, style=filled, color=orange, label="inventory_items"]

    users -> orders [label="user_id"]
    users -> order_items [label="user_id"]
    users -> events [label="user_id"]

    orders -> order_items [label="order_id"]

    order_items -> inventory_items [label="inventory_item_id"]
}
"""
st.graphviz_chart(erd_core)
