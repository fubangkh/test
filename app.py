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
            col1, col2, col3 = st.columns(3)
            with col1:
                report_date = st.date_input("日期")
            with col2:
                account_type = st.selectbox("账户", ["银行存款", "现金", "微信", "支付宝"])
            with col3:
                trans_type = st.radio("收支类型", ["收入", "支出"], horizontal=True)

            # 💡 动态显示：根据收支类型只显示一个输入框
            amount = st.number_input(f"请输入{trans_type}金额", min_value=0.0, step=100.0)
            
            col4, col5 = st.columns(2)
            with col4:
                current_balance = st.number_input("当前账户总余额", min_value=0.0, step=100.0)
            with col5:
                handler = st.text_input("经手人")

            ref_no = st.text_input("审批/发票编号")
            summary = st.text_input("摘要 (必填)")
            note = st.text_area("备注")

            if st.form_submit_button("🚀 提交并同步"):
                if not summary or not handler:
                    st.error("❌ 摘要和经手人为必填项")
                else:
                    try:
                        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
                        # 转换金额逻辑
                        inc = amount if trans_type == "收入" else 0.0
                        exp = amount if trans_type == "支出" else 0.0
                        
                        new_row = {
                            "序号": len(df) + 1,
                            "日期": report_date.strftime('%Y-%m-%d'),
                            "摘要": summary, "账户": account_type, "审批/发票编号": ref_no,
                            "收支类型": trans_type, "收入": inc, "支出": exp,
                            "余额": current_balance, "经手人": handler, "备注": note
                        }
                        updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        conn.update(worksheet="Summary", data=updated_df)
                        st.success("✅ 录入成功！")
                        st.balloons()
                    except Exception as e:
                        st.error(f"同步失败: {e}")

elif role == "管理看板":
    if password == ADMIN_PWD:
        st.title("📊 财务决策看板")
        
        try:
            # 1. 实时读取数据并处理日期
            df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
            
            if not df_sum.empty:
                df_sum['日期'] = pd.to_datetime(df_sum['日期'])
                df_sum = df_sum.sort_values('日期')
                
                # 获取当前月份和年份
                current_month = pd.Timestamp.now().month
                current_year = pd.Timestamp.now().year
                
                # 筛选本月数据
                month_mask = (df_sum['日期'].dt.month == current_month) & (df_sum['日期'].dt.year == current_year)
                df_month = df_sum[month_mask]

                # --- 计算各项指标 ---
                # A. 期初余额：本月第一笔记录之前的余额（若无则取本月第一笔的余额减去第一笔的收支）
                if not df_month.empty:
                    first_row = df_month.iloc[0]
                    # 期初 = 第一笔的余额 - 第一笔收入 + 第一笔支出
                    opening_balance = float(first_row["余额"]) - float(first_row["收入"]) + float(first_row["支出"])
                    month_income = df_month["收入"].sum()
                    month_expense = df_month["支出"].sum()
                    current_balance = df_month.iloc[-1]["余额"]
                else:
                    opening_balance = df_sum.iloc[-1]["余额"] if not df_sum.empty else 0
                    month_income = 0
                    month_expense = 0
                    current_balance = opening_balance

                # --- 显示第一排指标：当前状态 ---
                st.subheader(f"📅 {current_year}年{current_month}月 财务概况")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("期初余额", f"¥{opening_balance:,.2f}")
                with col2:
                    st.metric("本月累计收入", f"¥{month_income:,.2f}", delta_color="normal")
                with col3:
                    st.metric("本月累计支出", f"¥{month_expense:,.2f}", delta=f"-{month_expense:,.2f}", delta_color="inverse")

                # --- 显示第二排指标：最终结果 ---
                st.markdown("---")
                col4, col5 = st.columns(2)
                with col4:
                    # 计算本月净头寸
                    net_cash = month_income - month_expense
                    st.metric("本月收支净额", f"¥{net_cash:,.2f}", delta=f"{net_cash:,.2f}")
                with col5:
                    st.metric("当前动态总余额", f"¥{current_balance:,.2f}")

                # 4. 显示原始数据表
                st.markdown("---")
                st.subheader("📋 详细收支流水 (按日期倒序)")
                st.dataframe(df_sum.sort_values('日期', ascending=False), use_container_width=True)
            else:
                st.info("📊 暂无数据，请先完成首笔录入。")
                # --- 增加：数据删除功能 ---
                st.markdown("---")
                with st.expander("🛠️ 数据管理（误填删除）"):
                    st.warning("注意：删除操作不可撤销，请谨慎操作。")
                    delete_id = st.number_input("输入要删除的‘序号’", min_value=1, step=1)
                    if st.button("确认删除该行数据"):
                        try:
                            # 重新读取并过滤掉该序号
                            df_current = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
                            if delete_id in df_current["序号"].values:
                                df_new = df_current[df_current["序号"] != delete_id]
                                # 重新整理序号，保持连续
                                df_new["序号"] = range(1, len(df_new) + 1)
                                conn.update(worksheet="Summary", data=df_new)
                                st.success(f"✅ 序号 {delete_id} 已成功删除，其余序号已自动重排。")
                                st.rerun() # 刷新页面看效果
                            else:
                                st.error("未找到该序号。")
                        except Exception as e:
                            st.error(f"删除失败: {e}")
        except Exception as e:
            st.error(f"计算看板指标时出错: {e}")



