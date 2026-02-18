import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(page_title="富邦现金日记账", layout="wide")

# --- 权限配置 ---
STAFF_PWD = "123"      
ADMIN_PWD = "123"      

# --- 初始化连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 核心辅助函数 ---
def get_reference_rate(df_history, currency):
    now = datetime.now()
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now.strftime('%Y-%m')
        df_this_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_this_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try:
                    return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if res.status_code == 200:
            data = res.json().get("rates", {})
            rates = {"RMB": data.get("CNY", 7.23), "VND": data.get("VND", 25450.0), "HKD": data.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

def generate_serial_no(df_history):
    """字母前缀编号逻辑: R + YYYYMMDD + 3位序号"""
    today_prefix = "R" + datetime.now().strftime("%Y%m%d")
    if df_history.empty or "录入编号" not in df_history.columns:
        return today_prefix + "001"
    
    # 筛选出当天 R 开头的记录
    today_records = df_history[df_history["录入编号"].astype(str).str.startswith(today_prefix)]
    if today_records.empty:
        return today_prefix + "001"
    
    # 取出当天最大的序号并递增
    last_no = today_records["录入编号"].astype(str).max()
    # 截取最后3位数字进行递增
    try:
        next_val = int(last_no[-3:]) + 1
    except:
        next_val = 1
    return today_prefix + f"{next_val:03d}"

# --- 常量定义 ---
ACCOUNTS_LIST = ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"]
CORE_TYPES = ["期初结转", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
OTHER_INC = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
OTHER_EXP = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPS = (CORE_TYPES[:6] + OTHER_INC) + (CORE_TYPES[6:] + OTHER_EXP)

# --- 侧边栏 ---
st.sidebar.title("💰 富邦现金日记账")
role = st.sidebar.radio("功能选择", ["数据录入", "数据修改", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")
df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")

# --- 1. 数据录入 ---
if role == "数据录入" and password == STAFF_PWD:
    st.title("📝 专业账目录入")
    last_bal = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
    st.info(f"💵 账户总结余：**${last_bal:,.2f}** (USD)")

    c_top1, c_top2 = st.columns([1, 2])
    with c_top1: report_date = st.date_input("日期")
    with c_top2: summary = st.text_input("摘要 (必填)")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fund_prop = st.selectbox("资金性质", ALL_FUND_PROPS)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
        ref_rate = 1.0 if currency == "USD" else get_reference_rate(df_latest, currency)
        ex_rate = st.number_input("记账汇率", value=float(ref_rate), format="%.4f")
        raw_amt = st.number_input(f"录入金额 ({currency})", min_value=0.0, step=0.01)
        final_usd = raw_amt / ex_rate if ex_rate > 0 else 0.0
        st.markdown(f"📊 **折合预估：${final_usd:,.2f} USD**")

    with col2:
        acc_type = st.selectbox("结算账户", ACCOUNTS_LIST)
        proj_name = st.text_input("💎 客户/项目名称") if fund_prop in CORE_TYPES else ""
        ref_no = st.text_input("📑 审批/发票编号")
        handlers = sorted([h for h in df_latest["经手人"].unique().tolist() if h]) if not df_latest.empty else []
        h_select = st.selectbox("经手人", ["🔍 选择"] + handlers + ["➕ 新增"])
        new_h = st.text_input("👤 输入新名字") if h_select == "➕ 新增" else ""

    note = st.text_area("备注")

    if st.button("🚀 确认提交"):
        handler = new_h if h_select == "➕ 新增" else h_select
        if not summary or handler in ["🔍 选择", ""]: st.error("❌ 摘要和经手人为必填项！")
        else:
            try:
                inc = final_usd if fund_prop in (CORE_TYPES[:6] + OTHER_INC) else 0.0
                exp = final_usd if fund_prop in (CORE_TYPES[6:] + OTHER_EXP) else 0.0
                serial = generate_serial_no(df_latest)
                now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_row = {
                    "录入编号": serial, "提交时间": now_time, "修改时间": "--",
                    "日期": report_date.strftime('%Y-%m-%d'), "摘要": summary,
                    "客户/项目名称": proj_name, "账户": acc_type, "审批/发票编号": ref_no,
                    "资金性质": fund_prop, "收入": inc, "支出": exp,
                    "余额": last_bal + inc - exp, "经手人": handler, 
                    "备注": f"【原币：{raw_amt} {currency}，汇率：{ex_rate}】 " + note
                }
                updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                conn.update(worksheet="Summary", data=updated_df)
                st.success(f"✅ 录入成功！流水号：{serial}")
                st.rerun()
            except Exception as e: st.error(f"同步失败: {e}")

# --- 2. 数据修改 ---
elif role == "数据修改" and password == ADMIN_PWD:
    st.title("🛠️ 数据修正 (审计模式)")
    if not df_latest.empty:
        serial_list = df_latest["录入编号"].tolist()[::-1]
        edit_id = st.selectbox("请选择要修改的流水号", serial_list)
        row_idx = df_latest[df_latest["录入编号"] == edit_id].index[0]
        row_edit = df_latest.loc[row_idx]
        
        with st.form("edit_form"):
            st.warning(f"正在修改: {edit_id} | 初始提交: {row_edit['提交时间']}")
            c1, c2 = st.columns(2)
            with c1:
                new_date = st.date_input("日期", value=pd.to_datetime(row_edit["日期"]))
                new_sum = st.text_input("摘要", value=row_edit["摘要"])
                new_inc = st.number_input("收入 (USD)", value=float(row_edit["收入"]))
            with c2:
                new_exp = st.number_input("支出 (USD)", value=float(row_edit["支出"]))
                new_acc = st.selectbox("账户", ACCOUNTS_LIST, index=ACCOUNTS_LIST.index(row_edit["账户"]) if row_edit["账户"] in ACCOUNTS_LIST else 0)
                new_note = st.text_area("备注", value=row_edit["备注"])
            
            if st.form_submit_button("💾 保存修改"):
                df_latest.at[row_idx, "日期"] = new_date.strftime('%Y-%m-%d')
                df_latest.at[row_idx, "摘要"], df_latest.at[row_idx, "收入"] = new_sum, new_inc
                df_latest.at[row_idx, "支出"], df_latest.at[row_idx, "账户"] = new_exp, new_acc
                df_latest.at[row_idx, "备注"], df_latest.at[row_idx, "修改时间"] = new_note, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cur_bal = 0.0
                for i in range(len(df_latest)):
                    cur_bal += (float(df_latest.at[i, "收入"]) - float(df_latest.at[i, "支出"]))
                    df_latest.at[i, "余额"] = cur_bal
                conn.update(worksheet="Summary", data=df_latest)
                st.success("✅ 修改已保存。")
                st.rerun()
        st.dataframe(df_latest.sort_index(ascending=False), use_container_width=True)

# --- 3. 管理看板 ---
elif role == "管理看板" and password == ADMIN_PWD:
    st.title("📊 财务审计看板")
    if not df_latest.empty:
        df_vis = df_latest.copy()
        df_vis['日期'] = pd.to_datetime(df_vis['日期'])
        for col in ["收入", "支出", "余额"]: df_vis[col] = pd.to_numeric(df_vis[col], errors='coerce').fillna(0)
        
        total_bal = df_vis.iloc[-1]['余额']
        m1, m2 = st.columns(2)
        m1.metric("💰 账户总余额", f"${total_bal:,.2f}")
        m2.metric("📅 记录笔数", len(df_vis))

        st.divider()
        st.subheader("🏦 银行账户结余汇总 (USD)")
        acc_summary = []
        for acc in ACCOUNTS_LIST:
            d_acc = df_vis[df_vis['账户'] == acc]
            if not d_acc.empty:
                bal = d_acc['收入'].sum() - d_acc['支出'].sum()
                if abs(bal) > 0.01:
                    acc_summary.append({"账户": acc, "结余": bal})
        if acc_summary:
            st.table(pd.DataFrame(acc_summary).sort_values(by="结余", ascending=False).style.format({"结余": "${:,.2f}"}))

        st.divider()
        st.subheader("📝 全量审计明细表")
        st.dataframe(df_latest.sort_index(ascending=False), use_container_width=True)
