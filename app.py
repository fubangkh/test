import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection

# 导入自定义模块
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="财务流水管理系统", layout="wide", page_icon="📊")

# ✅ 找回并锁定您的金边时区
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# 初始化全局状态
if "table_version" not in st.session_state:
    st.session_state.table_version = 0
if "show_edit_modal" not in st.session_state:
    st.session_state.show_edit_modal = False
if "edit_target_id" not in st.session_state:
    st.session_state.edit_target_id = None

# --- 2. 数据加载函数 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data(version=0):
    try:
        # 使用 version 作为缓存键实现手动强刷
        df = conn.read(worksheet="Summary", ttl=0)
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

def get_live_rates():
    return {"USD": 1.0, "CNY": 7.21, "KHR": 4050.0, "THB": 35.8}

def get_dynamic_options(df, column_name):
    if df.empty or column_name not in df.columns:
        return ["-- 请选择 --", "➕ 新增..."]
    options = df[column_name].dropna().unique().tolist()
    options = [opt for opt in options if opt and str(opt).strip() != "" and opt != "资金结转"]
    return ["-- 请选择 --"] + sorted(options) + ["➕ 新增..."]

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("💰 财务管理系统")
    st.markdown(f"**📅 当前日期 (金边):** {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    if st.button("🚪 退出/重置系统", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        st.session_state.table_version += 1
        st.cache_data.clear()
        st.rerun()
    
    st.info("💡 提示：此操作将清除本地缓存并重新从云端同步数据。")

# --- 4. 主页面布局 ---
df_main = load_data(version=st.session_state.table_version)

c_title, c_btn = st.columns([5, 2])
with c_title:
    st.header("📊 汇总统计")
with c_btn:
    st.write("##") 
    if st.button("➕ 新增流水录入", type="primary", use_container_width=True):
        entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options)

st.caption(f"🚀 系统就绪 | 数据库总行数: {len(df_main)} | 缓存版本: {st.session_state.table_version}")

# 弹窗调度
if st.session_state.get("show_edit_modal", False):
    edit_dialog(st.session_state.edit_target_id, df_main, conn, get_live_rates, get_dynamic_options, LOCAL_TZ)

# --- 5. 数据预处理 (如实反映：空即是空) ---
if not df_main.empty:
    # 币种对齐
    df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')
    
    # 【修正解析逻辑】仅解析，绝不自动填充 datetime.now()
    def clean_date_for_stats(x):
        s = str(x).strip()
        if pd.isna(x) or s == "" or s.lower() == "nan":
            return pd.NaT # 真正为空时不填充
        try:
            # 统一尝试 Pandas 解析
            dt = pd.to_datetime(s, errors='coerce')
            if pd.isna(dt):
                return pd.NaT
            # 剥离时区信息以支持表格筛选
            return dt.replace(tzinfo=None)
        except:
            return pd.NaT

    # 建立隐藏辅助列，专门用于看板月份计算，避免干扰原始列显示
    df_main['_calc_date'] = df_main['提交时间'].apply(clean_date_for_stats)

    # 数值列清洗
    for col in ['收入(USD)', '支出(USD)', '余额(USD)', '实际金额']:
        if col in df_main.columns:
            df_main[col] = (
                df_main[col]
                .astype(str)
                .str.replace(r'[$,\s]', '', regex=True)
                .pipe(pd.to_numeric, errors='coerce')
                .fillna(0.0)
            )

# --- 6. 生成看板筛选列表 ---
current_now = datetime.now(LOCAL_TZ)
try:
    if not df_main.empty:
        # 只从有日期记录的行里提取年份
        valid_dates = df_main['_calc_date'].dropna()
        if not valid_dates.empty:
            year_list = sorted(valid_dates.dt.year.unique().tolist(), reverse=True)
        else:
            year_list = [current_now.year]
    else:
        year_list = [current_now.year]
except:
    year_list = [current_now.year]
    
month_list = list(range(1, 13))

# --- 7. 时间维度看板 ---
with st.container(border=True):
    st.markdown("### 📅 时间维度看板") 
    c1, c2, c3 = st.columns([2, 2, 5]) 
    with c1:
        sel_year = st.selectbox("年份", year_list, index=0, label_visibility="collapsed")
    with c2:
        sel_month = st.selectbox("月份", month_list, index=current_now.month - 1, label_visibility="collapsed")
    
    # 基于辅助列进行月份统计筛选
    mask_this_month = (
        (df_main['_calc_date'].dt.year == int(sel_year)) & 
        (df_main['_calc_date'].dt.month == int(sel_month))
    )
    df_this_month = df_main[mask_this_month].copy()
    
    # 计算月度统计数据
    tm_inc = df_this_month['收入(USD)'].sum()
    tm_exp = df_this_month['支出(USD)'].sum()
    t_balance = df_main['收入(USD)'].sum() - df_main['支出(USD)'].sum()

    with c3:
        st.markdown(f"""
            <div style="margin-top: 7px; padding-left: 5px;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #31333F;">
                    💡 当前统计周期：<span style="color: #4CAF50;">{sel_year}年{sel_month}月</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {sel_month}月收入", f"${tm_inc:,.2f}")
    m2.metric(f"📉 {sel_month}月支出", f"${tm_exp:,.2f}")
    m3.metric("🏦 累计总结余", f"${t_balance:,.2f}")

st.divider()

# --- 8. 余额对账与排行 ---
col_l, col_r = st.columns([1.6, 1])
with col_l:
    st.write("🏦 **各账户当前余额 (原币对账)**")
    if not df_main.empty:
        def calc_bank_balance(group):
            inc, exp, amt = group['收入(USD)'], group['支出(USD)'], group['实际金额']
            def get_raw_val(idx):
                val = amt.loc[idx]
                if val == 0 or pd.isna(val):
                    val = inc.loc[idx] if inc.loc[idx] > 0 else exp.loc[idx]
                return -val if exp.loc[idx] > 0 else val
            usd_bal = inc.sum() - exp.sum()
            raw_bal = sum(get_raw_val(idx) for idx in group.index)
            cur = group['实际币种'][group['实际币种'] != ""].iloc[-1] if not group['实际币种'].empty else "USD"
            return pd.Series([usd_bal, raw_bal, cur], index=['USD', 'RAW', 'CUR'])

        try:
            df_filtered = df_main[(df_main['结算账户'].notna()) & (df_main['结算账户'] != "") & (df_main['结算账户'] != "-- 请选择 --")].copy()
            if not df_filtered.empty:
                acc_stats = df_filtered.groupby('结算账户', group_keys=False).apply(calc_bank_balance).reset_index()
                iso_map = {"人民币": "CNY", "CNY": "CNY", "港币": "HKD", "HKD": "HKD", "瑞尔": "KHR", "KHR": "KHR", "美元": "USD", "USD": "USD"}
                acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: iso_map.get(x, x))
                st.dataframe(acc_stats[['结算账户', 'RAW', '原币种', 'USD']], use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"📊 余额计算异常: {e}")

with col_r:
    st.write(f"🏷️ **{sel_month}月支出排行**")
    exp_stats = df_this_month[df_this_month['支出(USD)'] > 0].groupby('资金性质')[['支出(USD)']].sum().sort_values(by='支出(USD)', ascending=False).reset_index()
    if not exp_stats.empty:
        st.dataframe(exp_stats.style.format({"支出(USD)": "${:,.2f}"}), use_container_width=True, hide_index=True)
    else:
        st.caption("该月暂无支出记录")

st.divider()

# --- 9. 数据明细表 (如实反映原始数据) ---
st.subheader("📑 财务流水账目明细")
if not df_main.empty:
    # 💡 核心修正：只展示 Google Sheets 里的原始列，彻底排除后台辅助列
    # 辅助列统一以 "_" 开头，我们将其过滤掉
    display_cols = [c for c in df_main.columns if not str(c).startswith('_')] 
    
    # 倒序展示，让最新录入在最上面
    view_df = df_main[display_cols].copy().iloc[::-1]
    
    table_key = f"main_table_v_{st.session_state.table_version}"
    event = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        key=table_key
    )

    # 选中行逻辑
    if event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        row_action_dialog(view_df.iloc[selected_row_idx], df_main, conn)
