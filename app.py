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
        st.title("📝 财务收支记账录入")
        
        with st.form("entry_form", clear_on_submit=True):
            # 第一行：基础信息
            col1, col2, col3 = st.columns(3)
            with col1:
                report_date = st.date_input("日期", help="列B")
            with col2:
                account_type = st.selectbox("账户", ["现金", "银行存款", "微信", "支付宝", "其他"], help="列D")
            with col3:
                trans_type = st.radio("收支类型", ["收入", "支出"], horizontal=True, help="列F")

            # 第二行：核心金额
            col4, col5, col6 = st.columns(3)
            with col4:
                income_val = st.number_input("收入金额", min_value=0.0, step=100.0) if trans_type == "收入" else 0.0
            with col5:
                expense_val = st.number_input("支出金额", min_value=0.0, step=100.0) if trans_type == "支出" else 0.0
            with col6:
                current_balance = st.number_input("当前账户余额", min_value=0.0, step=100.0, help="列I")

            # 第三行：单据与经手人
            col7, col8 = st.columns(2)
            with col7:
                ref_no = st.text_input("审批/发票编号", help="列E")
            with col8:
                handler = st.text_input("经手人", help="列J")

            # 第四行：文字描述
            summary = st.text_input("摘要 (必填)", help="列C")
            note = st.text_area("备注", help="列K")

            submitted = st.form_submit_button("🚀 提交并同步至云端")

            if submitted:
                if not summary or not handler:
                    st.error("❌ 请填写‘摘要’和‘经手人’！")
                else:
                    try:
                        # 1. 读取现有数据获取当前最大序号
                        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
                        next_id = 1 if df.empty else len(df) + 1
                        
                        # 2. 构造新行 (严格对应 A-K 列顺序)
                        new_row = {
                            "序号": next_id, # 列A
                            "日期": report_date.strftime('%Y-%m-%d'), # 列B
                            "摘要": summary, # 列C
                            "账户": account_type, # 列D
                            "审批/发票编号": ref_no, # 列E
                            "收支类型": trans_type, # 列F
                            "收入": income_val, # 列G
                            "支出": expense_val, # 列H
                            "余额": current_balance, # 列I
                            "经手人": handler, # 列J
                            "备注": note # 列K
                        }
                        
                        new_df = pd.DataFrame([new_row])
                        updated_df = pd.concat([df, new_df], ignore_index=True).fillna("")
                        
                        # 3. 写入 Google Sheets
                        conn.update(worksheet="Summary", data=updated_df)
                        
                        st.success(f"✅ 第 {next_id} 号记录已成功同步！")
                        st.balloons()
                    except Exception as e:
                        st.error(f"同步失败: {e}")

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


