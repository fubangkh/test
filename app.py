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

# --- 2. 核心数据函数 ---
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
    """实时切换汇率逻辑"""
    st.session_state.input_rate = float(get_reference_rate(st.session_state.sel_curr))

def get_reference_rate(currency):
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
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and "🔍" not in str(x)])

# 初始化数据
df_latest = load_all_data()
if 'input_rate' not in st.session_state: 
    st.session_state.input_rate = 1.0

# --- 3. 界面逻辑 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

# --- 4. 页面 A：数据录入 (实时联动增强版) ---
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | 柬埔寨时间：{get_now_str()}")

    # --- 实时联动区 (不在 Form 内) ---
    st.markdown("### 1️⃣ 业务基础与金额")
    r1_c1, r1_c2 = st.columns([2, 1])
    with r1_c1:
        val_summary = st.text_input("摘要内容", placeholder="请手动输入描述...", key="ui_summary")
    with r1_c2:
        val_biz_time = st.datetime_input("业务时间 (UTC+7)", value=get_now_local())

    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        val_raw_amt = st.number_input("录入金额", min_value=0.0, step=0.01, key="ui_raw_amt")
    with r2_c2:
        val_curr = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with r2_c3:
        val_rate = st.number_input("记账汇率", key="input_rate", format="%.4f")

    # 资金性质 (移出 Form)
    ALL_PROPS = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "期初结存", "内部调拨-转入", "内部调拨-转出", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    val_prop = st.selectbox("资金性质", ALL_PROPS, key="ui_prop")

    # 核心联动：性质触发项目信息
    val_project = ""
    PROJECT_TRIGGER = ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]
    if val_prop in PROJECT_TRIGGER:
        st.info("🔎 检测到收入/成本类科目，请完善项目信息：")
        pc1, pc2 = st.columns(2)
        with pc1:
            p_list = get_unique_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("选择历史项目/客户", ["🔍 请选择"] + p_list + ["➕ 新增项目"], key="ui_p_sel")
        with pc2:
            if p_sel == "➕ 新增项目":
                val_project = st.text_input("✍️ 输入新项目名称", key="ui_p_new")
            else:
                val_project = p_sel if p_sel != "🔍 请选择" else ""

    val_est_usd = round(val_raw_amt / val_rate, 2) if val_rate > 0 else 0.0
    st.success(f"📊 **当前换算金额预估：${val_est_usd:,.2f} USD**")

    # --- 结算与提交区 (在 Form 内) ---
    with st.form("remaining_info_form", clear_on_submit=True):
        st.markdown("### 2️⃣ 结算与备注")
        f1, f2 = st.columns(2)
        with f1:
            acc_list = get_unique_list(df_latest, "账户")
            a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + acc_list + ["➕ 新增账户"])
            val_acc = st.text_input("✍️ 输入新账户名称") if a_sel == "➕ 新增账户" else a_sel
        with f2:
            h_list = get_unique_list(df_latest, "经手人")
            h_sel = st.selectbox("经手人", ["🔍 选择历史人员"] + h_list + ["➕ 新增人员"])
            val_handler = st.text_input("✍️ 输入新姓名") if h_sel == "➕ 新增人员" else h_sel

        val_ref = st.text_input("审批/发票编号")
        val_note = st.text_area("备注详情")

        submit_btn = st.form_submit_button("🚀 确认提交账目流水", use_container_width=True)

    if submit_btn:
        if not val_summary or not val_acc or "🔍" in str(val_acc) or not val_handler or "🔍" in str(val_handler):
            st.error("❌ 摘要、账户和经手人不能为空！")
        elif val_prop in PROJECT_TRIGGER and not val_project:
            st.error("❌ 此类资金性质必须填写【项目名称】！")
        else:
            final_usd = round(val_raw_amt / val_rate, 2)
            is_inc = val_prop in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            
            tag = f"【原币：{val_raw_amt} {val_curr}，汇率：{val_rate}】"
            today_sn = "R" + get_now_local().strftime("%Y%m%d")
            sn = today_sn + f"{len(df_latest[df_latest['录入编号'].astype(str).str.contains(today_sn, na=False)]) + 1:03d}"
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": val_biz_time.strftime('%Y-%m-%d %H:%M'),
                "摘要": val_summary, "客户/项目名称": val_project, "账户": val_acc, "资金性质": val_prop, 
                "收入": inc_v, "支出": exp_v, "余额": round(last_bal + inc_v - exp_v, 2), 
                "经手人": val_handler, "备注": f"{val_note} {tag}", "审批/发票编号": val_ref
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.balloons()
            st.success("✅ 提交成功！")
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# --- 5. 页面 B：汇总统计 ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    if not df_latest.empty:
        # 当日快报
        today_date = get_now_local().strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str).str.startswith(today_date)]
        st.markdown(f"### 📅 今日收支概览 ({today_date})")
        m1, m2, m3 = st.columns(3)
        m1.metric("今日总收入", f"${df_today['收入'].sum():,.2f}")
        m2.metric("今日总支出", f"${df_today['支出'].sum():,.2f}", delta_color="inverse")
        m3.metric("当前实时总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        
        st.divider()
        # 月度账户表 (含合计行)
        this_month = get_now_local().strftime('%Y-%m')
        st.subheader(f"🏦 {this_month} 分账户统计 (USD)")
        acc_summary = []
        for acc in sorted(df_latest["账户"].unique()):
            if not acc: continue
            df_acc = df_latest[df_latest["账户"] == acc]
            # 计算期初 (本月1号之前)
            df_pre = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
            open_bal = round(df_pre["余额"].iloc[-1], 2) if not df_pre.empty else 0
            # 本月发生
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            acc_summary.append({"账户名称": acc, "期初余额": open_bal, "本月收入": df_m["收入"].sum(), "本月支出": df_m["支出"].sum(), "实时结余": df_acc["余额"].iloc[-1]})
        
        df_s = pd.DataFrame(acc_summary)
        if not df_s.empty:
            total_row = pd.DataFrame([{
                "账户名称": "✨ 总计 (Total)", "期初余额": df_s["期初余额"].sum(), 
                "本月收入": df_s["本月收入"].sum(), "本月支出": df_s["本月支出"].sum(), "实时结余": df_s["实时结余"].sum()
            }])
            st.table(pd.concat([df_s, total_row], ignore_index=True).style.format({"期初余额": "${:,.2f}", "本月收入": "${:,.2f}", "本月支出": "${:,.2f}", "实时结余": "${:,.2f}"}))

        st.divider()
        # 流水明细 (优化列宽显示)
        st.subheader("📑 原始流水明细")
        st.dataframe(
            df_latest.sort_values("录入编号", ascending=False), 
            hide_index=True, 
            use_container_width=True, 
            column_config={
                "提交时间": None, 
                "摘要": st.column_config.TextColumn("摘要", width="large"),
                "收入": st.column_config.NumberColumn(format="$%.2f"), 
                "支出": st.column_config.NumberColumn(format="$%.2f"), 
                "余额": st.column_config.NumberColumn(format="$%.2f")
            }
        )

        # 修正模块
        with st.expander("🛠️ 账目快速修正"):
            target = st.selectbox("请选择要修改的【录入编号】", ["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1], key="edit_select")
            if target != "-- 请选择 --":
                old = df_latest[df_latest["录入编号"] == target].iloc[0]
                with st.form("edit_form", clear_on_submit=True):
                    u_sum = st.text_input("修正摘要", value=old["摘要"])
                    u_inc = st.number_input("修正收入", value=float(old["收入"]))
                    u_exp = st.number_input("修正支出", value=float(old["支出"]))
                    if st.form_submit_button("💾 保存更新并重置"):
                        idx = df_latest[df_latest["录入编号"] == target].index[0]
                        df_latest.at[idx, "摘要"], df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = u_sum, round(u_inc, 2), round(u_exp, 2)
                        conn.update(worksheet="Summary", data=df_latest)
                        st.balloons(); st.success("更新成功！"); st.cache_data.clear(); time.sleep(1); st.rerun()
else:
    st.warning("🔒 权限验证：请输入正确密码。")
