import streamlit as st
from streamlit_gsheets import GSheetsConnection
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 (与录入页保持一致) ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')
conn = st.connection("gsheets", type=GSheetsConnection)

# 加载数据逻辑... (同前)
@st.cache_data(ttl=2)
def load_all_data():
    df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    df.columns = df.columns.str.strip()
    for col in ["收入", "支出", "余额"]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_latest = load_all_data()

# --- 2. 汇总统计逻辑 ---
def show_summary_metrics(df):
    st.subheader("🏦 账户本月汇总")
    this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
    accounts = sorted(df["账户"].unique().tolist())
    summary_list = []
    for acc in accounts:
        df_acc = df[df["账户"] == acc].sort_values("日期")
        df_before = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
        opening_bal = df_before["余额"].iloc[-1] if not df_before.empty else 0
        df_month = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
        month_inc = df_month["收入"].sum()
        month_exp = df_month["支出"].sum()
        current_bal = df_acc["余额"].iloc[-1] if not df_acc.empty else 0
        summary_list.append({"账户": acc, "期初": opening_bal, "收入": month_inc, "支出": month_exp, "结余": current_bal})
    st.table(pd.DataFrame(summary_list))

# --- 3. 汇总统计页面 (核心修改点) ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if role == "汇总统计" and pwd == "123": # ADMIN_PWD
    st.title("📊 统计与管理")
    
    if not df_latest.empty:
        show_summary_metrics(df_latest)
        st.divider()
        st.subheader("📑 明细流水 (选中行进行修改)")

        # --- 使用 AgGrid 构建带“选择”功能的表格 ---
        gb = GridOptionsBuilder.from_dataframe(df_latest.sort_values("录入编号", ascending=False))
        gb.configure_selection('single', use_checkbox=True) # 开启单选框
        gb.configure_pagination(paginationAutoPageSize=True) # 开启自动分页
        gb.configure_default_column(editable=False, groupable=True)
        gridOptions = gb.build()

        # 显示表格
        grid_response = AgGrid(
            df_latest,
            gridOptions=gridOptions,
            data_return_mode='AS_INPUT',
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            theme='balham', # 专业商务风格
        )

        # 获取选中的行
        selected_row = grid_response['selected_rows']
        
        if selected_row is not None and len(selected_row) > 0:
            st.warning(f"正在修改编号: {selected_row[0]['录入编号']}")
            with st.form("edit_form"):
                col1, col2, col3 = st.columns(3)
                new_sum = col1.text_input("摘要", value=selected_row[0]['摘要'])
                new_inc = col2.number_input("收入", value=float(selected_row[0]['收入']))
                new_exp = col3.number_input("支出", value=float(selected_row[0]['支出']))
                
                if st.form_submit_button("💾 保存修改"):
                    # 找到该行并覆盖数据
                    idx = df_latest[df_latest["录入编号"] == selected_row[0]['录入编号']].index[0]
                    df_latest.at[idx, "摘要"] = new_sum
                    df_latest.at[idx, "收入"] = new_inc
                    df_latest.at[idx, "支出"] = new_exp
                    
                    conn.update(worksheet="Summary", data=df_latest)
                    st.success("修改已成功同步到 Google Sheets！")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
