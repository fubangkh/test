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
        if not df_latest.empty:
            df_latest["余额"] = pd.to_numeric(df_latest["余额"], errors='coerce').fillna(0)
            last_balance = float(df_latest.iloc[-1]["余额"])
        else:
            last_balance = 0.0

        st.info(f"💵 当前结余：**${last_balance:,.2f}** (USD)")

        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                report_date = st.date_input("日期")
                fund_property = st.selectbox("资金性质", ALL_FUND_PROPERTIES)
                
                # 🔄 币种选择
                currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
                
                # 🔄 汇率逻辑
                ref_rate = 1.0 if currency == "USD" else get_reference_rate(df_latest, currency)
                exchange_rate = st.number_input(f"记账汇率", value=float(ref_rate), format="%.4f")
                
                # ✅ 修复联动：直接在 Label 里引用变量，并设置 Key 强制刷新
                raw_amount = st.number_input(f"录入金额 ({currency})", min_value=0.0, step=0.01, key=f"amt_{currency}")
                
                temp_usd = raw_amount / exchange_rate if exchange_rate != 0 else 0
                st.markdown(f"📊 **当前折合预估：${temp_usd:,.2f} USD**")

            with col2:
                account_type = st.selectbox("结算账户", ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"])
                
                project_name = st.text_input("💎 客户/项目名称 (必填项)") if fund_property in CORE_BUSINESS_TYPES else ""

                ref_no = st.text_input("📑 审批/发票编号")
                
                handlers = sorted([h for h in df_latest["经手人"].unique().tolist() if h]) if not df_latest.empty else []
                h_select = st.selectbox("经手人", ["🔍 选择"] + handlers + ["➕ 新增"])
                new_h = st.text_input("👤 输入新名字") if h_select == "➕ 新增" else ""

            summary = st.text_input("摘要 (必填)")
            note = st.text_area("备注")

            if st.form_submit_button("🚀 提交并同步"):
                handler = new_h if h_select == "➕ 新增" else h_select
                final_usd = raw_amount / exchange_rate if exchange_rate != 0 else 0
                
                if not summary or handler in ["🔍 选择", ""]:
                    st.error("❌ 摘要和经手人不能为空！")
                elif fund_property in CORE_BUSINESS_TYPES and not project_name:
                    st.error(f"❌ 选了【{fund_property}】，客户/项目名称必须填写！")
                elif raw_amount <= 0:
                    st.error(f"❌ 录入金额 ({currency}) 必须大于 0！")
                else:
                    try:
                        inc = final_usd if fund_property in (CORE_BUSINESS_TYPES[:5] + OTHER_INCOME_TYPES) else 0.0
                        exp = final_usd if fund_property in (CORE_BUSINESS_TYPES[5:] + OTHER_EXPENSE_TYPES) else 0.0
                        
                        auto_note = note if note else ""
                        if currency != "USD":
                            auto_note = f"【原币：{raw_amount} {currency}，汇率：{exchange_rate}】 " + auto_note
                        
                        new_row = {
                            "日期": report_date.strftime('%Y-%m-%d'),
                            "摘要": summary, 
                            "客户/项目名称": project_name,
                            "账户": account_type, 
                            "审批/发票编号": ref_no,
                            "资金性质": fund_property,
                            "收入": inc, "支出": exp, "余额": last_balance + inc - exp,
                            "经手人": handler, "备注": auto_note
                        }
                        
                        updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                        conn.update(worksheet="Summary", data=updated_df)
                        st.success(f"✅ 录入成功！折合：${final_usd:,.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"数据保存失败: {e}")

elif role == "管理看板":
    if password == ADMIN_PWD:
        st.title("📊 财务看板 (USD)")
        df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        if not df_sum.empty:
            for c in ["收入", "支出", "余额"]: 
                df_sum[c] = pd.to_numeric(df_sum[c], errors='coerce').fillna(0)
            st.dataframe(df_sum.sort_index(ascending=False).style.format({"收入": "{:.2f}", "支出": "{:.2f}", "余额": "{:.2f}"}), use_container_width=True)
