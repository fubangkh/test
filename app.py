import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")

# --- 2. 权限配置 ---
STAFF_PWD = "123"
ADMIN_PWD = "123"

# --- 3. 初始化连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. 核心辅助函数 ---
def get_reference_rate(df_history, currency):
    """获取参考汇率"""
    now = datetime.now()
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now.strftime('%Y-%m')
        df_this_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_this_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if res.status_code == 200:
            data = res.json().get("rates", {})
            rates = {"RMB": data.get("CNY", 7.23), "VND": data.get("VND", 25450.0), "HKD": data.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

def generate_serial_no(df_history, offset=0):
    """生成 R+年月日+3位序号"""
    today_prefix = "R" + datetime.now().strftime("%Y%m%d")
    if df_history.empty or "录入编号" not in df_history.columns:
        return today_prefix + f"{1 + offset:03d}"
    today_records = df_history[df_history["录入编号"].astype(str).str.startswith(today_prefix)]
    if today_records.empty:
        return today_prefix + f"{1 + offset:03d}"
    try:
        last_no = today_records["录入编号"].astype(str).max()
        next_val = int(last_no[-3:]) + 1 + offset
        return today_prefix + f"{next_val:03d}"
    except:
        return today_prefix + f"{1 + offset:03d}"

# --- 5. 常量定义 ---
ACCOUNTS_LIST = ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"]
INC_PROPS = ["期初结转", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_PROPS = ["内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPS = INC_PROPS + EXP_PROPS

# --- 6. 数据加载 ---
try:
    df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
except:
    df_latest = pd.DataFrame(columns=["录入编号", "提交时间", "修改时间", "日期", "摘要", "客户/项目名称", "账户", "审批/发票编号", "资金性质", "收入", "支出", "余额", "经手人", "备注"])

for col in ["录入编号", "提交时间", "修改时间"]:
    if col not in df_latest.columns: df_latest[col] = "--"

# --- 7. 侧边栏 ---
st.sidebar.title("🏮 富邦日记账系统")
role = st.sidebar.radio("功能选择", ["数据录入", "数据修改", "汇总统计"])
password = st.sidebar.text_input("请输入密码访问", type="password")

# --- 8. 功能逻辑 ---

# A. 数据录入
if role == "数据录入" and password == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
    st.info(f"💵 账户总计余额：**${last_bal:,.2f}** (USD)")

    c1, c2 = st.columns(2)
    with c1:
        report_date = st.date_input("选择日期")
        fund_prop = st.selectbox("资金性质", ALL_FUND_PROPS)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
        ex_rate = st.number_input("实时汇率", value=float(get_reference_rate(df_latest, currency)), format="%.4f")
    with c2:
        summary = st.text_input("摘要内容 (必填)")
        acc_type = st.selectbox("选择结算账户", ACCOUNTS_LIST)
        raw_amt = st.number_input("录入原币金额", min_value=0.0, step=0.01)
        final_usd = raw_amt / ex_rate if ex_rate > 0 else 0.0
        st.markdown(f"📊 **折合美金：${final_usd:,.2f}**")

    # 自动调拨
    auto_transfer, target_acc = False, None
    if fund_prop == "内部调拨-转出":
        with st.container(border=True):
            st.subheader("🔄 自动调拨")
            auto_transfer = st.checkbox("同步生成对应的【转入】账目", value=True)
            if auto_transfer:
                target_acc = st.selectbox("请选择收款账户", [a for a in ACCOUNTS_LIST if a != acc_type])

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        handlers = sorted([h for h in df_latest["经手人"].unique().tolist() if h]) if not df_latest.empty else []
        h_select = st.selectbox("经手人", ["🔍 选择"] + handlers + ["➕ 新增"])
        new_h = st.text_input("手动输入经手人") if h_select == "➕ 新增" else ""
    with col_h2:
        proj_name = st.text_input("客户/项目名称")
        ref_no = st.text_input("审批单/发票号")

    note = st.text_area("备注信息")

    if st.button("🚀 确认提交录入"):
        handler = new_h if h_select == "➕ 新增" else h_select
        if not summary or handler in ["🔍 选择", ""]: st.error("❌ 请填写摘要并选择经手人")
        else:
            serial1 = generate_serial_no(df_latest)
            now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            inc1 = final_usd if fund_prop in INC_PROPS else 0.0
            exp1 = final_usd if fund_prop in EXP_PROPS else 0.0
            
            row1 = {
                "录入编号": serial1, "提交时间": now_time, "修改时间": "--",
                "日期": report_date.strftime('%Y-%m-%d'), "摘要": summary, "客户/项目名称": proj_name,
                "账户": acc_type, "审批/发票编号": ref_no, "资金性质": fund_prop,
                "收入": inc1, "支出": exp1, "余额": last_bal + inc1 - exp1, "经手人": handler, "备注": note
            }
            rows = [row1]
            if auto_transfer and target_acc:
                row2 = row1.copy()
                row2.update({
                    "录入编号": generate_serial_no(df_latest, 1), "摘要": f"{summary} (关联{serial1})",
                    "账户": target_acc, "资金性质": "内部调拨-转入", "收入": exp1, "支出": 0.0, "余额": last_bal + inc1
                })
                rows.append(row2)
            
            new_df = pd.concat([df_latest, pd.DataFrame(rows)], ignore_index=True).fillna("")
            conn.update(worksheet="Summary", data=new_df)
            st.success("✅ 数据已安全同步至云端！")
            st.rerun()

# B. 数据修改
elif role == "数据修改" and password == ADMIN_PWD:
    st.title("🛠️ 数据修改")
    if not df_latest.empty:
        ids = [s for s in df_latest["录入编号"].tolist() if s != "--"][::-1]
        selected_id = st.selectbox("请选择要修改的流水编号", ids)
        idx = df_latest[df_latest["录入编号"] == selected_id].index[0]
        
        with st.form("edit_form"):
            st.warning(f"正在编辑记录: {selected_id}")
            c1, c2 = st.columns(2)
            with c1:
                e_sum = st.text_input("摘要", value=df_latest.at[idx, "摘要"])
                e_acc = st.selectbox("账户", ACCOUNTS_LIST, index=ACCOUNTS_LIST.index(df_latest.at[idx, "账户"]) if df_latest.at[idx, "账户"] in ACCOUNTS_LIST else 0)
                e_inc = st.number_input("收入 (USD)", value=float(df_latest.at[idx, "收入"]))
            with c2:
                e_h = st.text_input("经手人", value=df_latest.at[idx, "经手人"])
                e_prop = st.selectbox("性质", ALL_FUND_PROPS, index=ALL_FUND_PROPS.index(df_latest.at[idx, "资金性质"]) if df_latest.at[idx, "资金性质"] in ALL_FUND_PROPS else 0)
                e_exp = st.number_input("支出 (USD)", value=float(df_latest.at[idx, "支出"]))
            
            if st.form_submit_button("💾 保存修改并重算余额"):
                df_latest.at[idx, "摘要"], df_latest.at[idx, "账户"] = e_sum, e_acc
                df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = e_inc, e_exp
                df_latest.at[idx, "经手人"], df_latest.at[idx, "资金性质"] = e_h, e_prop
                df_latest.at[idx, "修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 余额重算逻辑
                bal = 0.0
                for i in range(len(df_latest)):
                    bal += (float(df_latest.at[i, "收入"]) - float(df_latest.at[i, "支出"]))
                    df_latest.at[i, "余额"] = bal
                conn.update(worksheet="Summary", data=df_latest)
                st.success("✅ 修改已生效！")
                st.rerun()
        st.dataframe(df_latest.sort_index(ascending=False), use_container_width=True)

# C. 汇总统计
elif role == "汇总统计" and password == ADMIN_PWD:
    st.title("📊 汇总统计")
    if not df_latest.empty:
        df_v = df_latest.copy()
        for c in ["收入", "支出", "余额"]: df_v[c] = pd.to_numeric(df_v[c], errors='coerce').fillna(0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 实时总资产 (USD)", f"${df_v.iloc[-1]['余额']:,.2f}")
        m2.metric("📈 累计收入", f"${df_v['收入'].sum():,.2f}")
        m3.metric("📉 累计支出", f"${df_v['支出'].sum():,.2f}")

        st.divider()
        st.subheader("🏦 银行账户余额分布")
        acc_b = []
        for a in ACCOUNTS_LIST:
            d = df_v[df_v['账户'] == a]
            if not d.empty:
                val = d['收入'].sum() - d['支出'].sum()
                if abs(val) > 0.01: acc_b.append({"账户": a, "余额": val})
        if acc_b:
            st.table(pd.DataFrame(acc_b).sort_values("余额", ascending=False).style.format({"余额": "${:,.2f}"}))
        
        st.divider()
        st.subheader("📑 全量流水审计明细")
        st.dataframe(df_latest.sort_index(ascending=False), use_container_width=True)
