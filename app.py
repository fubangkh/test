import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection

# 导入自定义逻辑与表单
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="财务流水管理系统", layout="wide", page_icon="📊")
LOCAL_TZ = pytz.timezone("Asia/Shanghai")

# 初始化全局状态
if "table_version" not in st.session_state:
    st.session_state.table_version = 0
if "show_edit_modal" not in st.session_state:
    st.session_state.show_edit_modal = False
if "edit_target_id" not in st.session_state:
    st.session_state.edit_target_id = None

# --- 2. 数据加载函数 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data(version=0):
    try:
        df = conn.read(worksheet="Summary", ttl=0)
        # 数据清洗：确保金额列为数值
        for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

# 获取实时汇率 (可根据需要对接API)
def get_live_rates():
    return {"USD": 1.0, "CNY": 7.21, "KHR": 4050.0, "THB": 35.8}

# 获取动态下拉选项
def get_dynamic_options(df, column_name):
    if df.empty or column_name not in df.columns:
        return ["-- 请选择 --", "➕ 新增..."]
    options = df[column_name].dropna().unique().tolist()
    # 过滤无效选项
    options = [opt for opt in options if opt and str(opt).strip() != "" and opt != "资金结转"]
    return ["-- 请选择 --"] + sorted(options) + ["➕ 新增..."]

# --- 3. 侧边栏 (带回所有消失的组件) ---
df = load_data(version=st.session_state.table_version)

with st.sidebar:
    st.title("💰 财务管理系统")
    st.markdown(f"**当前时间:** {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    # 🔙 消失的新增录入按钮回归
    if st.button("➕ 新增流水录入", type="primary", use_container_width=True):
        entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options)
    
    st.divider()
    # 🔙 消失的账户余额看板回归
    if not df.empty:
        st.subheader("🏦 账户余额明细")
        acc_group = df.groupby("结算账户")["收入(USD)", "支出(USD)"].sum()
        acc_group["当前结余"] = acc_group["收入(USD)"] - acc_group["支出(USD)"]
        for acc, row in acc_group.iterrows():
            if acc != "资金结转":
                st.metric(f"{acc}", f"$ {row['当前结余']:,.2f}")

# --- 4. 主页统计看板 ---
if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("累计总收入", f"$ {df['收入(USD)'].sum():,.2f}")
    m2.metric("累计总支出", f"$ {df['支出(USD)'].sum():,.2f}")
    m3.metric("当前总结余", f"$ {df['余额(USD)'].iloc[-1]:,.2f}")

    st.divider()

    # 🔙 消失的支出排行图表回归
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📊 支出性质排行")
        exp_df = df[df["支出(USD)"] > 0]
        if not exp_df.empty:
            prop_exp = exp_df.groupby("资金性质")["支出(USD)"].sum().sort_values(ascending=True)
            st.bar_chart(prop_exp, horizontal=True)
        else:
            st.info("暂无支出数据")
            
    with c2:
        st.subheader("📈 项目支出占比")
        if not exp_df.empty:
            proj_exp = exp_df.groupby("客户/项目信息")["支出(USD)"].sum()
            st.area_chart(proj_exp)
        else:
            st.info("暂无项目数据")

st.divider()

# --- 5. 数据明细表与调度逻辑 ---
st.subheader("📑 财务流水账目明细")

if not df.empty:
    # 倒序显示，最新的在上面
    view_df = df.copy().iloc[::-1]
    
    # 【修复关键】动态 Key 刷新，清空选中状态
    table_key = f"main_table_v_{st.session_state.table_version}"
    
    event = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        key=table_key
    )

    # 弹窗调度逻辑
    if st.session_state.show_edit_modal:
        edit_dialog(st.session_state.edit_target_id, df, conn, get_live_rates, get_dynamic_options, LOCAL_TZ)
    elif event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        row_action_dialog(view_df.iloc[selected_row_idx], df, conn)
else:
    st.warning("数据库为空，请点击左侧按钮开始录入。")
