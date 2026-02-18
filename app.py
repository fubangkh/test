import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import io
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 ---
st.set_page_config(page_title="富邦财务系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 视觉样式升级 (CSS) ---
st.markdown("""
    <style>
    /* 统一按钮基础样式 */
    div.stButton > button {
        border: None !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    
    /* 录入与修正按钮：蓝底白字，超大字体 */
    /* 注意：Streamlit 按钮在 CSS 中可能需要更具体的选择器 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: clamp(20px, 2vw, 32px) !important; 
        padding: 12px 0px !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.3) !important;
    }

    /* 下载表格按钮：绿底白字 */
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #28a745 0%, #218838 100%) !important;
        color: white !important;
        font-size: 18px !important;
        border: none !important;
        padding: 10px 0px !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
        filter: brightness(1.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 辅助函数 ---
def get_now_local():
    return datetime.now(LOCAL_TZ)

def get_now_str():
    return get_now_local().strftime("%Y-%m-%d %H:%M:%S")

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
    except:
        return pd.DataFrame()

# Excel 美化下载
def convert_df_to_excel(df):
    output = io.BytesIO()
    # 修复核心：确保安装了 xlsxwriter 并在代码中正确调用
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='流水明细')
            workbook  = writer.book
            worksheet = writer.sheets['流水明细']
            
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
            num_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
            border_format = workbook.add_format({'border': 1})

            for i, col in enumerate(df.columns):
                worksheet.write(0, i, col, header_format)
                worksheet.set_column(i, i, 18, border_format)
            
            for col_name in ["收入", "支出", "余额"]:
                if col_name in df.columns:
                    col_idx = df.columns.get_loc(col_name)
                    worksheet.set_column(col_idx, col_idx, 15, num_format)
        return output.getvalue()
    except Exception as e:
        st.error(f"Excel导出失败，请检查是否安装 xlsxwriter: {e}")
        return None

# --- 4. 弹窗函数 ---

@st.dialog("➕ 账目录入", width="large")
def entry_dialog():
    df_current = load_all_data()
    # ... 此处补全录入界面的 input 逻辑 ...
    st.write("### 录入界面")
    # 录入完成后增加三个按钮逻辑
    b1, b2, b3 = st.columns(3)
    b1.button("提交并继续", use_container_width=True)
    b2.button("提交并返回", use_container_width=True)
    b3.button("取消录入", use_container_width=True)

@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(df):
    target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        # ... 此处补全修正界面的 input 逻辑 ...
        st.write(f"正在修正：{target}")
        if st.button("确认保存全字段修正", use_container_width=True):
            st.success("保存成功")
            st.rerun()

# --- 5. 主页面布局 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    df_latest = load_all_data()
    
    if not df_latest.empty:
        # 指标展示
        m1, m2, m3 = st.columns(3)
        m1.metric("今日收入", f"${df_latest['收入'].sum():,.2f}")
        m2.metric("今日支出", f"${df_latest['支出'].sum():,.2f}")
        m3.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        
        st.divider()

        # --- 核心：标题与三按钮组对齐布局 ---
        # 调整比例确保按钮在右边对齐
        row_c1, row_c2, row_c3, row_c4 = st.columns([4, 1, 1, 1])
        
        with row_c1:
            st.subheader("📑 原始流水明细")

        with row_c2:
            # 下载表格按钮 (使用 secondary 样式)
            excel_bin = convert_df_to_excel(df_latest)
            if excel_bin:
                st.download_button(
                    label="💾 下载表格",
                    data=excel_bin,
                    file_name=f"流水明细_{get_now_local().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with row_c3:
            # 录入按钮 (使用 primary 样式)
            if st.button("➕ 录入", type="primary"):
                entry_dialog()

        with row_c4:
            # 修正按钮 (使用 primary 样式)
            if st.button("🛠️ 修正", type="primary"):
                edit_dialog(df_latest)

        # 数据表格展示
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), 
                     hide_index=True, use_container_width=True, height=600)
else:
    st.warning("请输入正确密码以访问系统")
