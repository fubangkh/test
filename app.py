import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 页面基础配置 ---
st.set_page_config(page_title="富邦现金流水账", layout="wide")

# --- 权限配置 ---
STAFF_PWD = "123"      
ADMIN_PWD = "123"      

# --- 初始化 Google Sheets 连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 定义分类常量 ---
CORE_BUSINESS_TYPES = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
OTHER_INCOME_TYPES = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
OTHER_EXPENSE_TYPES = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]

INCOME_TYPES = CORE_BUSINESS_TYPES[:5] + OTHER_INCOME_TYPES
EXPENSE_TYPES = CORE_BUSINESS_TYPES[5:] + OTHER_EXPENSE_TYPES
ALL_FUND_PROPERTIES = INCOME_TYPES + EXPENSE_TYPES

# --- 侧边栏导航 ---
st.sidebar.title("💰 富邦现金流水账")
role = st.sidebar.radio("选择功能模块", ["数据录入", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")

if role == "数据录入":
    if password == STAFF_PWD:
        st.title("📝 日记账录入 (USD)")
        
        # 1. 读取数据（用于计算结余和提取人名库）
        df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        
        # 提取现有经手人列表（去重、去空、排序）
        if not df_latest.empty and "经手人" in df_latest.columns:
            existing_handlers = sorted(df_latest["经手人"].unique().tolist())
            existing_handlers = [h for h in existing_handlers if h] # 过滤掉空值
        else:
            existing_handlers = []
        
        # 在列表最前面加上“+ 新增”选项
        handler_options = ["🔍 从列表中选择"] + existing_handlers + ["➕ 新增经手人..."]

        if not df_latest.empty:
            df_latest["余额"] = pd.to_numeric(df_latest["余额"], errors='coerce').fillna(0)
            last_balance = float(df_latest.iloc[-1]["余额"])
        else:
            last_balance = 0.0
        
        st.info(f"💵 当前系统账面结余：**${last_balance:,.2f}**")

        # 选定资金性质（外置以触发动态重绘）
        fund_property = st.selectbox("资金性质", ALL_FUND_PROPERTIES)

        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                report_date = st.date_input("日期")
                account_type = st.selectbox("账户类型", [
                    "ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户",
                    "ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", 
                    "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", 
                    "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", 
                    "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", 
                    "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", 
                    "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金" 
                ])
                
                # 项目/客户名称（主营业务必填）
                project_name = ""
                if fund_property in CORE_BUSINESS_TYPES:
                    project_name = st.text_input("💎 客户/项目名称 (必填)")

            with col2:
                amount = st.number_input("金额 (USD)", min_value=0.0, step=0.01, format="%.2f")
                # 🔄 经手人智能下拉菜单
                handler_select = st.selectbox("经手人选择", handler_options)
                new_handler = ""
                if handler_select == "➕ 新增经手人...":
                    new_handler = st.text_input("👤 请输入新经手人姓名")
                
            col3, col4 = st.columns(2)
            with col3:
                ref_no = st.text_input("审批/发票编号")
            with col4:
                summary = st.text_input("摘要 (必填)")
            
            note = st.text_area("备注")

            if st.form_submit_button("🚀 提交并同步至云端"):
                # 确定最终经手人姓名
                final_handler = new_handler if handler_select == "➕ 新增经手人..." else handler_select
                
                # 校验逻辑
                is_core = fund_property in CORE_BUSINESS_TYPES
                if not summary:
                    st.error("❌ 请填写摘要！")
                elif final_handler in ["🔍 从列表中选择", ""]:
                    st.error("❌ 请选择或输入有效的经手人！")
                elif is_core and not project_name:
                    st.error(f"❌ 选了【{fund_property}】，请填写‘客户/项目名称’！")
                elif amount <= 0:
                    st.error("❌ 金额必须大于 0！")
                else:
                    try:
                        inc = amount if fund_property in INCOME_TYPES else 0.0
                        exp = amount if fund_property in EXPENSE_TYPES else 0.0
                        new_balance = last_balance + inc - exp
                        
                        new_row = {
                            "日期": report_date.strftime('%Y-%m-%d'),
                            "摘要": summary, 
                            "客户/项目名称": project_name,
                            "账户": account_type, 
                            "审批/发票编号": ref_no,
                            "资金性质": fund_property, 
                            "收入": inc, "支出": exp,
                            "余额": new_balance, 
                            "经手人": final_handler, 
                            "备注": note
                        }
                        
                        updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                        conn.update(worksheet="Summary", data=updated_df)
                        
                        st.success(f"✅ {final_handler} 的记录已同步！当前结余：${new_balance:,.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"同步失败: {e}")

# --- 管理看板（保持原样） ---
elif role == "管理看板":
    if password == ADMIN_PWD:
        st.title("📊 财务决策看板 (USD)")
        try:
            df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
            if not df_sum.empty:
                for col in ["收入", "支出", "余额"]:
                    df_sum[col] = pd.to_numeric(df_sum[col], errors='coerce').fillna(0)
                df_sum['日期'] = pd.to_datetime(df_sum['日期'])
                df_sum = df_sum.sort_values('日期')
                
                now = pd.Timestamp.now()
                df_month = df_sum[(df_sum['日期'].dt.month == now.month) & (df_sum['日期'].dt.year == now.year)]

                if not df_month.empty:
                    first_row_m = df_month.iloc[0]
                    opening_bal = float(first_row_m["余额"]) - float(first_row_m["收入"]) + float(first_row_m["支出"])
                    m_income = df_month["收入"].sum()
                    m_expense = df_month["支出"].sum()
                    curr_bal = df_month.iloc[-1]["余额"]
                else:
                    opening_bal = float(df_sum.iloc[-1]["余额"]) if not df_sum.empty else 0.0
                    m_income, m_expense, curr_bal = 0.0, 0.0, opening_bal

                st.subheader(f"📅 {now.year}年{now.month}月 财务概况")
                c1, c2, c3 = st.columns(3)
                c1.metric("本月期初余额", f"${opening_bal:,.2f}")
                c2.metric("本月累计收入", f"${m_income:,.2f}")
                c3.metric("本月累计支出", f"${m_expense:,.2f}", delta=f"-${m_expense:,.2f}", delta_color="inverse")
                
                st.markdown("---")
                df_display = df_sum.copy()
                df_display['日期'] = df_display['日期'].dt.strftime('%Y-%m-%d')
                st.dataframe(df_display.sort_index(ascending=False).style.format({"收入": "{:.2f}", "支出": "{:.2f}", "余额": "{:.2f}"}), use_container_width=True)

                with st.expander("🛠️ 数据管理"):
                    del_idx = st.number_input("行索引", min_value=0, max_value=len(df_sum)-1, step=1)
                    if st.button("确认删除"):
                        conn.update(worksheet="Summary", data=df_sum.drop(del_idx))
                        st.rerun()
            else:
                st.info("📊 暂无数据")
        except Exception as e:
            st.error(f"看板异常: {e}")
