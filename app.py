import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 页面基本配置
st.set_page_config(page_title="财务管理系统", layout="wide")
st.title("💰 富邦日记账与发票管理系统")

# 建立云端连接
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 角色切换 ---
role = st.sidebar.radio("请选择操作角色", ["财务录入员", "授权管理人员"])

if role == "财务录入员":
    st.header("📝 每日数据上报")
    
    with st.form("main_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            report_date = st.date_input("报备日期", datetime.now()).strftime("%Y-%m-%d")
        with col2:
            income = st.number_input("昨日收款金额 (元)", min_value=0.0)
        with col3:
            balance = st.number_input("当前现金余额 (元)", min_value=0.0)
        
        user_name = st.text_input("填报人姓名")
        
        st.divider()
        st.write("### 🧾 手动录入发票明细")
        # 默认提供 5 行输入空间，如果不够可以增加
        num_rows = st.number_input("本次录入发票张数", min_value=1, max_value=20, value=1)
        invoice_list = []
        for i in range(int(num_rows)):
            c1, c2, c3 = st.columns([2, 3, 2])
            inv_no = c1.text_input(f"发票号 #{i+1}", key=f"no_{i}")
            cust = c2.text_input(f"客户名称 #{i+1}", key=f"cu_{i}")
            amt = c3.number_input(f"金额 #{i+1}", min_value=0.0, key=f"am_{i}")
            if inv_no: # 只有填了单号的才计入
                invoice_list.append({"对应日期": report_date, "发票号": inv_no, "客户名称": cust, "金额": amt})

        submitted = st.form_submit_button("🚀 提交数据并同步至云端")
        
        if submitted:
            try:
                # 构造汇总行
                new_summary_data = [[report_date, income, balance, user_name]]
                
                # 使用最基础的 append_rows 方法（绕过复杂的 DataFrame 合并）
                # 这种方法对 Google API 最友好
                conn.create(
                    worksheet="Summary",
                    data=new_summary_data
                )
                
                # 如果有发票明细，同样处理
                if invoice_list:
                    # 将字典列表转为二维列表 [[...], [...]]
                    new_invoice_data = [
                        [item["对应日期"], item["发票号"], item["客户名称"], item["金额"]] 
                        for item in invoice_list
                    ]
                    conn.create(
                        worksheet="Invoices",
                        data=new_invoice_data
                    )
                
                st.success("✅ 提交成功！数据已实时追加入云端表格。")
                st.balloons()
            except Exception as e:
                st.error(f"同步失败。当前错误详细信息: {e}")
                st.info("💡 终极排查建议：如果依然 400，请尝试在 Google Sheets 随便一个空白单元格打个空格，确认表格不是‘从未编辑’状态。")

