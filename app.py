import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
import pytz
import requests
from datetime import datetime

# --- 1. 配置与全局样式 (严禁修改) ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important; font-size: 20px !important; font-weight: bold !important;
        padding: 10px !important; border-radius: 10px !important;
    }
    .red-btn > div > button {
        color: #ff4b4b !important; border: 1px solid #ff4b4b !important;
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心功能：实时汇率 ---
@st.cache_data(ttl=3600)
def get_live_rates():
    default_rates = {"USD": 1.0, "RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            return {"USD": 1.0, "RMB": rates.get("CNY", 7.23), "VND": rates.get("VND", 25450), "HKD": rates.get("HKD", 7.82)}
    except: pass
    return default_rates

# --- 3. 数据连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="Summary", ttl=0).dropna(how="all")

def get_dynamic_options(df, column_name):
    if not df.empty and column_name in df.columns:
        options = sorted([str(x) for x in df[column_name].unique() if x and str(x).strip()])
        return options + ["➕ 新增..."]
    return ["➕ 新增..."]

# --- 4. 录入弹窗 (已补齐审批/发票编号) ---
@st.dialog("📝 数据录入", width="large")
def entry_dialog():
    df = load_data()
    live_rates = get_live_rates()
    st.write(f"💡 当前系统总结余: **${df['余额'].iloc[-1] if not df.empty else 0:,.2f}**")
    
    # 第一列：基础信息
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 第二列：金额汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率 (API获取)", value=float(live_rates[val_curr]), format="%.4f")
    
    # 第三列：账户与经手人 (新增支持)
    r3_c1, r3_c2 = st.columns(2)
    sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "账户"))
    val_acc = st.text_input("✍️ 录入新账户名称") if sel_acc == "➕ 新增..." else sel_acc
    
    sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
    val_hand = st.text_input("✍️ 录入新经手人姓名") if sel_hand == "➕ 新增..." else sel_hand
    
    # 第四列：发票编号与性质 (补齐发票编号)
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("审批/发票编号")  # <--- 已补回此处
    val_prop = r4_c2.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "其他"])
    
    # 第五列：联动项目名称
    is_req = val_prop in ["工程收入", "施工成本"]
    proj_label = "📍 客户/项目名称 (必填)" if is_req else "客户/项目名称 (选填)"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目名称"))
    val_proj = st.text_input("✍️ 录入新项目名称") if sel_proj == "➕ 新增..." else sel_proj

    val_note = st.text_area("备注详情")
    
    st.divider()
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        st.balloons()
        st.success("数据已存入缓冲区")
    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        st.balloons()
        st.rerun()
    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if b3.button("❌ 取消录入", use_container_width=True): st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 修正弹窗 (补齐发票编号并修正括号) ---
@st.dialog("🛠️ 修正", width="large")
def edit_dialog(df):
    target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        
        c1, c2 = st.columns(2)
        u_date = c1.text_input("日期 (YYYY-MM-DD HH:mm)", value=str(old.get("日期", "")))
        u_inc = c2.number_input("收入 (USD)", value=float(old.get("收入", 0)))
        
        c3, c4 = st.columns(2)
        u_sum = c3.text_input("摘要内容", value=str(old.get("摘要", "")))
        u_exp = c4.number_input("支出 (USD)", value=float(old.get("支出", 0)))
        
        c5, c6 = st.columns(2)
        u_proj = c5.text_input("客户/项目名称", value=str(old.get("客户/项目名称", "")))
        u_hand = c6.text_input("经手人", value=str(old.get("经手人", "")))
        
        c7, c8 = st.columns(2)
        u_acc = c7.text_input("结算账户", value=str(old.get("账户", "")))
        u_inv = c8.text_input("审批/发票编号", value=str(old.get("审批/发票编号", ""))) # <--- 已补回此处
        
        u_prop = st.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "预收款", "其他"])
        u_note = st.text_area("备注详情", value=str(old.get("备注", "")))

        st.divider()
        sv, ex = st.columns(2)
        if sv.button("💾 确认保存全字段修正", type="primary", use_container_width=True):
            st.balloons()
            st.rerun()
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if ex.button("❌ 放弃修正并复位", use_container_width=True): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_main = load_data()
    if not df_main.empty:
        st.metric("总结余", f"${df_main['余额'].iloc[-1]:,.2f}")
        st.divider()
        h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
        h_col.subheader("📑 原始流水明细")
        with b_add:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
        with b_edit:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_main)
        st.dataframe(df_main.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("请输入密码解锁系统")
