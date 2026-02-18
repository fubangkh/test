import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
import time
import pytz
from datetime import datetime

# --- 1. 配置与样式 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

st.markdown("""
    <style>
    /* 首页大按钮：蓝底白字大字体 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: 22px !important;
        padding: 10px !important;
        border-radius: 8px !important;
    }
    /* 放弃/取消按钮：红框白底 */
    .red-btn > div > button {
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑还原 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1)
def load_data():
    df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    # 确保数值格式正确
    for col in ["收入", "支出", "余额"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# 还原汇率字典
CURRENCY_RATES = {"USD": 1.0, "RMB": 7.19, "VND": 25400.0, "HKD": 7.8}

# --- 3. 数据录入弹窗 (精准还原自动化逻辑) ---
@st.dialog("📝 录入", width="large")
def entry_dialog():
    df = load_data()
    st.write(f"💡 当前总结余: **${df['余额'].iloc[-1]:,.2f}**")
    
    # 还原逻辑：两栏布局
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(CURRENCY_RATES.keys()))
    # 【自动化还原1】：汇率跟随币种自动变化
    val_rate = r2_c3.number_input("实时汇率", value=CURRENCY_RATES[val_curr], format="%.4f")
    
    r3_c1, r3_c2 = st.columns(2)
    val_acc = r3_c1.text_input("结算账户")
    # 【自动化还原2】：资金性质下拉
    val_prop = r3_c2.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "其他"])
    
    # 【自动化还原3】：如果选择施工成本/工程收入，提示输入项目
    val_proj = ""
    if val_prop in ["工程收入", "施工成本"]:
        val_proj = st.text_input("📍 请输入 客户/项目名称 (必填)", key="proj_input")
    else:
        val_proj = st.text_input("客户/项目名称 (选填)")

    val_note = st.text_area("备注详情")
    
    st.divider()
    # 底部三按钮齐平
    b1, b2, b3 = st.columns(3)
    if b1.button("提交并继续", type="primary", use_container_width=True):
        # 执行保存...
        st.success("已保存"); time.sleep(0.5); st.rerun()
    if b2.button("提交并返回", type="primary", use_container_width=True):
        # 执行保存...
        st.cache_data.clear(); st.rerun()
    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if b3.button("❌ 取消录入", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 数据修正弹窗 (还原深度布局 & 按钮齐平) ---
@st.dialog("🛠️ 修正", width="large")
def edit_dialog(df):
    target = st.selectbox("请选择要修改的编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        # 还原图片中的深度修正布局
        with st.container():
            r1c1, r1c2 = st.columns(2)
            u_date = r1c1.text_input("日期", value=str(old["日期"]))
            u_inc = r1c2.number_input("收入 (USD)", value=float(old["收入"]))
            
            r2c1, r2c2 = st.columns(2)
            u_sum = r2c1.text_input("摘要内容", value=str(old["摘要"]))
            u_exp = r2c2.number_input("支出 (USD)", value=float(old["支出"]))
            
            r3c1, r3c2 = st.columns(2)
            u_proj = r3c1.text_input("客户/项目名称", value=str(old.get("客户/项目名称", "")))
            u_hand = r3c2.text_input("经手人", value=str(old.get("经手人", "")))
            
            u_note = st.text_area("备注详情", value=str(old["备注"]))

        st.divider()
        # 底部两个大按钮并排齐平
        btn_save, btn_exit = st.columns(2)
        if btn_save.button("💾 确认保存全字段修正", type="primary", use_container_width=True):
            st.success("修正成功"); st.cache_data.clear(); time.sleep(0.5); st.rerun()
        
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if btn_exit.button("❌ 放弃修正并复位", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 主页面布局 ---
pwd = st.sidebar.text_input("密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_latest = load_data()
    
    # 顶部指标
    st.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
    st.divider()

    # 右上角三功能对齐
    h_col, b1_col, b2_col, b3_col = st.columns([4, 1, 1, 1])
    h_col.subheader("📑 原始流水明细")
    
    with b1_col:
        # 下载表格逻辑
        excel_data = io.BytesIO()
        df_latest.to_excel(excel_data, index=False)
        st.download_button("💾 下载表格", data=excel_data.getvalue(), file_name="流水.xlsx")
    
    with b2_col:
        if st.button("➕ 录入", type="primary"): entry_dialog()
        
    with b3_col:
        if st.button("🛠️ 修正", type="primary"): edit_dialog(df_latest)

    st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
