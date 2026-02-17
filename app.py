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
        # ... 这里放你原来的录入表单代码 (form) ...
        # 注意提交按钮逻辑保持不变
    elif password == "":
        st.info("请输入财务录入密码以开始工作")
    else:
        st.error("密码错误，请联系管理人员")

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
