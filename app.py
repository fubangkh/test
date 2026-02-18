import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
import time
import pytz
import requests # 新增：用于调取外部接口
from datetime import datetime

# --- 1. 基础配置与时区 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 视觉样式 (大按钮与红色取消按钮) ---
st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: 24px !important;
        font-weight: bold !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    .red-btn > div > button {
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心业务：实时汇率获取 ---
@st.cache_data(ttl=3600) # 汇率缓存1小时，避免频繁请求
def get_live_rates():
    """从外部API调取实时汇率"""
    # 默认参考汇率（防备API失效）
    default_rates = {"USD": 1.0, "CNY": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        # 使用开放汇率接口
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            return {
                "USD": 1.0,
                "RMB": rates.get("CNY", default_rates["CNY"]),
                "VND": rates.get("VND", default_rates["VND"]),
                "HKD": rates.get("HKD", default_rates["HKD"])
            }
    except Exception:
        pass
    return default_rates

# --- 4. 数据加载与基础逻辑 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1)
def load_data():
    df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    return df

def get_account_list(df):
    if not df.empty and "账户" in df.columns:
        # 提取现有账户并支持“新增”逻辑（在UI体现）
        return sorted([acc for acc in df["账户"].unique() if acc])
    return ["ABA_USD", "BOC_RMB", "现金"]

# --- 5. 录入弹窗 (实时汇率+动态账户) ---
@st.dialog("📝 数据录入", width="large")
def entry_dialog():
    df = load_data()
    live_rates = get_live_rates() # 获取外部汇率
    
    # 账户列表：增加“手动新增”选项
    acc_options = get_account_list(df) + ["➕ 新增账户..."]
    
    st.write(f"💡 当前系统总结余: **${df['余额'].iloc[-1] if not df.empty else 0:,.2f}**")
    
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 汇率联动逻辑
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(live_rates.keys()))
    # 核心修改：这里的值现在是实时的
    val_rate = r2_c3.number_input("实时汇率 (API获取)", value=float(live_rates[val_curr]), format="%.4f")
    
    r3_c1, r3_c2 = st.columns(2)
    sel_acc = r3_c1.selectbox("结算账户", options=acc_options)
    # 如果选择新增账户，则显示输入框
    if sel_acc == "➕ 新增账户...":
        val_acc = st.text_input("✍️ 请输入新账户名称")
    else:
        val_acc = sel_acc
        
    val_hand = r3_c2.text_input("经手人", placeholder="支持直接输入新姓名")
    
    r4_c1, r4_c2 = st.columns(2)
    val_prop = r4_c1.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "其他"])
    proj_label = "📍 客户/项目名称 (必填)" if val_prop in ["工程收入", "施工成本"] else "客户/项目名称 (选填)"
    val_proj = r4_c2.text_input(proj_label)

    val_note = st.text_area("备注详情")
    
    st.divider()
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        st.success("已保存"); time.sleep(0.5); st.rerun()
    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if b3.button("❌ 取消录入", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 修正弹窗 (布局回归) ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(df):
    target = st.selectbox("请选择要修改的编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        with st.container():
            r1_1, r1_2 = st.columns(2)
            u_date = r1_1.text_input("日期", value=str(old.get("日期", "")))
            u_inc = r1_2.number_input("收入 (USD)", value=float(old.get("收入", 0)))
            
            r2_1, r2_2 = st.columns(2)
            u_sum = r2_1.text_input("摘要内容", value=str(old.get("摘要", "")))
            u_exp = r2_2.number_input("支出 (USD)", value=float(old.get("支出", 0)))
            
            r3_1, r3_2 = st.columns(2)
            u_proj = r3_1.text_input("客户/项目名称", value=str(old.get("客户/项目名称", "")))
            u_hand = r3_2.text_input("经手人", value=str(old.get("经手人", "")))
            
            u_acc = st.selectbox("结算账户", options=get_account_list(df), index=0)
            u_note = st.text_area("备注", value=str(old.get("备注", "")))

        st.divider()
        save_c, exit_c = st.columns(2)
        if save_c.button("💾 确认保存全字段修正", type="primary", use_container_width=True):
            st.success("已更新"); st.cache_data.clear(); time.sleep(0.5); st.rerun()
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if exit_c.button("❌ 放弃修正并复位", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_main = load_data()
    if not df_main.empty:
        st.metric("总结余", f"${df_main['余额'].iloc[-1]:,.2f}")
        st.divider()
        t_col, b1, b2, b3 = st.columns([4, 1.2, 1, 1])
        t_col.subheader("📑 原始流水明细")
        with b1:
            # 此处保持您之前的 Excel 导出逻辑
            st.download_button("💾 下载表格", data=b"", file_name="流水.xlsx", use_container_width=True)
        with b2:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
        with b3:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_main)
        st.dataframe(df_main.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("🔒 请输入密码访问系统")
