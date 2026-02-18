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

# --- 2. 核心函数 ---
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

@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df_latest = load_all_data()

if 'input_rate' not in st.session_state: st.session_state.input_rate = 1.0

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and str(x).strip() != ""])

# --- 3. 界面逻辑 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

# --- 页面 A：数据录入 ---
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | {get_now_str()}")
    
    st.markdown("### 1️⃣ 业务摘要")
    c1, c2 = st.columns([3, 1])
    with c1:
        final_summary = st.text_input("摘要内容", placeholder="请在此录入业务摘要...")
    with c2:
        biz_date = st.date_input("业务日期", value=datetime.now(LOCAL_TZ))

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
        a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + accs_list + ["➕ 新增账户"])
        final_acc = st.text_input("✍️ 输入新账户名") if a_sel == "➕ 新增账户" else a_sel

    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        f_p = ""
        PROJECT_TRIGGER_LIST = ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]
        if fund_p in PROJECT_TRIGGER_LIST:
            projs_list = get_unique_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("项目/客户", ["🔍 选择历史项目"] + projs_list + ["➕ 新增项目"])
            f_p = st.text_input("✍️ 输入新项目名") if p_sel == "➕ 新增项目" else (p_sel if "🔍" not in str(p_sel) else "")
        else:
            st.write("ℹ️ 无需项目信息")
    with hc2:
        hands_list = get_unique_list(df_latest, "经手人")
        h_sel = st.selectbox("经手人", ["🔍 选择历史经手人"] + hands_list + ["➕ 新增经手人"])
        f_h = st.text_input("✍️ 输入经手人姓名") if h_sel == "➕ 新增经手人" else h_sel
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注信息", height=68)

    if st.button("🚀 提交账目流水", use_container_width=True):
        if not final_summary or "🔍" in str(final_acc) or "🔍" in str(f_h):
            st.error("❌ 必填项缺失！")
        else:
            final_usd = raw_amt / st.session_state.input_rate if st.session_state.input_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            rate_tag = f"【原币：{raw_amt} {currency}，汇率：{st.session_state.input_rate}】"
            today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
            sn = today + f"{len(df_latest[df_latest['录入编号'].astype(str).str.contains(today, na=False)]) + 1:03d}"
            row = {"录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'), "摘要": final_summary, "客户/项目名称": f_p, "账户": final_acc, "资金性质": fund_p, "收入": inc_v, "支出": exp_v, "余额": last_bal + inc_v - exp_v, "经手人": f_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no}
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.cache_data.clear(); st.balloons(); st.success("✅ 提交成功！"); time.sleep(1); st.rerun()

# --- 页面 B：汇总统计与修改 ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 账户汇总与数据管理")
    
    if not df_latest.empty:
        # 1. 账户汇总逻辑
        st.subheader("🏦 账户收支月报")
        this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        acc_summary = []
        for acc in get_unique_list(df_latest, "账户"):
            df_acc = df_latest[df_latest["账户"] == acc]
            df_before = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
            open_bal = df_before["余额"].iloc[-1] if not df_before.empty else 0
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            acc_summary.append({"账户": acc, "期初": open_bal, "本月收入": df_m["收入"].sum(), "本月支出": df_m["支出"].sum(), "结余": df_acc["余额"].iloc[-1]})
        st.table(pd.DataFrame(acc_summary))

        st.divider()
        
        # 2. 修改功能 (使用单选逻辑)
        st.subheader("🛠️ 账目明细修改")
        st.write("请在下方列表中记下编号，在下拉框中选择进行修改：")
        
        # 为了方便操作，提供一个带搜索的选择框
        target_sn = st.selectbox("🔍 选择需要修改的录入编号", options=["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1])
        
        if target_sn != "-- 请选择 --":
            old_data = df_latest[df_latest["录入编号"] == target_sn].iloc[0]
            with st.expander(f"📝 正在编辑记录：{target_sn}", expanded=True):
                with st.form("edit_form"):
                    e_col1, e_col2, e_col3 = st.columns(3)
                    new_s = e_col1.text_input("摘要", value=old_data["摘要"])
                    new_i = e_col2.number_input("收入", value=float(old_data["收入"]))
                    new_e = e_col3.number_input("支出", value=float(old_data["支出"]))
                    new_n = st.text_area("备注", value=old_data["备注"])
                    
                    if st.form_submit_button("💾 保存并更新全表"):
                        idx = df_latest[df_latest["录入编号"] == target_sn].index[0]
                        df_latest.at[idx, "摘要"] = new_s
                        df_latest.at[idx, "收入"] = new_i
                        df_latest.at[idx, "支出"] = new_e
                        df_latest.at[idx, "备注"] = new_n
                        # 注意：此处不自动重算余额，防止破坏历史逻辑
                        conn.update(worksheet="Summary", data=df_latest)
                        st.success("数据已更新！")
                        st.cache_data.clear(); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("📑 原始流水清单")
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ 请在侧边栏输入正确密码以访问系统")
