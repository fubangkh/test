import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection

# 导入自定义模块
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础配置 ---
st.set_page_config(page_title="财务流水管理系统", layout="wide", page_icon="📊")
LOCAL_TZ = pytz.timezone("Asia/Shanghai")

if "table_version" not in st.session_state:
    st.session_state.table_version = 0
if "show_edit_modal" not in st.session_state:
    st.session_state.show_edit_modal = False
if "edit_target_id" not in st.session_state:
    st.session_state.edit_target_id = None

# --- 2. 数据加载 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data(version=0):
    try:
        df = conn.read(worksheet="Summary", ttl=0)
        for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"加载失败: {e}")
        return pd.DataFrame()

def get_live_rates():
    return {"USD": 1.0, "CNY": 7.21, "KHR": 4050.0, "THB": 35.8}

def get_dynamic_options(df, column_name):
    if df.empty or column_name not in df.columns:
        return ["-- 请选择 --", "➕ 新增..."]
    options = df[column_name].dropna().unique().tolist()
    options = [opt for opt in options if opt and str(opt).strip() != "" and opt != "资金结转"]
    return ["-- 请选择 --"] + sorted(options) + ["➕ 新增..."]

# --- 3. 侧边栏 ---
df = load_data(version=st.session_state.table_version)

with st.sidebar:
    st.title("💰 财务管理")
    st.write(f"📅 {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d')}")
    if st.button("➕ 新增流水录入", type="primary", use_container_width=True):
        entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options)

# --- 4. 统计看板 ---
if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("累计总收入", f"$ {df['收入(USD)'].sum():,.2f}")
    m2.metric("累计总支出", f"$ {df['支出(USD)'].sum():,.2f}")
    m3.metric("当前总结余", f"$ {df['余额(USD)'].iloc[-1]:,.2f}")

st.divider()

# --- 5. 明细表与弹窗调度 ---
st.subheader("📑 财务明细账目")

view_df = df.copy()
if not view_df.empty:
    view_df = view_df.iloc[::-1]
    
    # 【核心修复】: 动态 Key。
    # 只要 table_version 变动，表格就会彻底重置，清空选中行状态。
    table_key = f"main_table_v_{st.session_state.table_version}"
    
    event = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        key=table_key
    )

    # 调度逻辑
    if st.session_state.show_edit_modal:
        edit_dialog(st.session_state.edit_target_id, df, conn, get_live_rates, get_dynamic_options, LOCAL_TZ)
    elif len(event.selection.rows) > 0:
        selected_row_idx = event.selection.rows[0]
        row_action_dialog(view_df.iloc[selected_row_idx], df, conn)
