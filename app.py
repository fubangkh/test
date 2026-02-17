import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 页面基本配置
st.set_page_config(page_title="财务管理系统", layout="wide")
st.title("💰 富邦日记账与发票管理系统")

# 建立云端连接
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 角色切换 ---
role = st.sidebar.radio("请选择操作角色", ["财务录入员", "授权管理人员"])

if role == "财务录入员":
    st.header("📝 每日数据上报")
    
    with st.form("main_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            report_date = st.date_input("报备日期", datetime.now()).strftime("%Y-%m-%d")
        with col2:
            income = st.number_input("昨日收款金额 (元)", min_value=0.0)
        with col3:
            balance = st.number_input("当前现金余额 (元)", min_value=0.0)
        
        user_name = st.text_input("填报人姓名")
        
        st.divider()
        st.write("### 🧾 手动录入发票明细")
        # 默认提供 5 行输入空间，如果不够可以增加
        num_rows = st.number_input("本次录入发票张数", min_value=1, max_value=20, value=1)
        invoice_list = []
        for i in range(int(num_rows)):
            c1, c2, c3 = st.columns([2, 3, 2])
            inv_no = c1.text_input(f"发票号 #{i+1}", key=f"no_{i}")
            cust = c2.text_input(f"客户名称 #{i+1}", key=f"cu_{i}")
            amt = c3.number_input(f"金额 #{i+1}", min_value=0.0, key=f"am_{i}")
            if inv_no: # 只有填了单号的才计入
                invoice_list.append({"对应日期": report_date, "发票号": inv_no, "客户名称": cust, "金额": amt})

        submitted = st.form_submit_button("🚀 提交数据并同步至云端")
        
        if submitted:
            try:
                # 1. 更新汇总表
                conn.read(worksheet="Summary", ttl=0).dropna(how="all")
                new_summary = pd.DataFrame([{"日期": report_date, "收款金额": income, "现金余额": balance, "填报人": user_name}])
                updated_summary = pd.concat([summary_df, new_summary], ignore_index=True).dropna(how="all")
                conn.update(worksheet="Summary", data=updated_summary)
                
                # 2. 更新明细表
                if invoice_list:
                    invoice_df = conn.read(worksheet="Invoices", ttl=0).dropna(how="all")
                    new_invoices = pd.DataFrame(invoice_list)
                    updated_invoices = pd.concat([invoice_df, new_invoices], ignore_index=True).dropna(how="all")
                    conn.update(worksheet="Invoices", data=updated_invoices)
                
                st.success("✅ 数据已成功同步至云端！")
            except Exception as e:
                st.error(f"同步失败，请检查 Google Sheets 配置或工作表名称是否正确。错误信息: {e}")

else:
    st.header("📊 财务概览看板")
    try:
        df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df_inv = conn.read(worksheet="Invoices", ttl=0).dropna(how="all")
        
        tab1, tab2 = st.tabs(["资金汇总历史", "发票明细清单"])
        with tab1:
            st.dataframe(df_sum, use_container_width=True)
        with tab2:
            st.dataframe(df_inv, use_container_width=True)
    except:
        st.info("暂无云端数据，请等待财务人员完成首次提交。")

