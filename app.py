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

# --- 核心函数：获取参考汇率 ---
def get_reference_rate(df_history, currency):
    now = datetime.now()
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now.strftime('%Y-%m')
        df_this_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_this_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try:
                    return float(note.split("汇率：")[1].split("】")[0])
                except:
                    continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if res.status_code == 200:
            data = res.json().get("rates", {})
            rates = {"RMB": data.get("CNY", 7.23), "VND": data.get("VND", 25450.0), "HKD": data.get("HKD", 7.82)}
    except:
        pass
    return rates.get(currency, 1.0)

# --- 常量定义 ---
CORE_BUSINESS_TYPES = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
OTHER_INCOME_TYPES = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
OTHER_EXPENSE_TYPES = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPERTIES = (CORE_BUSINESS_TYPES[:5] + OTHER_INCOME_TYPES) + (CORE_BUSINESS_TYPES[5:] + OTHER_EXPENSE_TYPES)

# --- 侧边栏 ---
st.sidebar.title("💰 富邦现金日记账")
role = st.sidebar.radio("选择功能模块", ["数据录入", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")

if role == "数据录入":
    if password == STAFF_PWD:
        st.title("📝 日记账录入")
        
        df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        last_balance = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
        st.info(f"💵 当前结余：**${last_balance:,.2f}** (USD)")

        # --- 实时互动区 (移出 Form 外以实现秒级联动) ---
        col1, col2 = st.columns(2)
        with col1:
            report_date = st.date_input("日期")
            fund_property = st.selectbox("资金性质", ALL_FUND_PROPERTIES)
            currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
            
            ref_rate = 1.0 if currency == "USD" else get_reference_rate(df_latest, currency)
            exchange_rate = st.number_input(f"记账汇率", value=float(ref_rate), format="%.4f")
            
            # 这里是联动的核心：Label 随变量实时改变
            raw_amount = st.number_input(f"录入金额 ({currency})", min_value=0.0, step=0.01)
            
            final_usd = raw_amount / exchange_rate if exchange_rate > 0 else 0.0
            st.success(f"📊 **当前折合预估：${final_usd:
