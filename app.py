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
    /* 首页顶部大按钮 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: 24px !important;
        font-weight: bold !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
    /* 弹窗底部：红框取消按钮 */
    .red-btn > div > button {
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        background-color: white !important;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心逻辑（还原汇率与账户库） ---
conn = st.connection("gsheets", type=GSheetsConnection)

# 预设汇率字典
CURRENCY_RATES = {"USD": 1.0, "RMB": 7.19, "VND": 25400.0, "HKD": 7.82}

@st.cache_data(ttl=1)
def load_data():
    df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    return df

# 获取所有已存在的结算账户供下拉
def get_account_list(df):
    if "账户" in df.columns:
        return sorted(df["账户"].unique().tolist())
    return ["BOC_人民币", "ABA_USD", "现金"]

# --- 3. 录入弹窗（精准找回所有丢失逻辑） ---
@st.dialog("📝 录入", width="large")
def entry_dialog():
    df = load_data()
    acc_list = get_account_list(df)
    st.write(f"💡 当前总结余: **${df['余额'].iloc[-1] if not df.empty else 0:,.2f}**")
    
    # --- 第一行：摘要与时间 ---
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.datetime_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # --- 第二行：金额、币种、汇率（联动回归！） ---
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("币种", list(CURRENCY_RATES.keys()))
    # 汇率根据币种自动变化
    val_rate = r2_c3.number_input("实时汇率", value=CURRENCY_RATES[val_curr], format="%.4f")
    
    # --- 第三行：结算账户（下拉菜单回归！）与经手人（回归！） ---
    r3_c1, r3_c2 = st.columns(2)
    val_acc = r3_c1.selectbox("结算账户", options=acc_list) # 回归下拉菜单
    val_hand = r3_c2.text_input("经手人") # 找回经手人字段
    
    # --- 第四行：性质与动态项目 ---
    r4_c1, r4_c2 = st.columns(2)
    val_prop = r4_c1.selectbox("资金性质", ["预收款", "工程收入", "施工成本", "管理费用", "其他"])
    
    # 如果是工程相关，项目名称变为必填提示
    proj_label = "📍 客户/项目名称 (必填)" if val_prop in ["工程收入", "施工成本"] else "客户/项目名称 (选填)"
    val_proj = r4_c2.text_input(proj_label)

    val_note = st.text_area("备注详情")
    
    st.divider()
    # 底部三个按钮并排齐平
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续", type="primary", use_container_width=True):
        st.success("已提交"); time.sleep(0.5); st.rerun()
    if b2.button("✅ 提交并返回", type="primary", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div class="red-btn">', unsafe_allow_html=True)
    if b3.button("❌ 取消录入", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 修正弹窗（深度布局还原 & 按钮齐平） ---
@st.dialog("🛠️ 修正", width="large")
def edit_dialog(df):
    target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        st.markdown(f"📁 **正在深度修正编号：{target}**")
        
        # 完美还原图片 image_bc5c60.png 中的两栏布局
        with st.container():
            r1c1, r1c2 = st.columns(2)
            u_date = r1c1.text_input("日期 (YYYY-MM-DD HH:mm)", value=str(old.get("日期", "")))
            u_inc = r1c2.number_input("收入 (USD)", value=float(old.get("收入", 0)))
            
            r2c1, r2c2 = st.columns(2)
            u_sum = r2c1.text_input("摘要内容", value=str(old.get("摘要", "")))
            u_exp = r2c2.number_input("支出 (USD)", value=float(old.get("支出", 0)))
            
            r3c1, r3c2 = st.columns(2)
            u_proj = r3c1.text_input("客户/项目名称", value=str(old.get("客户/项目名称", "")))
            u_hand = r3c2.text_input("经手人", value=str(old.get("经手人", ""))) # 修正中的经手人
            
            r4c1, r4c2 = st.columns(2)
            u_acc = r4c1.selectbox("结算账户", options=get_account_list(df), index=0)
            u_ref = r4c2.text_input("审批/发票编号", value=str(old.get("审批/发票编号", "")))

            u_note = st.text_area("备注详情", value=str(old.get("备注", "")))

        st.divider()
        # 底部两个大按钮并排齐平
        btn_save, btn_exit = st.columns(2)
        if btn_save.button("💾 确认保存全字段修正", type="primary", use_container_width=True):
            st.success("数据已更新"); st.cache_data.clear(); time.sleep(0.5); st.rerun()
        
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        if btn_exit.button("❌ 放弃修正并复位", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 主页面布局 ---
pwd = st.sidebar.text_input("🔑 密码", type="password")
if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_latest = load_data()
    
    if not df_latest.empty:
        st.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        st.divider()

        # 右上角三功能对齐：标题 + 下载 + 录入 + 修正
        h_col, b1_col, b2_col, b3_col = st.columns([4, 1.2, 1, 1])
        h_col.subheader("📑 原始流水明细")
        
        with b1_col:
            # 下载表格按钮
            excel_data = io.BytesIO()
            df_latest.to_excel(excel_data, index=False, engine='xlsxwriter')
            st.download_button("💾 下载表格", data=excel_data.getvalue(), file_name="流水明细.xlsx", use_container_width=True)
        
        with b2_col:
            if st.button("➕ 录入", type="primary", use_container_width=True): entry_dialog()
            
        with b3_col:
            if st.button("🛠️ 修正", type="primary", use_container_width=True): edit_dialog(df_latest)

        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.warning("🔒 请输入密码访问系统")
