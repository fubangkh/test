import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 (严禁改动) ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 核心数据函数 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        # 强制转换数值列，防止对比或计算报错
        for c in ["收入", "支出", "余额"]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

def handle_currency_change():
    new_curr = st.session_state.sel_curr
    st.session_state.input_rate = float(get_reference_rate(df_latest, new_curr))

def get_reference_rate(df_history, currency):
    if currency == "USD": return 1.0
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1)
        if res.status_code == 200:
            api = res.json().get("rates", {})
            rates = {"RMB": api.get("CNY", 7.23), "VND": api.get("VND", 25450.0), "HKD": api.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan'])

df_latest = load_all_data()
if 'input_rate' not in st.session_state: st.session_state.input_rate = 1.0

# --- 3. 界面侧边栏 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

# --- 4. 页面 A：数据录入 ---
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | {get_now_str()}")

    st.markdown("### 1️⃣ 业务摘要")
    c1, c2 = st.columns([3, 1])
    with c1:
        final_summary = st.text_input("摘要内容", placeholder="请手动输入本笔业务描述...")
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
    with cc3:
        acc_list = get_unique_list(df_latest, "账户")
        a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + acc_list + ["➕ 新增账户"])
        final_acc = st.text_input("✍️ 输入新账户") if a_sel == "➕ 新增账户" else a_sel

    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        f_p = ""
        PROJECT_TRIGGER = ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]
        if fund_p in PROJECT_TRIGGER:
            p_list = get_unique_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("项目/客户", ["🔍 选择历史项目"] + p_list + ["➕ 新增项目"])
            f_p = st.text_input("✍️ 输入新项目") if p_sel == "➕ 新增项目" else (p_sel if "🔍" not in str(p_sel) else "")
        else:
            st.write("ℹ️ 此性质无需填写项目")
    with hc2:
        h_list = get_unique_list(df_latest, "经手人")
        h_sel = st.selectbox("经手人", ["🔍 选择历史人员"] + h_list + ["➕ 新增人员"])
        f_h = st.text_input("✍️ 输入新姓名") if h_sel == "➕ 新增人员" else h_sel
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注", height=68)

    if st.button("🚀 提交账目流水", use_container_width=True):
        if not final_summary or "🔍" in str(final_acc) or "🔍" in str(f_h):
            st.error("❌ 摘要、账户和经手人不能为空！")
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

# --- 5. 页面 B：汇总统计与修正 ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 账户汇总与管理")
    
    if not df_latest.empty:
        # 1. 顶部统计
        st.subheader("🏦 账户本月收支汇总")
        this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        summary_list = []
        for acc in get_unique_list(df_latest, "账户"):
            df_acc = df_latest[df_latest["账户"] == acc]
            df_before = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
            open_bal = df_before["余额"].iloc[-1] if not df_before.empty else 0
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            summary_list.append({"账户": acc, "期初": open_bal, "月收入": df_m["收入"].sum(), "月支出": df_m["支出"].sum(), "实时结余": df_acc["余额"].iloc[-1]})
        st.table(pd.DataFrame(summary_list))

        st.divider()
        
        # 2. 修正模块 (无需新插件的稳健方案)
        st.subheader("🛠️ 数据修正中心")
        with st.expander("🔍 点击此处，输入编号修改错误账目"):
            all_sn = df_latest["录入编号"].tolist()[::-1]
            target_sn = st.selectbox("请选择要修改的【录入编号】", options=["-- 请选择 --"] + all_sn)
            
            if target_sn != "-- 请选择 --":
                old_row = df_latest[df_latest["录入编号"] == target_sn].iloc[0]
                st.info(f"正在编辑记录：{target_sn}")
                with st.form("edit_form"):
                    col1, col2, col3 = st.columns(3)
                    u_sum = col1.text_input("摘要", value=str(old_row["摘要"]))
                    u_inc = col2.number_input("收入($)", value=float(old_row["收入"]))
                    u_exp = col3.number_input("支出($)", value=float(old_row["支出"]))
                    u_note = st.text_area("备注", value=str(old_row["备注"]))
                    
                    if st.form_submit_button("💾 保存并更新 Google 表格"):
                        idx = df_latest[df_latest["录入编号"] == target_sn].index[0]
                        df_latest.at[idx, "摘要"] = u_sum
                        df_latest.at[idx, "收入"] = u_inc
                        df_latest.at[idx, "支出"] = u_exp
                        df_latest.at[idx, "备注"] = u_note
                        conn.update(worksheet="Summary", data=df_latest)
                        st.success(f"编号 {target_sn} 已更新！"); st.cache_data.clear(); time.sleep(1); st.rerun()

        st.divider()
        # 3. 原始明细
        st.subheader("📑 原始流水明细")
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ 请在侧边栏输入密码访问")

