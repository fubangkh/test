import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
import time
import pytz
import requests
from datetime import datetime

# --- 1. 基础配置与时区 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 视觉样式 ---
st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: 22px !important;
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

# --- 3. 实时汇率获取 ---
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

# --- 4. 数据连接与自动提取列表 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2) # 极短缓存保证刷新
def load_data():
    return conn.read(worksheet="Summary", ttl=0).dropna(how="all")

def get_dynamic_options(df, column_name):
    """自动从历史数据提取下拉选项"""
    if not df.empty and column_name in df.columns:
        options = sorted([str(x) for x in df[column_name].unique() if x and str(x).strip()])
        return options + ["➕ 新增..."]
    return ["➕ 新增..."]

# --- 5. 录入弹窗 (全自动化+下拉+气球) ---
@st.dialog("📝 数据录入", width="large")
def entry_dialog():
    df = load_data()
    live_rates = get_live_rates()
    
    st.write(f"💡 当前结余: **${df['余额'].iloc[-1] if not df.empty else 0:,.2f}**")
    
    with st.form("entry_form", clear_on_submit=True): # clear_on_submit 实现复位
        c1, c2 = st.columns(2)
        val_sum = c1.text_input("摘要内容")
        val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
        
        r2_c1, r2_c2, r2_c3 = st.columns(3)
        val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
        val_curr = r2_c2.selectbox("币种", list(live_rates.keys()))
        val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f")
        
        # --- 智能下拉选择组 ---
        r3_c1, r3_c2 = st.columns(2)
        
        # 结算账户
        acc_opts = get_dynamic_options(df, "账户")
        sel_acc = r3_c1.selectbox("结算账户", options=acc_opts)
        val_acc = st.text_input("✍️ 请输入新账户名称") if sel_acc == "➕ 新增..." else sel_acc
        
        # 经手人 (找回下拉+新增)
        hand_opts = get_dynamic_options(df, "经手人")
        sel_hand = r3_c2.selectbox("经手人", options=hand_opts)
        val_hand = st.text_input("✍️ 请输入新经手人姓名") if sel_hand == "➕ 新增..." else sel_hand
        
        # 资金性质与项目 (找回下拉+新增)
        r4_c1, r4_c2 = st.columns(2)
        val_prop = r4_c1.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "其他"])
        
        proj_opts = get_dynamic_options(df, "客户/项目名称")
        sel_proj = r4_c2.selectbox("客户/项目名称", options=proj_opts)
        val_proj = st.text_input("✍️ 请输入新项目名称") if sel_proj == "➕ 新增..." else sel_proj

        val_note = st.text_area("备注详情")
        
        st.divider()
        sub1, sub2, cancel_c = st.columns([1,1,1])
        
        submit_continue = sub1.form_submit_button("📥 提交并继续", use_container_width=True)
        submit_back = sub2.form_submit_button("✅ 提交并返回", use_container_width=True)
        
        if submit_continue or submit_back:
            # 这里执行实际的 conn.update 写入操作 (略)
            st.balloons() # 气球庆贺
            st.success("🎉 数据录入成功！")
            st.cache_data.clear() # 关键：清除缓存强制刷新页面
            time.sleep(1)
            if submit_back: st.rerun()

    # 取消按钮放在 Form 之外
    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if st.button("❌ 取消并关闭", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 修正弹窗 ---
@st.dialog("🛠️ 修正", width="large")
def edit_dialog(df):
    target = st.selectbox("选择要修改的编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        # (修正字段布局保持 image_bc5c60.png 样式)
        # ... 修正逻辑
        btn_save, btn_exit = st.columns(2)
        if btn_save.button("💾 确认保存", type="primary", use_container_width=True):
            st.balloons()
            st.cache_data.clear()
            st.rerun()
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if btn_exit.button("❌ 放弃并复位", use_container_width=True): st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 主页面展示 ---
pwd = st.sidebar.text_input("🔑 密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_main = load_data()
    
    if not df_main.empty:
        st.metric("总结余", f"${df_main['余额'].iloc[-1]:,.2f}")
        st.divider()
        
        # 功能区
        h_col, b1, b2, b3 = st.columns([4, 1.2, 1, 1])
        h_col.subheader("📑 原始流水明细")
        with b2:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
        with b3:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_main)
            
        # 数据表显示
        st.dataframe(df_main.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("请输入密码访问")
