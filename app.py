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

# --- 2. 状态初始化 ---
if "form_iteration" not in st.session_state:
    st.session_state.form_iteration = 0
if "edit_iteration" not in st.session_state:
    st.session_state.edit_iteration = 0 

# --- 3. 核心函数 ---
@st.cache_data(ttl=1)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
        if "修正时间" not in df.columns:
            df["修正时间"] = ""
        return df
    except:
        return pd.DataFrame()

def handle_currency_change():
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

df_latest = load_all_data()
if 'input_rate' not in st.session_state: 
    st.session_state.input_rate = 1.0

# --- 4. 界面逻辑 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

# --- 5. 页面 A：数据录入 (代码完全锁定，未做任何修改) ---
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | 柬埔寨时间：{get_now_str()}")

    itr = st.session_state.form_iteration
    st.markdown("### 1️⃣ 业务基础")
    r1_c1, r1_c2 = st.columns([2, 1])
    with r1_c1:
        val_summary = st.text_input("摘要内容", placeholder="例如：支付2月租金", key=f"sum_{itr}")
    with r1_c2:
        val_biz_time = st.datetime_input("业务时间 (UTC+7)", value=get_now_local(), key=f"time_{itr}")

    st.markdown("### 2️⃣ 金额与结算账户")
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        val_raw_amt = st.number_input("录入金额", min_value=0.0, step=0.01, key=f"raw_{itr}")
    with r2_c2:
        val_curr = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with r2_c3:
        val_rate = st.number_input("记账汇率", key="input_rate", format="%.4f")
    
    acc_list = get_unique_list(df_latest, "账户")
    r3_c1, r3_c2 = st.columns([1, 1])
    with r3_c1:
        a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + acc_list + ["➕ 新增账户"], key=f"asel_{itr}")
        val_acc = st.text_input("✍️ 输入新账户名称", key=f"accnew_{itr}") if a_sel == "➕ 新增账户" else a_sel
    with r3_c2:
        val_est_usd = round(val_raw_amt / val_rate, 2) if val_rate > 0 else 0.0
        st.markdown(f"<br><p style='font-size:20px; color:#008000;'><b>当前金额预估：${val_est_usd:,.2f} USD</b></p>", unsafe_allow_html=True)

    st.markdown("### 3️⃣ 资金性质与归属")
    ALL_PROPS = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "期初结存", "内部调拨-转入", "内部调拨-转出", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    val_prop = st.selectbox("资金性质", ALL_PROPS, key=f"prop_{itr}")

    val_project = ""
    PROJECT_TRIGGER = ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]
    if val_prop in PROJECT_TRIGGER:
        st.info("🔎 需关联项目/客户信息：")
        pc1, pc2 = st.columns(2)
        with pc1:
            p_list = get_unique_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("选择历史项目/客户", ["🔍 请选择"] + p_list + ["➕ 新增项目"], key=f"psel_{itr}")
        with pc2:
            if p_sel == "➕ 新增项目":
                val_project = st.text_input("✍️ 输入新项目名称", key=f"pnew_{itr}")
            else:
                val_project = p_sel if p_sel != "🔍 请选择" else ""

    with st.form(f"submit_form_{itr}", clear_on_submit=True):
        st.markdown("### 4️⃣ 经手人与备注")
        f1, f2 = st.columns(2)
        with f1:
            h_list = get_unique_list(df_latest, "经手人")
            h_sel = st.selectbox("经手人", ["🔍 选择历史人员"] + h_list + ["➕ 新增人员"])
            val_handler = st.text_input("✍️ 输入经手人姓名") if h_sel == "➕ 新增人员" else h_sel
        with f2:
            val_ref = st.text_input("审批/发票编号")
        val_note = st.text_area("备注详情")
        submit_btn = st.form_submit_button("🚀 确认提交账目流水", use_container_width=True)

    if submit_btn:
        if not val_summary or not val_acc or "🔍" in str(val_acc) or not val_handler or "🔍" in str(val_handler):
            st.error("❌ 请检查：摘要、账户、经手人均不能为空！")
        elif val_prop in PROJECT_TRIGGER and not val_project:
            st.error("❌ 当前资金性质需要选择或输入【项目名称】！")
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
                "经手人": val_handler, "备注": f"{val_note} {tag}", "审批/发票编号": val_ref, "修正时间": ""
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.session_state.form_iteration += 1
            st.balloons()
            st.success("✅ 提交成功！")
            st.cache_data.clear()
            time.sleep(1.2)
            st.rerun()

# --- 6. 页面 B：汇总统计 (已将“放弃并返回”移至底部并更名) ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    if not df_latest.empty:
        # 今日统计
        today_date = get_now_local().strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str).str.startswith(today_date)]
        st.markdown(f"### 📅 今日快报 ({today_date})")
        m1, m2, m3 = st.columns(3)
        m1.metric("今日收入合计", f"${df_today['收入'].sum():,.2f}")
        m2.metric("今日支出合计", f"${df_today['支出'].sum():,.2f}", delta_color="inverse")
        m3.metric("当前总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")
        
        st.divider()
        st.subheader("🏦 分账户统计 (本月)")
        this_month = get_now_local().strftime('%Y-%m')
        acc_summary = []
        for acc in sorted(df_latest["账户"].unique()):
            if not acc: continue
            df_acc = df_latest[df_latest["账户"] == acc]
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            acc_summary.append({"账户": acc, "月收入": df_m["收入"].sum(), "月支出": df_m["支出"].sum(), "结余": df_acc["余额"].iloc[-1]})
        
        df_s = pd.DataFrame(acc_summary)
        if not df_s.empty:
            st.table(df_s.style.format({"月收入": "${:,.2f}", "月支出": "${:,.2f}", "结余": "${:,.2f}"}))

        st.divider()
        st.subheader("📑 原始流水明细")
        display_cols = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "修正时间", "备注", "审批/发票编号"]
        st.dataframe(
            df_latest.sort_values("录入编号", ascending=False), 
            hide_index=True, 
            use_container_width=True,
            column_order=display_cols,
            column_config={
                "提交时间": None, 
                "日期": st.column_config.TextColumn("日期", width="medium"),
                "摘要": st.column_config.TextColumn("摘要", width="large"),
                "收入": st.column_config.NumberColumn(format="$%.2f"), 
                "支出": st.column_config.NumberColumn(format="$%.2f"), 
                "余额": st.column_config.NumberColumn(format="$%.2f"),
                "修正时间": st.column_config.TextColumn("最后修正", width="medium")
            }
        )
        
        st.divider()
        st.subheader("🛠️ 全字段数据修正")
        e_itr = st.session_state.edit_iteration
        
        # 第一步：仅保留编号选择框
        target = st.selectbox("第一步：选择要修改的录入编号", ["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1], key=f"edit_target_{e_itr}")
        
        if target != "-- 请选择 --":
            old_data = df_latest[df_latest["录入编号"] == target].iloc[0]
            # 修正表单
            with st.form(f"full_edit_form_{e_itr}_{target}"):
                st.write(f"📂 正在深度修正编号：**{target}**")
                fe_c1, fe_c2 = st.columns(2)
                with fe_c1:
                    u_date = st.text_input("日期 (YYYY-MM-DD HH:mm)", value=str(old_data["日期"]))
                    u_sum = st.text_input("摘要内容", value=str(old_data["摘要"]))
                    u_proj = st.text_input("客户/项目名称", value=str(old_data["客户/项目名称"]))
                    u_acc = st.text_input("结算账户", value=str(old_data["账户"]))
                    props_list = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "期初结存", "内部调拨-转入", "内部调拨-转出", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
                    u_prop = st.selectbox("资金性质", props_list, index=props_list.index(old_data["资金性质"]) if old_data["资金性质"] in props_list else 0)
                
                with fe_c2:
                    u_inc = st.number_input("收入 (USD)", value=float(old_data["收入"]), step=0.01)
                    u_exp = st.number_input("支出 (USD)", value=float(old_data["支出"]), step=0.01)
                    u_hand = st.text_input("经手人", value=str(old_data["经手人"]))
                    u_ref = st.text_input("审批/发票编号", value=str(old_data["审批/发票编号"]))
                    u_note = st.text_area("备注详情", value=str(old_data["备注"]))

                st.warning("⚠️ 提示：保存后余额将重新计算，并自动盖上修正时间戳。")
                
                # 修改点：将保存按钮和放弃按钮在表单底部并排
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    save_clicked = st.form_submit_button("💾 确认保存全字段修正", use_container_width=True)
                with btn_c2:
                    # 注意：在 st.form 内部，只能有一个真正的 submit_button，
                    # 另一个必须通过 form 外的逻辑或逻辑分支实现。
                    # 这里我们使用一个特殊的 submit_button 作为“放弃”动作
                    cancel_clicked = st.form_submit_button("❌ 放弃并返回", use_container_width=True)

                if save_clicked:
                    idx = df_latest[df_latest["录入编号"] == target].index[0]
                    df_latest.at[idx, "日期"] = u_date
                    df_latest.at[idx, "摘要"] = u_sum
                    df_latest.at[idx, "客户/项目名称"] = u_proj
                    df_latest.at[idx, "账户"] = u_acc
                    df_latest.at[idx, "资金性质"] = u_prop
                    df_latest.at[idx, "收入"] = round(u_inc, 2)
                    df_latest.at[idx, "支出"] = round(u_exp, 2)
                    df_latest.at[idx, "经手人"] = u_hand
                    df_latest.at[idx, "审批/发票编号"] = u_ref
                    df_latest.at[idx, "备注"] = u_note
                    df_latest.at[idx, "修正时间"] = get_now_str()
                    
                    # 自动重算整表余额
                    temp_bal = 0
                    for i in range(len(df_latest)):
                        temp_bal = round(temp_bal + df_latest.at[i, "收入"] - df_latest.at[i, "支出"], 2)
                        df_latest.at[i, "余额"] = temp_bal
                    
                    conn.update(worksheet="Summary", data=df_latest)
                    st.session_state.edit_iteration += 1
                    st.balloons()
                    st.success(f"✅ 编号 {target} 修正成功并重算余额！")
                    st.cache_data.clear()
                    time.sleep(1.2)
                    st.rerun()
                
                if cancel_clicked:
                    st.session_state.edit_iteration += 1
                    st.rerun()
else:
    st.warning("🔒 权限验证：请输入正确密码访问。")
