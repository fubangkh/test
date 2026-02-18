import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz  # 请确保环境中已安装 pytz

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")

# --- 2. 权限与时区配置 ---
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    """获取校准后的柬埔寨本地时间字符串"""
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

# --- 3. 初始化状态控制 (用于自动跳转) ---
if 'menu_option' not in st.session_state:
    st.session_state.menu_option = "数据录入"

# --- 4. 初始化连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. 核心辅助函数 ---
def get_reference_rate(df_history, currency):
    now_local = datetime.now(LOCAL_TZ)
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now_local.strftime('%Y-%m')
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
    today_prefix = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
    if df_history.empty or "录入编号" not in df_history.columns:
        return today_prefix + f"{1 + offset:03d}"
    ids = df_history["录入编号"].astype(str).str.strip()
    today_records = ids[ids.str.startswith(today_prefix)]
    if today_records.empty:
        return today_prefix + f"{1 + offset:03d}"
    try:
        last_no = today_records.max()
        next_val = int(last_no[-3:]) + 1 + offset
        return today_prefix + f"{next_val:03d}"
    except: return today_prefix + f"{1 + offset:03d}"

# --- 6. 常量定义 ---
ACCOUNTS_LIST = ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"]
INC_PROPS = ["期初结转", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_PROPS = ["内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPS = INC_PROPS + EXP_PROPS

# --- 7. 数据加载 ---
try:
    df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    df_latest.columns = df_latest.columns.str.strip()
except Exception as e:
    df_latest = pd.DataFrame(columns=["录入编号", "提交时间", "修改时间", "日期", "摘要", "客户/项目名称", "账户", "审批/发票编号", "资金性质", "收入", "支出", "余额", "经手人", "备注"])

# --- 8. 侧边栏导航 ---
st.sidebar.title("🏮 富邦日记账系统")
# 使用 index 绑定 session_state 实现自动跳转
menu_list = ["数据录入", "数据修改", "汇总统计"]
role = st.sidebar.radio(
    "功能选择", 
    menu_list, 
    index=menu_list.index(st.session_state.menu_option)
)
# 同步状态
st.session_state.menu_option = role
password = st.sidebar.text_input("请输入密码访问", type="password")

# --- 9. 功能逻辑 ---

# A. 数据录入
if role == "数据录入" and password == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
    st.info(f"💵 账户总结余：**${last_bal:,.2f}** (USD) | 柬埔寨时间：{get_now_str()}")

    with st.form("entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            report_date = st.date_input("业务日期")
            fund_prop = st.selectbox("资金性质", ALL_FUND_PROPS)
            currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
            ex_rate = st.number_input("实时汇率", value=float(get_reference_rate(df_latest, currency)), format="%.4f")
        with c2:
            summary = st.text_input("摘要 (必填)")
            acc_type = st.selectbox("结算账户", ACCOUNTS_LIST)
            raw_amt = st.number_input("金额", min_value=0.0, step=0.01)
            handler = st.text_input("经手人 (必填)")

        if st.form_submit_button("🚀 确认提交录入", use_container_width=True):
            if not summary or not handler:
                st.error("❌ 摘要和经手人不能为空")
            else:
                final_usd = raw_amt / ex_rate if ex_rate > 0 else 0.0
                serial1 = generate_serial_no(df_latest)
                row = {
                    "录入编号": serial1, "提交时间": get_now_str(), "修改时间": "--",
                    "日期": report_date.strftime('%Y-%m-%d'), "摘要": summary, "账户": acc_type,
                    "资金性质": fund_prop, "收入": final_usd if fund_prop in INC_PROPS else 0.0,
                    "支出": final_usd if fund_prop in EXP_PROPS else 0.0, 
                    "余额": last_bal + (final_usd if fund_prop in INC_PROPS else -final_usd), 
                    "经手人": handler
                }
                new_df = pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True).fillna("--")
                conn.update(worksheet="Summary", data=new_df)
                st.balloons()
                st.success("✅ 录入成功！")
                time.sleep(1.2)
                st.rerun()

# B. 数据修改 (核心跳转逻辑)
elif role == "数据修改" and password == ADMIN_PWD:
    st.title("🛠️ 数据修改")
    if not df_latest.empty:
        ids = df_latest["录入编号"].astype(str).tolist()[::-1]
        selected_id = st.selectbox("选择要修改的编号", ids)
        idx = df_latest[df_latest["录入编号"].astype(str) == selected_id].index[0]
        
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                e_date = st.date_input("日期", value=pd.to_datetime(df_latest.at[idx, "日期"]))
                e_sum = st.text_input("摘要", value=df_latest.at[idx, "摘要"])
                e_inc = st.number_input("收入 (USD)", value=float(df_latest.at[idx, "收入"]))
            with c2:
                e_h = st.text_input("经手人", value=df_latest.at[idx, "经手人"])
                e_exp = st.number_input("支出 (USD)", value=float(df_latest.at[idx, "支出"]))
                e_acc = st.selectbox("账户", ACCOUNTS_LIST, index=ACCOUNTS_LIST.index(df_latest.at[idx, "账户"]) if df_latest.at[idx, "账户"] in ACCOUNTS_LIST else 0)

            if st.form_submit_button("💾 保存并查看清单", use_container_width=True):
                df_latest.at[idx, "日期"] = e_date.strftime('%Y-%m-%d')
                df_latest.at[idx, "摘要"], df_latest.at[idx, "账户"] = e_sum, e_acc
                df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = e_inc, e_exp
                df_latest.at[idx, "经手人"] = e_h
                df_latest.at[idx, "修改时间"] = get_now_str()
                
                # 重算余额
                bal = 0.0
                for i in range(len(df_latest)):
                    bal += (float(df_latest.at[i, "收入"]) - float(df_latest.at[i, "支出"]))
                    df_latest.at[i, "余额"] = bal
                
                conn.update(worksheet="Summary", data=df_latest)
                
                # --- 触发反馈并强制跳转 ---
                st.balloons()
                st.success("✅ 修改成功！正在跳转至汇总清单...")
                st.session_state.menu_option = "汇总统计" # 强制修改导航状态
                time.sleep(1.5)
                st.rerun() # 重新运行，此时 radio 会自动选到汇总统计

# C. 汇总统计
elif role == "汇总统计" and password == ADMIN_PWD:
    st.title("📊 汇总统计")
    if not df_latest.empty:
        df_v = df_latest.copy()
        df_v['日期_dt'] = pd.to_datetime(df_v['日期'])
        for c in ["收入", "支出", "余额"]: df_v[c] = pd.to_numeric(df_v[c], errors='coerce').fillna(0)
        
        months = df_v['日期_dt'].dt.strftime('%Y-%m').unique().tolist()
        months.sort(reverse=True)
        selected_month = st.sidebar.selectbox("📅 筛选月份", ["全部历史"] + months)
        
        df_filtered = df_v if selected_month == "全部历史" else df_v[df_v['日期_dt'].dt.strftime('%Y-%m') == selected_month]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 期末结余", f"${df_filtered.iloc[-1]['余额'] if not df_filtered.empty else 0:,.2f}")
        m2.metric("📥 累计收入", f"${df_filtered['收入'].sum():,.2f}")
        m3.metric("📤 累计支出", f"${df_filtered['支出'].sum():,.2f}")
        
        st.divider()
        st.dataframe(df_filtered.drop(columns=['日期_dt']).sort_index(ascending=False), use_container_width=True)
