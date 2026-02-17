import streamlit as st
import pandas as pd
from datetime import datetime

# --- 配置与页面设置 ---
st.set_page_config(page_title="企业财务云助手", layout="wide")
st.title("💼 企业财务每日报备系统")

# 模拟数据库（实际应用中建议对接 Google Sheets 或 腾讯文档 API）
if 'data_summary' not in st.session_state:
    st.session_state.data_summary = pd.DataFrame(columns=["日期", "收款金额", "现金余额", "填报人"])
if 'data_invoices' not in st.session_state:
    st.session_state.data_invoices = pd.DataFrame(columns=["对应日期", "发票号", "客户名称", "金额"])

# --- 侧边栏：角色切换 ---
role = st.sidebar.radio("请选择操作角色", ["财务录入员", "授权管理人员"])

# --- 财务录入模块 ---
if role == "财务录入员":
    st.header("📝 每日数据上报")
    
    with st.expander("第一步：填写基本资金情况", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            report_date = st.date_input("报备日期", datetime.now())
        with col2:
            income = st.number_input("昨日收款金额 (元)", min_value=0.0)
        with col3:
            balance = st.number_input("当前现金余额 (元)", min_value=0.0)

    with st.expander("第二步：手动录入发票明细"):
        num_invoices = st.number_input("本次录入发票张数", min_value=1, step=1)
        temp_invoices = []
        for i in range(num_invoices):
            c1, c2, c3 = st.columns([2, 3, 2])
            inv_no = c1.text_input(f"发票号 #{i+1}")
            cust = c2.text_input(f"客户名称 #{i+1}")
            amt = c3.number_input(f"金额 #{i+1}", min_value=0.0)
            temp_invoices.append([report_date, inv_no, cust, amt])

    if st.button("🚀 确认提交所有数据"):
        # 这里演示逻辑：将数据存入 session_state
        new_summary = pd.DataFrame([[report_date, income, balance, "财务A"]], columns=st.session_state.data_summary.columns)
        st.session_state.data_summary = pd.concat([st.session_state.data_summary, new_summary], ignore_index=True)
        
        new_invs = pd.DataFrame(temp_invoices, columns=st.session_state.data_invoices.columns)
        st.session_state.data_invoices = pd.concat([st.session_state.data_invoices, new_invs], ignore_index=True)
        
        st.success("数据已成功上报并同步至云端！")

# --- 管理查看模块 ---
else:
    st.header("📊 财务数据总览 (授权可见)")
    
    # 指标卡片
    if not st.session_state.data_summary.empty:
        latest = st.session_state.data_summary.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("最近收款", f"¥{latest['收款金额']:,}")
        c2.metric("当前余额", f"¥{latest['现金余额']:,}")
        c3.metric("累计发票张数", len(st.session_state.data_invoices))

        st.subheader("历史明细查询")
        tab1, tab2 = st.tabs(["资金汇总表", "发票明细表"])
        with tab1:
            st.dataframe(st.session_state.data_summary, use_container_width=True)
        with tab2:
            st.dataframe(st.session_state.data_invoices, use_container_width=True)
    else:
        st.info("暂无历史数据，请等待财务人员提交。")