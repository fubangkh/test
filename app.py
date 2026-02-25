import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from streamlit_gsheets import GSheetsConnection
from logic import get_live_rates, get_dynamic_options, ISO_MAP, prepare_new_data
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER
from forms import entry_dialog, edit_dialog, row_action_dialog

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="富邦日记账", layout="wide", page_icon="📊")

# ✅ 锁定金边时区 (全局唯一定义)
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
        # 使用 version 作为缓存键实现手动强刷，ttl=0 确保每次读取最新云端
        df = conn.read(worksheet="Summary", ttl=0)
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return pd.DataFrame()

    if df.empty or column_name not in df.columns:
        return ["-- 请选择 --", "➕ 新增..."]
    options = df[column_name].dropna().unique().tolist()
    # 过滤空值及特定排除项
    options = [opt for opt in options if opt and str(opt).strip() != "" and opt != "资金结转"]
    return ["-- 请选择 --"] + sorted(options) + ["➕ 新增..."]

# --- 3. 侧边栏 ---
with st.sidebar:
    st.title("💰 富邦日记账")
    # 显示实时金边时间，增强感知
    st.markdown(f"**📅 当前日期 (金边):** {datetime.now(LOCAL_TZ).strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    
    if st.button("🚪 退出/重置系统", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        st.session_state.table_version += 1
        st.cache_data.clear()
        st.rerun()
    
    st.info("💡 提示：此操作将清除本地缓存并重新从云端同步数据。")

# --- 4. 主页面数据加载 ---
df_main = load_data(version=st.session_state.table_version)

c_title, c_btn = st.columns([5, 2])
with c_title:
    st.header("📊 汇总统计")
with c_btn:
    st.write("##") 
    if st.button("➕ 新增流水录入", use_container_width=True):
        # 传递 LOCAL_TZ 确保录入时间正确
        entry_dialog(conn, load_data, LOCAL_TZ)

st.caption(f"🚀 系统就绪 | 数据库总行数: {len(df_main)} | 缓存版本: {st.session_state.table_version}")

# 处理弹窗调度
if st.session_state.get("show_edit_modal", False):
    edit_dialog(
        st.session_state.edit_target_id, 
        df_main, 
        conn, 
        LOCAL_TZ
    )

# --- 5. 数据预处理 (严谨处理：空值不回填) ---
if not df_main.empty:
    # 币种对齐，确保统计准确
    df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')
    
    # 辅助日期解析函数：仅用于看板统计，不影响原始数据显示
    def clean_date_for_stats(x):
        s = str(x).strip()
        if pd.isna(x) or s == "" or s.lower() == "nan":
            return pd.NaT # 重点：绝不填充当前时间，确保无数据的单据不参与统计
        try:
            dt = pd.to_datetime(s, errors='coerce')
            if pd.isna(dt): return pd.NaT
            return dt.replace(tzinfo=None) # 剥离时区以兼容筛选
        except:
            return pd.NaT

    # 生成隐藏辅助列，专供看板使用
    df_main['_calc_date'] = df_main['提交时间'].apply(clean_date_for_stats)

    # 数值列强制类型转换与清洗
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
    
    # 筛选当前月份数据
    mask_this_month = (
        (df_main['_calc_date'].dt.year == int(sel_year)) & 
        (df_main['_calc_date'].dt.month == int(sel_month))
    )
    df_this_month = df_main[mask_this_month].copy()
    
    # 指标计算
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

# --- 8. 各账户余额与支出排行 ---
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
            # 获取该账户最后一次使用的币种
            cur = group['实际币种'][group['实际币种'] != ""].iloc[-1] if not group['实际币种'].empty else "USD"
            return pd.Series([usd_bal, raw_bal, cur], index=['USD', 'RAW', 'CUR'])

        try:
            df_filtered = df_main[(df_main['结算账户'].notna()) & (df_main['结算账户'] != "") & (df_main['结算账户'] != "-- 请选择 --")].copy()
            if not df_filtered.empty:
                acc_stats = df_filtered.groupby('结算账户', group_keys=False).apply(calc_bank_balance).reset_index()
                
                # ✨ 修改点：从 logic 导入统一的 ISO_MAP
                from logic import ISO_MAP 
                acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: ISO_MAP.get(x, x))
                
                # 优化：给表格列换个更好看的中文名
                st.dataframe(
                    acc_stats[['结算账户', 'RAW', '原币种', 'USD']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "RAW": "原币余额",
                        "USD": "折合美元(USD)"
                    }
                )
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

# --- 9. 流水明细表 ---
st.subheader("📑 流水明细表")
if not df_main.empty:
    # 💡 排除所有以 "_" 开头的辅助列（比如 _calc_date）
    display_cols = [c for c in df_main.columns if not str(c).startswith('_')] 
    
    # 倒序展示
    view_df = df_main[display_cols].copy().iloc[::-1]
    
    # ✨ 核心优化：确保数据类型正确，并配置前端显示样式
    # 注意：不要使用 view_df.astype(object)，那会把数字变成对象导致格式化失效
    table_key = f"main_table_v_{st.session_state.table_version}"
    
    event = st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun", 
        selection_mode="single-row",
        key=table_key,
        # ✨ 核心渲染配置：实现千分符、2位小数、右对齐
        column_config={
            "实际金额": st.column_config.NumberColumn("实际金额", format="#,##0.00"),
            "收入(USD)": st.column_config.NumberColumn("收入(USD)", format="#,##0.00"),
            "支出(USD)": st.column_config.NumberColumn("支出(USD)", format="#,##0.00"),
            "余额(USD)": st.column_config.NumberColumn("余额(USD)", format="#,##0.00"),
            # 如果还有其他需要格式化的列，可以在此继续添加
        }
    )

    # 选中行逻辑
    if event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        # 传入 view_df.iloc[...] 包含的原始编号进行修正
        # 注意：这里我们传给 dialog 的依然是 view_df 里的原始数据
        row_action_dialog(view_df.iloc[selected_row_idx], df_main, conn)
