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

# --- 2. 汇率逻辑 ---
def get_reference_rate(df_history, currency):
    if currency == "USD": return 1.0
    # 查找本月历史备注中的汇率
    if not df_history.empty and "备注" in df_history.columns:
        this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        df_month = df_history[df_history['日期'].astype(str).str.contains(this_month)]
        for note in df_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    # 备选 API
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
    except: return pd.DataFrame(), ["房租支付", "工资发放"]

df_latest, SHORTCUT_SUMMARIES = load_data()

# --- 4. 汇率联动回调函数 (关键点) ---
def update_rate():
    # 当币种改变时，自动计算新汇率并存入 session_state
    new_curr = st.session_state.my_currency
    st.session_state.my_rate = float(get_reference_rate(df_latest, new_curr))

# 初始化 session_state
if 'my_rate' not in st.session_state:
    st.session_state.my_rate = 1.0

# --- 5. 界面逻辑 ---
role = st.sidebar.radio("功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 账户总结余：**${last_bal:,.2f}** (USD)")

    # 重点：为了实现联动，我们不使用 st.form，而是手动创建布局，最后用一个普通按钮提交
    # 这样可以保证选币种时，汇率框能实时刷新
    
    st.markdown("### 1️⃣ 摘要与日期")
    shortcut = st.radio("⚡ 快捷摘要", ["自定义"] + SHORTCUT_SUMMARIES, horizontal=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        default_s = f"{shortcut} ({datetime.now(LOCAL_TZ).strftime('%m')}月)" if shortcut != "自定义" else ""
        summary = st.text_input("摘要内容 (必填)", value=default_s)
    with c2:
        biz_date = st.date_input("业务日期")

    st.markdown("### 2️⃣ 金额与账户")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        ALL_PROPS = ["期初结存", "内部调拨-转入", "内部调拨-转出", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
        fund_p = st.selectbox("资金性质", ALL_PROPS)
        # 币种选择器：加入 on_change 回调
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="my_currency", on_change=update_rate)
    with cc2:
        raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
        # 汇率输入框：绑定 session_state
        ex_rate = st.number_input("实时汇率", key="my_rate", format="%.4f")
    with cc3:
        accs = sorted([str(x) for x in df_latest["账户"].unique() if x and str(x)!='nan'])
        a_sel = st.selectbox("结算账户", ["🔍 选择历史"] + accs + ["➕ 新增"])
        new_a = st.text_input("新账户名")

    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        projs = sorted([str(x) for x in df_latest["客户/项目名称"].unique() if x and str(x)!='nan'])
        p_sel = st.selectbox("客户/项目", ["🔍 选择历史"] + projs + ["➕ 新增项目"])
        new_p = st.text_input("新项目名")
    with hc2:
        hands = sorted([str(x) for x in df_latest["经手人"].unique() if x and str(x)!='nan'])
        h_sel = st.selectbox("经手人", ["🔍 选择历史"] + hands + ["➕ 新增经手人"])
        new_h = st.text_input("新姓名")
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注信息")

    if st.button("🚀 确认提交录入", use_container_width=True):
        final_a = new_a if a_sel == "➕ 新增" else a_sel
        final_h = new_h if h_sel == "➕ 新增经手人" else h_sel
        final_p = (new_p if p_sel == "➕ 新增项目" else p_sel) if "选择" not in str(p_sel) else ""
        
        if not summary or "选择" in str(final_a) or "选择" in str(final_h):
            st.error("❌ 摘要、账户和经手人不能为空")
        else:
            final_usd = raw_amt / st.session_state.my_rate if st.session_state.my_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_val, exp_val = (final_usd, 0) if is_inc else (0, final_usd)
            
            rate_tag = f"【原币：{raw_amt} {st.session_state.my_currency}，汇率：{st.session_state.my_rate}】"
            today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
            sn = today + f"{len(df_latest[df_latest['录入编号'].str.contains(today, na=False)]) + 1:03d}"
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'),
                "摘要": summary, "客户/项目名称": final_p, "账户": final_a, "资金性质": fund_p,
                "收入": inc_val, "支出": exp_val, "余额": last_bal + inc_val - exp_val, 
                "经手人": final_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no
            }
            new_df = pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True)
            conn.update(worksheet="Summary", data=new_df)
            st.balloons(); st.success("✅ 录入成功！"); time.sleep(1); st.rerun()

elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计与维护")
    if not df_latest.empty:
        for c in ["收入", "支出", "余额"]: df_latest[c] = pd.to_numeric(df_latest[c], errors='coerce').fillna(0)
        m1, m2, m3 = st.columns(3)
        m1.metric("总结余 (USD)", f"${df_latest['余额'].iloc[-1]:,.2f}")
        m2.metric("总收入", f"${df_latest['收入'].sum():,.2f}")
        m3.metric("总支出", f"${df_latest['支出'].sum():,.2f}")
        st.divider()
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
