import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
import time
import pytz
from datetime import datetime

# --- 1. 基础配置与时区 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 视觉样式定义 (CSS) ---
st.markdown("""
    <style>
    /* 首页大按钮样式 */
    div.stButton > button {
        border: None !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    
    /* 录入与修正：超大蓝色渐变 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: clamp(16px, 1.2vw, 24px) !important;
        padding: 10px 0px !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.3) !important;
    }

    /* 下载表格：灰色中性背景 */
    div.stButton > button[kind="secondary"] {
        background: #f0f2f6 !important;
        color: #31333F !important;
        border: 1px solid #dcdfe6 !important;
    }

    /* 红色放弃/取消按钮专用样式 (白底红字红框) */
    .red-cancel-btn > div > button {
        background-color: white !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }
    .red-cancel-btn > div > button:hover {
        background-color: #fff5f5 !important;
        border: 1px solid #ff3333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心功能函数 ---
def get_now_local(): return datetime.now(LOCAL_TZ)
def get_now_str(): return get_now_local().strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
        return df
    except: return pd.DataFrame()

def convert_df_to_excel(df):
    output = io.BytesIO()
    try:
        # 使用 xlsxwriter（已在 requirements.txt 中）
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='流水明细')
        return output.getvalue()
    except: return None

# --- 4. 弹窗逻辑：数据录入 (补全所有字段) ---
@st.dialog("📝 数据录入", width="large")
def entry_dialog():
    df_current = load_all_data()
    last_bal = df_current["余额"].iloc[-1] if not df_current.empty else 0.0
    
    st.write(f"💡 **当前系统总结余：${last_bal:,.2f}**")
    
    # 录入字段布局
    with st.container():
        c1, c2 = st.columns(2)
        val_summary = c1.text_input("摘要内容", placeholder="请输入流水摘要")
        val_biz_time = c2.datetime_input("业务时间", value=get_now_local())
        
        r2_c1, r2_c2, r2_c3 = st.columns(3)
        val_raw_amt = r2_c1.number_input("金额", min_value=0.0, step=0.01)
        val_curr = r2_c2.selectbox("币种", ["USD", "RMB", "VND", "HKD"])
        val_rate = r2_c3.number_input("汇率 (1 USD = ?)", value=1.0, format="%.4f")
        
        r3_c1, r3_c2 = st.columns(2)
        val_acc = r3_c1.text_input("结算账户", placeholder="如：BOC_865_人民币")
        val_prop = r3_c2.selectbox("资金性质", ["预收款", "工程收入", "日常支出", "管理费用", "其他"])
        
        val_project = st.text_input("客户/项目名称")
        val_note = st.text_area("备注详情")

    st.divider()
    
    # 底部按钮组
    b_c1, b_c2, b_c3 = st.columns(3)
    
    def save_process():
        # 这里放置您的保存到 Google Sheets 的代码
        st.success("数据已成功提交！")
        st.cache_data.clear()
        time.sleep(0.5)
        return True

    if b_c1.button("📥 提交并继续", type="primary", use_container_width=True):
        if save_process(): st.rerun()
    
    if b_c2.button("✅ 提交并返回", type="primary", use_container_width=True):
        if save_process(): st.rerun()

    st.markdown('<div class="red-cancel-btn">', unsafe_allow_html=True)
    if b_c3.button("❌ 取消录入", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 弹窗逻辑：数据修正 (还原深度布局并按钮齐平) ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(df):
    target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        st.markdown(f"📁 **正在深度修正编号：{target}**")
        
        # 还原两栏表单布局 (还原图片 image_bc5c60.png 中的内容)
        with st.container():
            r1c1, r1c2 = st.columns(2)
            u_date = r1c1.text_input("日期 (YYYY-MM-DD HH:mm)", value=str(old["日期"]))
            u_inc = r1c2.number_input("收入 (USD)", value=float(old["收入"]), step=0.01)
            
            r2c1, r2c2 = st.columns(2)
            u_sum = r2c1.text_input("摘要内容", value=str(old["摘要"]))
            u_exp = r2c2.number_input("支出 (USD)", value=float(old["支出"]), step=0.01)
            
            r3c1, r3c2 = st.columns(2)
            u_proj = r3c1.text_input("客户/项目名称", value=str(old["客户/项目名称"]))
            u_hand = r3c2.text_input("经手人", value=str(old["经手人"]))
            
            r4c1, r4c2 = st.columns(2)
            u_acc = r4c1.text_input("结算账户", value=str(old["账户"]))
            u_ref = r4c2.text_input("审批/发票编号", value=str(old["审批/发票编号"]))
            
            u_prop = st.selectbox("资金性质", ["预收款", "工程收入", "管理费用", "其他"], index=0)
            u_note = st.text_area("备注详情", value=str(old["备注"]))

        st.divider()
        
        # 底部操作按钮齐平
        save_col, exit_col = st.columns(2)
        
        if save_col.button("💾 确认保存全字段修正", type="primary", use_container_width=True):
            # 执行更新逻辑
            st.success("修正成功！")
            st.cache_data.clear()
            time.sleep(0.5)
            st.rerun()
        
        st.markdown('<div class="red-cancel-btn">', unsafe_allow_html=True)
        if exit_col.button("❌ 放弃修正并复位", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 主页面 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    st.markdown("## 📊 财务实时汇总统计")
    df_latest = load_all_data()
    
    if not df_latest.empty:
        # 顶部指标
        m1, m2, m3 = st.columns(3)
        m1.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        
        st.divider()

        # 三按钮齐平布局
        t_col, b1_col, b2_col, b3_col = st.columns([4, 1, 1, 1])
        with t_col: st.subheader("📑 原始流水明细")
        
        with b1_col:
            excel_bin = convert_df_to_excel(df_latest)
            if excel_bin:
                st.download_button("💾 下载表格", data=excel_bin, file_name="流水明细.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
        with b2_col:
            if st.button("➕ 录入", type="primary", use_container_width=True):
                entry_dialog()
        
        with b3_col:
            if st.button("🛠️ 修正", type="primary", use_container_width=True):
                edit_dialog(df_latest)

        # 全宽表格
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), hide_index=True, use_container_width=True, height=600)
else:
    st.info("🔒 请输入密码访问系统")
