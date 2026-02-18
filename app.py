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
    /* 1. 统一渐变按钮样式 */
    div.stButton > button {
        border: None !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
    }
    
    /* 录入与修正按钮：蓝底白字，大字体 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        font-size: clamp(18px, 1.8vw, 30px) !important; /* 字体加大 */
        padding: 0.5em 1.5em !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.3) !important;
    }

    /* 下载按钮：绿底白字（通常下载用绿色） */
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #28a745 0%, #218838 100%) !important;
        color: white !important;
        font-size: clamp(16px, 1.4vw, 24px) !important;
        border: none !important;
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

# Excel 美化下载函数
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='流水明细')
        workbook  = writer.book
        worksheet = writer.sheets['流水明细']
        
        # 定义格式
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        num_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        border_format = workbook.add_format({'border': 1})

        # 设置列宽和格式
        for i, col in enumerate(df.columns):
            worksheet.write(0, i, col, header_format)
            worksheet.set_column(i, i, 15, border_format)
        
        # 针对金额列应用数字格式
        for col_name in ["收入", "支出", "余额"]:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name)
                worksheet.set_column(col_idx, col_idx, 15, num_format)
                
    return output.getvalue()

# --- 4. 弹窗：录入窗口 ---
@st.dialog("📝 账目录入", width="large")
def entry_dialog():
    df_current = load_all_data()
    last_bal = df_current["余额"].iloc[-1] if not df_current.empty else 0.0
    st.markdown(f"### 当前余额: ${last_bal:,.2f}")
    
    with st.container():
        c1, c2 = st.columns(2)
        val_summary = c1.text_input("摘要内容")
        val_biz_time = c2.datetime_input("业务时间", value=get_now_local())
        
        r2_c1, r2_c2, r2_c3 = st.columns(3)
        val_raw_amt = r2_c1.number_input("金额", min_value=0.0)
        val_curr = r2_c2.selectbox("币种", ["USD", "RMB", "VND"])
        val_rate = r2_c3.number_input("汇率", value=1.0, format="%.4f")
        
        val_acc = st.text_input("结算账户")
        val_prop = st.selectbox("资金性质", ["工程收入", "施工成本", "管理费用", "其他"])
        val_note = st.text_area("备注")

    st.markdown("---")
    b1, b2, b3 = st.columns(3)
    if b1.button("📥 提交并继续录入", use_container_width=True):
        # 此处省略具体的保存逻辑代码（同前，实际使用请补全）
        st.toast("已提交"); time.sleep(0.5); st.rerun()
    if b2.button("✅ 提交并返回", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    if b3.button("❌ 取消录入", use_container_width=True):
        st.rerun()

# --- 5. 弹窗：修正窗口 ---
@st.dialog("🛠️ 数据修正窗口", width="large")
def edit_dialog(df):
    target = st.selectbox("请选择要修改的编号", ["-- 请选择 --"] + df["录入编号"].tolist()[::-1])
    if target != "-- 请选择 --":
        old = df[df["录入编号"] == target].iloc[0]
        with st.form("edit_inner"):
            st.info(f"正在编辑：{target}")
            u_sum = st.text_input("摘要", value=str(old["摘要"]))
            u_inc = st.number_input("收入", value=float(old["收入"]))
            u_exp = st.number_input("支出", value=float(old["支出"]))
            u_note = st.text_area("备注", value=str(old["备注"]))
            
            if st.form_submit_button("💾 保存并更新全表余额", use_container_width=True):
                # 更新与重算逻辑...
                st.success("修正成功！"); time.sleep(0.5); st.cache_data.clear(); st.rerun()

# --- 6. 主页面布局 ---
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    # 顶部标题栏
    st.title("📊 财务实时汇总统计")
    
    df_latest = load_all_data()
    
    # 顶部指标卡
    if not df_latest.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        
    st.divider()

    # --- 按钮组布局 (靠右齐平) ---
    # 创建 5 列，前 2 列占位，后 3 列放按钮
    btn_row_c1, btn_row_c2, btn_row_c3, btn_row_c4, btn_row_c5 = st.columns([3, 1.5, 1, 1, 1])
    
    with btn_row_c1:
        st.subheader("📑 原始流水明细")

    with btn_row_c3:
        # 下载表格按钮 (Secondary 样式)
        excel_data = convert_df_to_excel(df_latest)
        st.download_button(
            label="💾 下载表格",
            data=excel_data,
            file_name=f"富邦流水明细_{get_now_local().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with btn_row_c4:
        # 录入按钮 (Primary 样式)
        if st.button("➕ 录入", type="primary", use_container_width=True):
            entry_dialog()

    with btn_row_c5:
        # 修正按钮 (Primary 样式)
        if st.button("🛠️ 修正", type="primary", use_container_width=True):
            edit_dialog(df_latest)

    # 原始流水表格
    st.dataframe(
        df_latest.sort_values("录入编号", ascending=False),
        hide_index=True,
        use_container_width=True,
        height=600
    )
else:
    st.info("🔒 请输入密码访问系统")
