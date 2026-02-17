import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. 基础配置 ---
st.set_page_config(page_title="富邦财务报备系统", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 侧边栏：权限控制 ---
st.sidebar.title("🔐 访问控制")
role = st.sidebar.selectbox("选择操作模式", ["数据录入", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")

# 这里设置你的密码
ADMIN_PWD = "admin888"  # 管理员看报表的密码
STAFF_PWD = "fb123"      # 财务录入数据的密码

# --- 3. 逻辑判断 ---
if role == "数据录入":
    if password == STAFF_PWD:
        st.title("📝 财务日常录入")
        
        # --- 重新填回的表单代码开始 ---
        with st.form("entry_form"):
            col1, col2 = st.columns(2)
            with col1:
                report_date = st.date_input("报备日期")
                income = st.number_input("昨日收款金额 (元)", min_value=0.0, step=100.0)
            with col2:
                balance = st.number_input("当前现金余额 (元)", min_value=0.0, step=100.0)
                user_name = st.text_input("填报人姓名")

            st.markdown("---")
            st.subheader("🧾 发票明细录入")
            
            # 使用文本框让用户输入，每行一条：发票号,客户,金额
            invoice_raw = st.text_area("格式：发票号,客户名称,金额 (每行一条)", help="例如：INV001,某某公司,5000")
            
            submitted = st.form_submit_button("🚀 提交数据并同步至云端")
            
            if submitted:
                if not user_name:
                    st.error("请输入填报人姓名！")
                else:
                    try:
                        # 处理发票数据
                        invoice_list = []
                        if invoice_raw.strip():
                            for line in invoice_raw.strip().split('\n'):
                                parts = line.split(',')
                                if len(parts) == 3:
                                    invoice_list.append({
                                        "对应日期": report_date.strftime('%Y-%m-%d'),
                                        "发票号": parts[0].strip(),
                                        "客户名称": parts[1].strip(),
                                        "金额": float(parts[2].strip())
                                    })

                        # 执行同步逻辑
                        summary_df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
                        new_summary = pd.DataFrame([{"日期": report_date.strftime('%Y-%m-%d'), "收款金额": income, "现金余额": balance, "填报人": user_name}])
                        updated_summary = pd.concat([summary_df, new_summary], ignore_index=True).fillna("")
                        conn.update(worksheet="Summary", data=updated_summary)
                        
                        if invoice_list:
                            invoice_df = conn.read(worksheet="Invoices", ttl=0).dropna(how="all")
                            new_inv_df = pd.DataFrame(invoice_list)
                            updated_invoices = pd.concat([invoice_df, new_inv_df], ignore_index=True).fillna("")
                            conn.update(worksheet="Invoices", data=updated_invoices)
                            
                        st.success("✅ 同步成功！数据已写入 Google Sheets。")
                        st.balloons()
                    except Exception as e:
                        st.error(f"同步失败: {e}")
        # --- 重新填回的表单代码结束 ---

    elif password == "":
        st.info("💡 请在左侧边栏输入‘录入密码’以开启表单")
    else:
        st.error("❌ 密码错误")

elif role == "管理看板":
    if password == ADMIN_PWD:
        st.title("📊 财务决策看板")
        
        try:
            # 1. 实时读取并按日期排序，确保最后一行是最新日期
            df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
            df_sum['日期'] = pd.to_datetime(df_sum['日期'])
            df_sum = df_sum.sort_values('日期')

            # 2. 计算环比逻辑
            if len(df_sum) >= 2:
                # 获取最后两行数据
                today_data = df_sum.iloc[-1]
                yesterday_data = df_sum.iloc[-2]
                
                curr_income = float(today_data["收款金额"])
                prev_income = float(yesterday_data["收款金额"])
                income_delta = curr_income - prev_income
                
                curr_balance = float(today_data["现金余额"])
                prev_balance = float(yesterday_data["现金余额"])
                balance_delta = curr_balance - prev_balance
            else:
                # 如果只有一行数据，则没有环比
                curr_income = float(df_sum.iloc[-1]["收款金额"]) if not df_sum.empty else 0
                income_delta = 0
                curr_balance = float(df_sum.iloc[-1]["现金余额"]) if not df_sum.empty else 0
                balance_delta = 0

            # 3. 显示指标卡片
            col1, col2, col3 = st.columns(3)
            with col1:
                # 显示现金余额及其变动
                st.metric("当前现金总余额", f"¥{curr_balance:,.2f}", delta=f"¥{balance_delta:,.2f}")
            with col2:
                # 显示今日收款及其环比昨日的增减
                # delta_color="normal" 会自动实现：正数绿色，负数红色
                st.metric("最新单日收款", f"¥{curr_income:,.2f}", delta=f"{income_delta:,.2f} (较上笔)")
            with col3:
                st.metric("累计报备次数", f"{len(df_sum)} 次")

            # ... 下方保留原来的 tab 表格展示 ...

        except Exception as e:
            st.error(f"计算看板指标时出错: {e}")

