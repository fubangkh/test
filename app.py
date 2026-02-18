import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 联动逻辑函数 ---
def handle_currency_change():
    new_curr = st.session_state.sel_curr
    st.session_state.input_rate = float(get_reference_rate(df_latest, new_curr))

def handle_shortcut_change():
    choice = st.session_state.shortcut_select
    if choice != "--- 🔍 输入关键词搜索摘要 ---":
        month_str = datetime.now(LOCAL_TZ).strftime('%m')
        st.session_state.summary_input = f"{choice} ({month_str}月)"

def get_reference_rate(df_history, currency):
    if currency == "USD": return 1.0
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        df_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1)
        if res.status_code == 200:
            api = res.json().get("rates", {})
            rates = {"RMB": api.get("CNY", 7.23), "VND": api.get("VND", 25450.0), "HKD": api.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

# --- 3. 数据加载 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        try:
            df_cfg = conn.read(worksheet="Config", ttl=0).dropna(how="all")
            shortcuts = sorted([s for s in df_cfg["快捷摘要"].dropna().tolist() if s])
        except: shortcuts = []
        return df, shortcuts
    except: return pd.DataFrame(), []

df_latest, SHORTCUT_SUMMARIES = load_all_data()

# 初始化状态
if 'input_rate' not in st.session_state: st.session_state.input_rate = 1.0
if 'summary_input' not in st.session_state: st.session_state.summary_input = ""

# 安全提取列表函数
def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and str(x).strip() != ""])

# --- 4. 界面展示 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 智能财务录入系统")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 账户总结余：**${last_bal:,.2f}** | {get_now_str()}")
    
    # --- 模块 1：业务描述 ---
    st.markdown("### 1️⃣ 业务摘要")
    shortcut_options = ["--- 🔍 输入关键词搜索摘要 ---"] + SHORTCUT_SUMMARIES
    st.selectbox("⚡ 快捷搜索摘要词库", shortcut_options, key="shortcut_select", on_change=handle_shortcut_change)
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        summary = st.text_input("摘要确认 (必填)", key="summary_input")
    with col_b:
        biz_date = st.date_input("业务日期", value=datetime.now(LOCAL_TZ))

    # --- 模块 2：财务金额 ---
    st.markdown("### 2️⃣ 金额与结算")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        ALL_PROPS = ["期初结存", "内部调拨-转入", "内部调拨-转出", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
        fund_p = st.selectbox("资金性质", ALL_PROPS)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with cc2:
        raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
        ex_rate = st.number_input("实时汇率", key="input_rate", format="%.4f")
        if ex_rate > 0:
            converted = raw_amt / ex_rate
            if currency != "USD":
                st.metric("📊 换算美元", f"${converted:,.2f}")
    with cc3:
        # 结算账户搜索
        accs_list = get_unique_list(df_latest, "账户")
        a_sel = st.selectbox("结算账户 (🔍搜索)", ["🔍 选择历史账户"] + accs_list + ["➕ 新增账户"])
        new_a = st.text_input("✍️ 输入新账户名") if a_sel == "➕ 新增账户" else ""

    # --- 模块 3：相关方信息 ---
    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        # 项目搜索
        projs_list = get_unique_list(df_latest, "客户/项目名称")
        p_sel = st.selectbox("项目/客户 (🔍搜索)", ["🔍 选择历史项目"] + projs_list + ["➕ 新增项目"])
        new_p = st.text_input("✍️ 输入新项目名") if p_sel == "➕ 新增项目" else ""
    with hc2:
        # 经手人搜索
        hands_list = get_unique_list(df_latest, "经手人")
        h_sel = st.selectbox("经手人 (🔍搜索)", ["🔍 选择历史经手人"] + hands_list + ["➕ 新增经手人"])
        new_h = st.text_input("✍️ 输入新经手人姓名") if h_sel == "➕ 新增经手人" else ""
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注信息", height=68)

    st.divider()
    if st.button("🚀 提交账目流水", use_container_width=True):
        f_a = new_a if a_sel == "➕ 新增账户" else a_sel
        f_h = new_h if h_sel == "➕ 新增经手人" else h_sel
        f_p = new_p if p_sel == "➕ 新增项目" else (p_sel if "🔍" not in str(p_sel) else "")
        
        # 校验
        if not st.session_state.summary_input or "🔍" in str(f_a) or "🔍" in str(f_h):
            st.error("❌ 必填项缺失：请检查摘要、账户和经手人是否已选择或填写！")
        else:
            final_usd = raw_amt / st.session_state.input_rate if st.session_state.input_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            
            rate_tag = f"【原币：{raw_amt} {currency}，汇率：{st.session_state.input_rate}】"
            today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
            sn_count = len(df_latest[df_latest['录入编号'].astype(str).str.contains(today, na=False)])
            sn = today + f"{sn_count + 1:03d}"
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'),
                "摘要": st.session_state.summary_input, "客户/项目名称": f_p, "账户": f_a, 
                "资金性质": fund_p, "收入": inc_v, "支出": exp_v, "余额": last_bal + inc_v - exp_v, 
                "经手人": f_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.balloons(); st.success(f"✅ 录入成功！流水号：{sn}"); time.sleep(1); st.rerun()

elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总明细")
    if not df_latest.empty:
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
