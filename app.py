import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import time
from streamlit_gsheets import GSheetsConnection

# 导入自定义模块
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="财务流水管理系统", layout="wide", page_icon="📊")
LOCAL_TZ = pytz.timezone("Asia/Shanghai")

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
        # ttl=0 配合 version 实现强制刷新
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
    st.markdown(f"**📅 当前日期:** {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d')}")
    st.divider()
    
    if st.button("🚪 退出/重置系统", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        st.session_state.table_version += 1
        st.cache_data.clear()
        st.rerun()
    
    st.info("💡 提示：点击退出将刷新数据缓存并重置所有选择。")

# --- 4. 主页面布局 ---
df_main = load_data(version=st.session_state.table_version)

# 录入按钮布局
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

if df_main.empty:
    st.warning("⚠️ 数据库目前没有数据。")
    if st.button("➕ 立即录入第一笔", key="empty_add"):
        entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options)

# --- 5. 数据预处理 (如实反映版：不自动填充当前时间) ---
if not df_main.empty:
    df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')
    
    # 【核心逻辑修正】
    def clean_date_for_stats(x):
        try:
            if pd.isna(x) or str(x).strip() == "":
                return pd.NaT # 真正为空时不填充，返回空日期
            s = str(x).strip()
            dt = pd.to_datetime(s, errors='coerce')
            if pd.isna(dt):
                return pd.NaT
            return dt.replace(tzinfo=None)
        except:
            return pd.NaT

    # 创建一个隐藏的辅助列专门用于看板计算，不显示在表格里
    df_main['_calc_date'] = df_main['提交时间'].apply(clean_date_for_stats)

    # 数值清洗
    for col in ['收入(USD)', '支出(USD)', '余额(USD)', '实际金额']:
        if col in df_main.columns:
            df_main[col] = (
                df_main[col]
                .astype(str)
                .str.replace(r'[$,\s]', '', regex=True)
                .pipe(pd.to_numeric, errors='coerce')
                .fillna(0.0)
            )

# --- 6. 生成时间筛选列表 ---
current_now = datetime.now(LOCAL_TZ)
try:
    if not df_main.empty:
        # 只从有效日期中提取年份
        valid_dates = df_main['_calc_date'].dropna()
        if not valid_dates.empty:
            year_list = sorted(valid_dates.dt.year.unique().tolist(), reverse=True)
        else:
            year_list = [current_now.year]
    else:
        year_list = [current_now.year]
except Exception:
    year_list = [current_now.year]
    
month_list = list(range(1, 13))

# --- 7. 时间维度看板 ---
with st.container(border=True):
    st.markdown("### 📅 时间维度看板") 
    
    c1, c2, c3 = st.columns([2, 2, 5]) 
    with c1:
        sel_year = st.selectbox("年份", year_list, index=0, label_visibility="collapsed")
    with c2:
        sel_month = st.selectbox("月份", month_list, index=datetime.now(LOCAL_TZ).month - 1, label_visibility="collapsed")
    
    # 使用辅助列进行筛选
    mask_this_month = (
        (df_main['_calc_date'].dt.year == int(sel_year)) & 
        (df_main['_calc_date'].dt.month == int(sel_month))
    )
    df_this_month = df_main[mask_this_month].copy()
    
    lm = 12 if sel_month == 1 else sel_month - 1
    ly = sel_year - 1 if sel_month == 1 else sel_year
    mask_last_month = (
        (df_main['_calc_date'].dt.year == int(ly)) & 
        (df_main['_calc_date'].dt.month == int(lm))
    )
    df_last_month = df_main[mask_last_month].copy()
    
    tm_inc = df_this_month['收入(USD)'].sum()
    tm_exp = df_this_month['支出(USD)'].sum()
    lm_inc = df_last_month['收入(USD)'].sum()
    lm_exp = df_last_month['支出(USD)'].sum()
    
    inc_delta = tm_inc - lm_inc
    exp_delta = tm_exp - lm_exp
    t_balance = df_main['收入(USD)'].sum() - df_main['支出(USD)'].sum()

    with c3:
        st.markdown(f"""<div style="margin-top: 7px; padding-left: 5px;"><span style="font-size: 1.2rem; font-weight: bold; color: #31333F;">💡 当前统计周期：<span style="color: #4CAF50;">{sel_year}年{sel_month}月</span></span></div>""", unsafe_allow_html=True)
    st.markdown("---")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {sel_month}月收入", f"${tm_inc:,.2f}", delta=f"{inc_delta:,.2f}")
    m2.metric(f"📉 {sel_month}月支出", f"${tm_exp:,.2f}", delta=f"{exp_delta:,.2f}", delta_color="inverse")
    m3.metric("🏦 累计总结余", f"${t_balance:,.2f}")

st.divider()

# --- 8. 账户余额与排行 ---
col_l, col_r = st.columns([1.6, 1])
with col_l:
    st.write("🏦 **各账户当前余额 (原币对账)**")
    if df_main.empty:
        st.info("💡 数据库目前为空。")
    else:
        def calc_bank_balance(group):
            inc_clean = group['收入(USD)']
            exp_clean = group['支出(USD)']
            amt_clean = group['实际金额']
            def get_raw_val(idx):
                current_val = amt_clean.loc[idx]
                if current_val == 0 or pd.isna(current_val):
                    if inc_clean.loc[idx] > 0: current_val = inc_clean.loc[idx]
                    elif exp_clean.loc[idx] > 0: current_val = exp_clean.loc[idx]
                    else: current_val = 0
                return -current_val if exp_clean.loc[idx] > 0 else current_val
            usd_bal = inc_clean.sum() - exp_clean.sum()
            raw_bal = sum(get_raw_val(idx) for idx in group.index)
            valid_currencies = group['实际币种'][group['实际币种'] != ""].tolist()
            cur_name = valid_currencies[-1] if valid_currencies else "USD"
            return pd.Series([usd_bal, raw_bal, cur_name], index=['USD', 'RAW', 'CUR'])

        try:
            df_filtered = df_main[(df_main['结算账户'].notna()) & (df_main['结算账户'] != "") & (df_main['结算账户'] != "-- 请选择 --")].copy()
            if not df_filtered.empty:
                acc_stats = df_filtered.groupby('结算账户', group_keys=False).apply(calc_bank_balance).reset_index()
                iso_map = {"人民币": "CNY", "CNY": "CNY", "港币": "HKD", "HKD": "HKD", "印尼盾": "IDR", "IDR": "IDR", "越南盾": "VND", "VND": "VND", "瑞尔": "KHR", "KHR": "KHR", "美元": "USD", "USD": "USD"}
                acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: iso_map.get(x, x))
                display_acc = acc_stats[['结算账户', 'RAW', '原币种', 'USD']].copy()
                styled_acc = display_acc.style.format({'RAW': '{:,.2f}', 'USD': '${:,.2f}'}).map(lambda x: 'color: #d32f2f;' if isinstance(x, (int, float)) and x < -0.01 else 'color: #31333F;', subset=['RAW', 'USD'])
                st.dataframe(styled_acc, use_container_width=True, hide_index=True, column_config={"结算账户": st.column_config.TextColumn("账户", width="medium"), "RAW": st.column_config.NumberColumn("原币余额", width="small"), "原币种": st.column_config.TextColumn("原币种", width="small"), "USD": st.column_config.NumberColumn("折合美元 (USD)", width="small")})
        except Exception as e:
            st.error(f"📊 余额计算异常: {e}")

with col_r:
    st.write(f"🏷️ **{sel_month}月支出排行**")
    exp_stats = df_this_month[df_this_month['支出(USD)'] > 0].groupby('资金性质')[['支出(USD)']].sum().sort_values(by='支出(USD)', ascending=False).reset_index()
    if not exp_stats.empty:
        styled_exp = exp_stats.style.format({"支出(USD)": "${:,.2f}"}).map(lambda x: 'color: #d32f2f; text-align: right;', subset=['支出(USD)'])
        st.dataframe(styled_exp, use_container_width=True, hide_index=True, column_config={"资金性质": st.column_config.TextColumn("资金性质", width="medium"), "支出(USD)": st.column_config.NumberColumn("支出金额", width="medium")})
    else:
        st.caption("该月暂无支出记录")

st.divider()

# --- 9. 数据明细表 (如实展示：隐藏辅助列) ---
st.subheader("📑 财务流水账目明细")
if not df_main.empty:
    # 核心：只选取原始存在的列，不选取我们生成的 _calc_date 列
    all_cols = df_main.columns.tolist()
    display_cols = [c for c in all_cols if not c.startswith('_')] # 排除隐藏列
    
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

    if event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        row_action_dialog(view_df.iloc[selected_row_idx], df_main, conn)
