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

# --- 2. 汇率获取函数 (精准逻辑) ---
def get_reference_rate(df_history, currency):
    if currency == "USD": return 1.0
    # A. 查找历史备注
    if not df_history.empty and "备注" in df_history.columns:
        this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        df_month = df_history[df_history['日期'].astype(str).str.contains(this_month)]
        for note in df_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    # B. API 获取
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
def load_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        df_cfg = conn.read(worksheet="Config", ttl=0).dropna(how="all")
        shortcuts = df_cfg["快捷摘要"].dropna().tolist()
        return df, shortcuts
    except: return pd.DataFrame(), ["房租", "工资"]

df_latest, SHORTCUT_SUMMARIES = load_data()

# --- 4. 界面逻辑 ---
role = st.sidebar.radio("功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    
    # --- 核心改进：把币种选择放在表单外面，或者作为独立组件以触发刷新 ---
    st.subheader("1️⃣ 币种与汇率设置")
    col_curr, col_rate = st.columns(2)
    with col_curr:
        # 移出 form 或使用 session_state 确保联动
        currency = st.selectbox("选择录入币种", ["USD", "RMB", "VND", "HKD"], key="curr_selector")
    with col_rate:
        # 这里的汇率会随 currency 的改变而实时计算
        suggested_rate = get_reference_rate(df_latest, currency)
        ex_rate = st.number_input("确认实时汇率", value=float(suggested_rate), format="%.4f", key="rate_input")

    with st.form("main_entry_form"):
        st.subheader("2️⃣ 摘要与日期")
        shortcut = st.radio("⚡ 快捷摘要", ["自定义"] + SHORTCUT_SUMMARIES, horizontal=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            default_s = f"{shortcut} ({datetime.now(LOCAL_TZ).strftime('%m')}月)" if shortcut != "自定义" else ""
            summary = st.text_input("摘要内容", value=default_s)
        with c2:
            biz_date = st.date_input("业务日期")

        st.subheader("3️⃣ 金额与账户")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            INC_PROPS = ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            EXP_PROPS = ["内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
            fund_p = st.selectbox("资金性质", INC_PROPS + EXP_PROPS)
        with cc2:
            raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
        with cc3:
            accs = sorted([str(x) for x in df_latest["账户"].unique() if x and str(x)!='nan'])
            a_sel = st.selectbox("结算账户", ["🔍 选择"] + accs + ["➕ 新增"])
            new_a = st.text_input("新账户名")

        st.subheader("4️⃣ 相关方")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            projs = sorted([str(x) for x in df_latest["客户/项目名称"].unique() if x and str(x)!='nan'])
            p_sel = st.selectbox("项目", ["🔍 选择"] + projs + ["➕ 新增"])
            new_p = st.text_input("新项目")
        with hc2:
            hands = sorted([str(x) for x in df_latest["经手人"].unique() if x and str(x)!='nan'])
            h_sel = st.selectbox("经手人", ["🔍 选择"] + hands + ["➕ 新增"])
            new_h = st.text_input("新经手人")
        with hc3:
            ref_no = st.text_input("凭证/审批编号")
            note = st.text_area("备注信息")

        if st.form_submit_button("🚀 提交录入", use_container_width=True):
            # 获取外部组件的值
            current_currency = st.session_state.curr_selector
            current_rate = st.session_state.rate_input
            
            final_a = new_a if a_sel == "➕ 新增" else a_sel
            final_h = new_h if h_sel == "➕ 新增" else h_sel
            final_p = (new_p if p_sel == "➕ 新增" else p_sel) if "选择" not in str(p_sel) else ""
            
            if not summary or "选择" in str(final_a) or "选择" in str(final_h):
                st.error("❌ 必填项缺失")
            else:
                usd = raw_amt / current_rate if current_rate > 0 else 0
                inc = usd if fund_p in INC_PROPS else 0
                exp = usd if fund_p in EXP_PROPS else 0
                rate_note = f"【原币：{raw_amt} {current_currency}，汇率：{current_rate}】"
                
                today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
                sn = today + f"{len(df_latest[df_latest['录入编号'].str.contains(today, na=False)]) + 1:03d}"
                
                row = {
                    "录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'),
                    "摘要": summary, "客户/项目名称": final_p, "账户": final_a, "资金性质": fund_p,
                    "收入": inc, "支出": exp, "余额": last_bal + inc - exp, "经手人": final_h, 
                    "备注": f"{note} {rate_note}", "审批/发票编号": ref_no
                }
                new_df = pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True)
                conn.update(worksheet="Summary", data=new_df)
                st.success("录入成功！"); time.sleep(1); st.rerun()

# 汇总统计逻辑 (保持不变，确保显示)
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计明细")
    if not df_latest.empty:
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True)
