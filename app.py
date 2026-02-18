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
ADMIN_PWD = "123"  # 管理员看报表的密码
STAFF_PWD = "123"  # 财务录入数据的密码

# --- 3. 逻辑判断 ---
if role == "数据录入":
    if password == STAFF_PWD:
        st.title("📝 出纳日记账录入")

        # 1. 实时读取当前最新余额
        df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        last_balance = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
        
        # 2. 在显眼位置显示当前账面余额（只读）
        st.info(f"💰 当前系统账面总余额：**¥{last_balance:,.2f}**")

        trans_type = st.radio("收支类型", ["收入", "支出"], horizontal=True)

        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                report_date = st.date_input("日期")
                account_type = st.selectbox("账户类型", ["银行存款", "现金", "微信", "支付宝"])
            with col2:
                amount = st.number_input(f"请输入【{trans_type}】金额", min_value=0.0, step=100.0)
                # 💡 这里不再提供余额输入框，仅作文字提示
                st.text_input("当前余额 (系统自动计算)", value=f"¥{last_balance:,.2f}", disabled=True)

            col3, col4 = st.columns(2)
            with col3:
                handler = st.text_input("经手人")
            with col4:
                ref_no = st.text_input("审批/发票编号")
            
            summary = st.text_input("摘要 (必填)")
            note = st.text_area("备注")

            if st.form_submit_button("🚀 提交并同步"):
                if not summary or not handler:
                    st.error("❌ 请填写摘要和经手人！")
                else:
                    try:
                        # 计算新余额
                        inc = amount if trans_type == "收入" else 0.0
                        exp = amount if trans_type == "支出" else 0.0
                        new_balance = last_balance + inc - exp
                        
                        # 💡 构造新行：删掉了 "序号" 键值对
                        new_row = {
                            "日期": report_date.strftime('%Y-%m-%d'),
                            "摘要": summary, 
                            "账户": account_type, 
                            "审批/发票编号": ref_no,
                            "收支类型": trans_type, 
                            "收入": inc, 
                            "支出": exp,
                            "余额": new_balance, 
                            "经手人": handler, 
                            "备注": note
                        }
                        
                        updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                        conn.update(worksheet="Summary", data=updated_df)
                        
                        st.success(f"✅ 记录已同步！当前结余：¥{new_balance:,.2f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"同步失败: {e}")
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
                    first_row_month = df_month.iloc[0]
                    opening_balance = float(first_row_month["余额"]) - float(first_row_month["收入"]) + float(first_row_month["支出"])
                    month_income = df_month["收入"].sum()
                    month_expense = df_month["支出"].sum()
                    current_balance = df_month.iloc[-1]["余额"]
                else:
                    opening_balance = float(df_sum.iloc[-1]["余额"])
                    month_income, month_expense = 0.0, 0.0
                    current_balance = opening_balance

                # --- 布局显示：全部改为 $ 符号 ---
                st.subheader(f"📅 {now.year}年{now.month}月 财务概况")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("本月期初余额", f"${opening_balance:,.2f}")
                with col2:
                    st.metric("本月累计收入", f"${month_income:,.2f}")
                with col3:
                    st.metric("本月累计支出", f"${month_expense:,.2f}", delta=f"-${month_expense:,.2f}", delta_color="inverse")

                st.markdown("---")
                col4, col5 = st.columns(2)
                with col4:
                    net_cash = month_income - month_expense
                    st.metric("本月收支净额", f"${net_cash:,.2f}", delta=f"${net_cash:,.2f}")
                with col5:
                    st.metric("当前动态总余额", f"${current_balance:,.2f}")

                # --- 流水表美化：强制显示两位小数 ---
                st.markdown("---")
                st.subheader("📋 详细收支流水 (USD)")
                df_display = df_sum.copy()
                df_display['日期'] = df_display['日期'].dt.strftime('%Y-%m-%d')
                
                # 使用 Pandas 的样式器强制表格显示两位小数
                styled_df = df_display.sort_index(ascending=False).style.format({
                    "收入": "{:.2f}",
                    "支出": "{:.2f}",
                    "余额": "{:.2f}"
                })
                st.dataframe(styled_df, use_container_width=True)

                # --- 数据管理保持不变 ---
                with st.expander("🛠️ 数据管理"):
                    delete_idx = st.number_input("输入要删除的行索引", min_value=0, max_value=len(df_sum)-1, step=1)
                    if st.button("确认删除该行"):
                        df_new = df_sum.drop(delete_idx)
                        conn.update(worksheet="Summary", data=df_new)
                        st.success(f"✅ 记录已删除")
                        st.rerun()
            else:
                st.info("📊 暂无数据")

        except Exception as e:
            st.error(f"看板计算异常: {e}")








