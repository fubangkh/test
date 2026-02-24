import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection

# 导入自定义模块
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# =========================================================
# 1. 基础配置与环境初始化
# =========================================================
st.set_page_config(page_title="财务流水管理系统", layout="wide", page_icon="📊")

# 时区与全局变量初始化
LOCAL_TZ = pytz.timezone("Asia/Shanghai")

if "table_version" not in st.session_state:
    st.session_state.table_version = 0

# 🛠️ 关键修复：初始化弹窗控制状态
if "show_edit_modal" not in st.session_state:
    st.session_state.show_edit_modal = False
if "edit_target_id" not in st.session_state:
    st.session_state.edit_target_id = None

# 隐藏 Streamlit 默认页眉页脚
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# =========================================================
# 2. 数据核心引擎 (Read/Load)
# =========================================================
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data(version=0):
    """从云端读取 Summary 表数据"""
    try:
        df = conn.read(worksheet="Summary", ttl=0)
        # 确保数值列正确加载
        for col in ['收入(USD)', '支出(USD)', '余额(USD)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

def get_live_rates():
    """获取实时汇率"""
    return {"USD": 1.0, "CNY": 7.21, "KHR": 4050.0, "THB": 35.8}

def get_dynamic_options(df, column_name):
    """从现有表格提取去重后的下拉选项"""
    if df.empty or column_name not in df.columns:
        return ["-- 请选择 --", "➕ 新增..."]
    options = df[column_name].dropna().unique().tolist()
    options = [opt for opt in options if opt and str(opt).strip() != "" and opt != "资金结转"]
    return ["-- 请选择 --"] + sorted(options) + ["➕ 新增..."]

# =========================================================
# 3. 侧边栏与数据预加载
# =========================================================
df = load_data(version=st.session_state.table_version)

with st.sidebar:
    st.title("💰 财务管理")
    st.write(f"📅 报表日期: {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d')}")
    st.divider()
    
    if st.button("➕ 新增流水录入", type="primary", use_container_width=True):
        entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options)
    
    st.divider()
    st.info("💡 提示：点击明细表中的行可进行‘修正’或‘删除’操作。")

# =========================================================
# 4. 大屏统计看板
# =========================================================
if not df.empty:
    latest_balance = df['余额(USD)'].iloc[-1]
    total_inc = df['收入(USD)'].sum()
    total_exp = df['支出(USD)'].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("累计总收入 (USD)", f"$ {total_inc:,.2f}")
    m2.metric("累计总支出 (USD)", f"$ {total_exp:,.2f}")
    m3.metric("当前总结余 (USD)", f"$ {latest_balance:,.2f}", delta_color="normal")
else:
    st.warning("📭 暂无财务记录，请点击左侧‘新增录入’开始。")

st.divider()

# =========================================================
# 5. 明细表展示与弹窗调度逻辑
# =========================================================
st.subheader("📑 财务明细账目")

view_df = df.copy()
if not view_df.empty:
    view_df = view_df.iloc[::-1] # 逆序展示
    
    # 定义表格，使用 key 确保状态唯一
    event = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "收入(USD)": st.column_config.NumberColumn(format="$ %.2f"),
            "支出(USD)": st.column_config.NumberColumn(format="$ %.2f"),
            "余额(USD)": st.column_config.NumberColumn(format="$ %.2f"),
            "提交时间": st.column_config.DatetimeColumn(format="MM-DD HH:mm")
        },
        on_select="rerun", 
        selection_mode="single-row",
        key="data_table"
    )

    # 🛠️ 关键修复：弹窗调度逻辑 (if...elif 互斥结构)
    
    # 1. 检查是否需要打开“数据修正”对话框 (优先级最高)
    if st.session_state.show_edit_modal:
        edit_dialog(
            target_id=st.session_state.edit_target_id,
            full_df=df,
            conn=conn,
            get_live_rates=get_live_rates,
            get_dynamic_options=get_dynamic_options,
            LOCAL_TZ=LOCAL_TZ
        )
    
    # 2. 如果没有修正任务，再检查表格是否有行被选中
    elif len(event.selection.rows) > 0:
        selected_row_idx = event.selection.rows[0]
        target_row_data = view_df.iloc[selected_row_idx]
        row_action_dialog(target_row_data, df, conn)
