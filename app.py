import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置与柬埔寨时区 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_local():
    return datetime.now(LOCAL_TZ)

def get_now_str():
    return get_now_local().strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 数据加载 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
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
# --- 优化后的录入逻辑片段 (请替换原代码中的对应部分) ---

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | 柬埔寨时间：{get_now_str()}")

    # 1. 把“录入币种”和“汇率”提出来，放在表单外面，这样 on_change 才能生效
    st.markdown("### 0️⃣ 汇率预设")
    ex_c1, ex_c2 = st.columns(2)
    with ex_c1:
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with ex_c2:
        ex_rate = st.number_input("实时汇率", key="input_rate", format="%.4f")

    # 2. 进入正式表单
    with st.form("entry_form", clear_on_submit=True):
        st.markdown("### 1️⃣ 业务摘要")
        c1, c2 = st.columns([2, 1])
        with c1:
            final_summary = st.text_input("摘要内容", placeholder="请手动输入描述...")
        with c2:
            biz_datetime = st.datetime_input("业务时间 (UTC+7)", value=get_now_local())

        st.markdown("### 2️⃣ 资金与账户")
        cc1, cc2 = st.columns(2)
        with cc1:
            ALL_PROPS = ["期初结存", "内部调拨-转入", "内部调拨-转出", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
            fund_p = st.selectbox("资金性质", ALL_PROPS)
        with cc2:
            raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)

        # 账户选择
        acc_list = get_unique_list(df_latest, "账户")
        a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + acc_list + ["➕ 新增账户"])
        final_acc = st.text_input("✍️ 如果是新账户，请在此输入名称") if a_sel == "➕ 新增账户" else a_sel

        st.markdown("### 3️⃣ 相关方信息")
        hc1, hc2 = st.columns(2)
        with hc1:
            f_p = ""
            PROJECT_TRIGGER = ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]
            if fund_p in PROJECT_TRIGGER:
                p_list = get_unique_list(df_latest, "客户/项目名称")
                p_sel = st.selectbox("项目/客户", ["🔍 选择历史项目"] + p_list + ["➕ 新增项目"])
                f_p = st.text_input("✍️ 输入新项目名") if p_sel == "➕ 新增项目" else (p_sel if "🔍" not in str(p_sel) else "")
        with hc2:
            h_list = get_unique_list(df_latest, "经手人")
            h_sel = st.selectbox("经手人", ["🔍 选择历史人员"] + h_list + ["➕ 新增人员"])
            f_h = st.text_input("✍️ 输入新姓名") if h_sel == "➕ 新增人员" else h_sel

        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注")

        # 必须要有一个这个按钮
        submit_btn = st.form_submit_button("🚀 提交账目流水", use_container_width=True)
    if submit_btn:
        if not final_summary or "🔍" in str(final_acc) or "🔍" in str(f_h):
            st.error("❌ 摘要、账户和经手人不能为空！")
        else:
            final_usd = round(raw_amt / st.session_state.input_rate, 2) if st.session_state.input_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            
            rate_tag = f"【原币：{raw_amt} {currency}，汇率：{st.session_state.input_rate}】"
            today_sn = "R" + get_now_local().strftime("%Y%m%d")
            sn = today_sn + f"{len(df_latest[df_latest['录入编号'].astype(str).str.contains(today_sn, na=False)]) + 1:03d}"
            
            new_bal = round(last_bal + inc_v - exp_v, 2)
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": biz_datetime.strftime('%Y-%m-%d %H:%M'),
                "摘要": final_summary, "客户/项目名称": f_p, "账户": final_acc, "资金性质": fund_p, 
                "收入": inc_v, "支出": exp_v, "余额": new_bal, 
                "经手人": f_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.balloons()
            st.success("✅ 提交成功！页面已重置。")
            st.cache_data.clear()
            time.sleep(1.2)
            st.rerun()

# --- 5. 页面 B：汇总统计 ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    
    if not df_latest.empty:
        # --- A. 当日统计 ---
        today_date = get_now_local().strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str).str.startswith(today_date)]
        t_inc, t_exp = round(df_today["收入"].sum(), 2), round(df_today["支出"].sum(), 2)
        total_bal = round(df_latest["余额"].iloc[-1], 2)
        
        st.markdown(f"### 📅 今日概览 ({today_date})")
        m1, m2, m3 = st.columns(3)
        m1.metric("今日总收入", f"${t_inc:,.2f}")
        m2.metric("今日总支出", f"${t_exp:,.2f}", delta_color="inverse")
        m3.metric("实时总结余 (All)", f"${total_bal:,.2f}")
        
        st.divider()

        # --- B. 账户汇总表 (带合计行) ---
        st.subheader("🏦 本月分账户统计 (USD)")
        this_month = get_now_local().strftime('%Y-%m')
        acc_summary = []
        unique_accs = sorted([x for x in df_latest["账户"].unique() if x])
        for acc in unique_accs:
            df_acc = df_latest[df_latest["账户"] == acc]
            df_before = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
            open_bal = round(df_before["余额"].iloc[-1], 2) if not df_before.empty else 0
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            acc_summary.append({"账户": acc, "期初": open_bal, "收入": df_m["收入"].sum(), "支出": df_m["支出"].sum(), "结余": df_acc["余额"].iloc[-1]})
        
        df_s = pd.DataFrame(acc_summary)
        if not df_s.empty:
            total_row = pd.DataFrame([{"账户": "✨ 总计 (Total)", "期初": df_s["期初"].sum(), "收入": df_s["收入"].sum(), "支出": df_s["支出"].sum(), "结余": df_s["结余"].sum()}])
            st.table(pd.concat([df_s, total_row], ignore_index=True).style.format({"期初": "${:,.2f}", "收入": "${:,.2f}", "支出": "${:,.2f}", "结余": "${:,.2f}"}))

        st.divider()

        # --- C. 数据明细列宽优化 ---
        st.subheader("📑 原始流水明细 (按编号倒序)")
        column_configuration = {
            "录入编号": st.column_config.TextColumn("编号", width="small"),
            "日期": st.column_config.TextColumn("业务时间", width="medium"),
            "摘要": st.column_config.TextColumn("摘要描述", width="large"),
            "收入": st.column_config.NumberColumn("收入 ($)", format="$%.2f", width="small"),
            "支出": st.column_config.NumberColumn("支出 ($)", format="$%.2f", width="small"),
            "余额": st.column_config.NumberColumn("余额 ($)", format="$%.2f", width="small"),
            "经手人": st.column_config.TextColumn("经手人", width="small"),
            "提交时间": None 
        }
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), column_config=column_configuration, use_container_width=True, hide_index=True)

        # --- D. 数据修正模块 (重置逻辑) ---
        st.divider()
        st.subheader("🛠️ 数据修正")
        # 修正表单也放入 expander 并增加重置逻辑
        with st.expander("🔍 展开修正表单", expanded=False):
            # 使用 key 绑定选择框，方便后续重置（虽然 rerun 会重置所有，但规范化更好）
            target_sn = st.selectbox("请选择要修改的【录入编号】", options=["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1])
            
            if target_sn != "-- 请选择 --":
                old = df_latest[df_latest["录入编号"] == target_sn].iloc[0]
                # clear_on_submit 确保修正后表单内容不残留
                with st.form("edit_form", clear_on_submit=True):
                    st.warning(f"正在修正记录：{target_sn}")
                    e1, e2, e3 = st.columns(3)
                    u_sum = e1.text_input("修改摘要", value=str(old["摘要"]))
                    u_inc = e2.number_input("修正收入", value=float(old["收入"]), step=0.01)
                    u_exp = e3.number_input("修正支出", value=float(old["支出"]), step=0.01)
                    
                    if st.form_submit_button("💾 确认并保存更新"):
                        idx = df_latest[df_latest["录入编号"] == target_sn].index[0]
                        df_latest.at[idx, "摘要"] = u_sum
                        df_latest.at[idx, "收入"] = round(u_inc, 2)
                        df_latest.at[idx, "支出"] = round(u_exp, 2)
                        conn.update(worksheet="Summary", data=df_latest)
                        
                        st.balloons() # 撒气球
                        st.success(f"✅ 编号 {target_sn} 已成功修正并重置页面！")
                        st.cache_data.clear()
                        time.sleep(1.2)
                        st.rerun() # 彻底刷新页面，选择框回归默认，表单收起
else:
    st.warning("🔒 权限验证：请输入正确密码访问。")

