import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置与时区 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# 注入 CSS 修复按钮颜色并实现字体自适应
st.markdown("""
    <style>
    /* 强制主按钮为蓝底白字 */
    div.stButton > button[kind="primary"] {
        background-color: #007bff !important;
        color: white !important;
        border: none;
        width: 100%;
        /* 字体大小随窗口宽度缩放：在 1.2% 窗口宽度和 14px 之间取较大值 */
        font-size: max(1.2vw, 14px) !important; 
        padding: 10px 0px;
    }
    /* 修正模块的样式微调 */
    .stExpander {
        border: 1px solid #f0f2f6;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_now_local():
    return datetime.now(LOCAL_TZ)

def get_now_str():
    return get_now_local().strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 状态初始化 ---
if "edit_iteration" not in st.session_state:
    st.session_state.edit_iteration = 0

# --- 3. 核心函数 ---
@st.cache_data(ttl=1)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
        if "修正时间" not in df.columns:
            df["修正时间"] = ""
        return df
    except:
        return pd.DataFrame()

def get_reference_rate(currency):
    if currency == "USD": return 1.0
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1)
        if res.status_code == 200:
            api = res.json().get("rates", {})
            rates = {"RMB": api.get("CNY", 7.23), "VND": api.get("VND", 25450.0), "HKD": api.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and "🔍" not in str(x)])

# --- 4. 数据录入弹窗 ---
@st.dialog("📝 数据录入窗口", width="large")
def entry_dialog():
    df_current = load_all_data()
    last_bal = df_current["余额"].iloc[-1] if not df_current.empty else 0.0
    st.markdown(f"**💡 当前实时结余：${last_bal:,.2f}**")
    
    c1, c2 = st.columns([2, 1])
    with c1: val_summary = st.text_input("摘要内容")
    with c2: val_biz_time = st.datetime_input("业务时间", value=get_now_local())
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1: val_raw_amt = st.number_input("金额", min_value=0.0, step=0.01)
    with r2_c2: val_curr = st.selectbox("币种", ["USD", "RMB", "VND", "HKD"])
    with r2_c3: val_rate = st.number_input("记账汇率", value=float(get_reference_rate(val_curr)), format="%.4f")
    
    acc_list = get_unique_list(df_current, "账户")
    a_sel = st.selectbox("结算账户", ["🔍 选择账户"] + acc_list + ["➕ 新增"])
    val_acc = st.text_input("✍️ 输入新账户") if a_sel == "➕ 新增" else a_sel
    
    prop_list = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "期初结存", "内部调拨-转入", "内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    val_prop = st.selectbox("资金性质", prop_list)
    
    val_project = ""
    if val_prop in ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]:
        p_list = get_unique_list(df_current, "客户/项目名称")
        p_sel = st.selectbox("选择项目", ["🔍 请选择"] + p_list + ["➕ 新增"])
        val_project = st.text_input("✍️ 输入新项目") if p_sel == "➕ 新增" else (p_sel if p_sel != "🔍 请选择" else "")

    f1, f2 = st.columns(2)
    with f1:
        h_list = get_unique_list(df_current, "经手人")
        h_sel = st.selectbox("经手人", ["🔍 选择人员"] + h_list + ["➕ 新增"])
        val_handler = st.text_input("✍️ 姓名") if h_sel == "➕ 新增" else h_sel
    with f2: val_ref = st.text_input("审批编号")
    val_note = st.text_area("备注详情")

    st.markdown("---")
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续录入", use_container_width=True):
        # 保存逻辑（同前，此处省略重复代码逻辑）...
        st.cache_data.clear(); st.rerun()
    if b2.button("✅ 提交并返回", use_container_width=True):
        # 保存逻辑...
        st.cache_data.clear(); st.rerun()
    if b3.button("❌ 取消录入", use_container_width=True):
        st.rerun()

# --- 5. 主页面内容 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    # 顶部标题与自适应蓝色按钮
    header_c1, header_c2 = st.columns([5, 1])
    with header_c1:
        st.title("📊 财务实时汇总统计")
    with header_c2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("➕ 数据录入", use_container_width=True, type="primary"):
            entry_dialog()

    df_latest = load_all_data()
    if not df_latest.empty:
        # 今日指标
        today_date = get_now_local().strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str).str.startswith(today_date)]
        m1, m2, m3 = st.columns(3)
        m1.metric("今日收入", f"${df_today['收入'].sum():,.2f}")
        m2.metric("今日支出", f"${df_today['支出'].sum():,.2f}")
        m3.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")

        st.divider()
        
        # --- 左右分栏布局 (明细 vs 修正) ---
        main_c1, main_c2 = st.columns([3, 1])
        
        with main_c1:
            st.subheader("📑 原始流水明细")
            display_cols = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "修正时间"]
            st.dataframe(df_latest.sort_values("录入编号", ascending=False), 
                         hide_index=True, use_container_width=True, 
                         column_order=display_cols, height=600)

        with main_c2:
            st.subheader("🛠️ 数据修正")
            e_itr = st.session_state.edit_iteration
            target = st.selectbox("选择编号", ["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1], key=f"edit_target_{e_itr}")
            
            if target != "-- 请选择 --":
                old = df_latest[df_latest["录入编号"] == target].iloc[0]
                with st.form(f"edit_form_{target}"):
                    st.info(f"正在修正: {target}")
                    u_sum = st.text_input("摘要", value=str(old["摘要"]))
                    u_inc = st.number_input("收入", value=float(old["收入"]))
                    u_exp = st.number_input("支出", value=float(old["支出"]))
                    u_hand = st.text_input("经手人", value=str(old["经手人"]))
                    u_note = st.text_area("备注", value=str(old["备注"]))
                    
                    eb1, eb2 = st.columns(2)
                    if eb1.form_submit_button("💾 保存"):
                        # 更新逻辑（同前）...
                        st.session_state.edit_iteration += 1
                        st.cache_data.clear(); st.rerun()
                    if eb2.form_submit_button("❌ 放弃"):
                        st.session_state.edit_iteration += 1
                        st.rerun()
else:
    st.info("请输入密码访问系统")
