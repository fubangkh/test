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

# --- 2. 核心逻辑 (汇率与联想) ---
def handle_currency_change():
    new_curr = st.session_state.sel_curr
    st.session_state.input_rate = float(get_reference_rate(df_latest, new_curr))

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

# --- 3. 数据加载 (带强力列名容错) ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # 补全缺失列名，防止 KeyError
        cols = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "备注", "审批/发票编号"]
        for c in cols:
            if c not in df.columns: df[c] = ""
            
        history_summaries = sorted([str(x) for x in df["摘要"].unique() if x and str(x)!='nan'])
        return df, history_summaries
    except:
        return pd.DataFrame(), []

df_latest, SUMMARY_HISTORY = load_all_data()

# 初始化汇率状态
if 'input_rate' not in st.session_state: st.session_state.input_rate = 1.0

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and str(x).strip() != ""])

# --- 4. 界面展示 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 智能财务录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | {get_now_str()}")
    
    # --- 模块 1：业务摘要 ---
    st.markdown("### 1️⃣ 业务摘要")
    c1, c2 = st.columns([3, 1])
    with c1:
        final_summary = st.selectbox(
            "摘要内容",
            options=SUMMARY_HISTORY,
            index=None,
            placeholder="打字搜索历史或直接输入新内容...",
            label_visibility="collapsed"
        )
    with c2:
        biz_date = st.date_input("业务日期", value=datetime.now(LOCAL_TZ), label_visibility="collapsed")

    # --- 模块 2：金额与结算 ---
    st.markdown("### 2️⃣ 金额与结算")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        ALL_PROPS = ["期初结存", "内部调拨-转入", "内部调拨-转出", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
        fund_p = st.selectbox("资金性质", ALL_PROPS)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with cc2:
        raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
        ex_rate = st.number_input("实时汇率", key="input_rate", format="%.4f")
        if ex_rate > 0 and currency != "USD":
            st.metric("📊 换算美元", f"${(raw_amt/ex_rate):,.2f}")
    with cc3:
        accs_list = get_unique_list(df_latest, "账户")
        final_acc = st.selectbox(
            "结算账户",
            options=accs_list,
            index=None,
            placeholder="搜索历史账户或输入新账户..."
        )

    # --- 模块 3：相关方信息 (二合一重构) ---
    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        # 客户/项目名称二合一
        projs_list = get_unique_list(df_latest, "客户/项目名称")
        f_p = st.selectbox(
            "项目/客户 (搜索或输入)",
            options=projs_list,
            index=None,
            placeholder="搜索或输入新项目..."
        )
    with hc2:
        # 经手人二合一
        hands_list = get_unique_list(df_latest, "经手人")
        f_h = st.selectbox(
            "经手人 (搜索或输入)",
            options=hands_list,
            index=None,
            placeholder="搜索或输入新经手人..."
        )
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注信息", height=68)

    st.divider()
    if st.button("🚀 提交账目流水", use_container_width=True):
        if not final_summary or not final_acc or not f_h:
            st.error("❌ 必填项缺失：请检查摘要、结算账户和经手人！")
        else:
            final_usd = raw_amt / st.session_state.input_rate if st.session_state.input_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            
            rate_tag = f"【原币：{raw_amt} {currency}，汇率：{st.session_state.input_rate}】"
            today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
            sn = today + f"{len(df_latest[df_latest['录入编号'].astype(str).str.contains(today, na=False)]) + 1:03d}"
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'),
                "摘要": final_summary, "客户/项目名称": f_p if f_p else "", "账户": final_acc, 
                "资金性质": fund_p, "收入": inc_v, "支出": exp_v, "余额": last_bal + inc_v - exp_v, 
                "经手人": f_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.cache_data.clear() 
            st.balloons(); st.success(f"✅ 录入成功！"); time.sleep(1); st.rerun()

elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计")
    if not df_latest.empty:
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
