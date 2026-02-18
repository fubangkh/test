import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 页面基础配置 ---
st.set_page_config(page_title="富邦现金流水账", layout="wide")

# --- 权限配置 ---
STAFF_PWD = "123"      # 出纳录入密码
ADMIN_PWD = "123"      # 管理看板密码

# --- 初始化 Google Sheets 连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 侧边栏导航 ---
st.sidebar.title("💰 富邦现金流水账")
role = st.sidebar.radio("选择功能模块", ["数据录入", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")

# --- 逻辑判断 ---

# 1. 数据录入模块
if role == "数据录入":
    if password == STAFF_PWD:
        st.title("📝 日记账录入 (USD)")
        
        # 实时读取当前结余
        df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        # 强制数值化处理
        if not df_latest.empty:
            df_latest["余额"] = pd.to_numeric(df_latest["余额"], errors='coerce').fillna(0)
            last_balance = float(df_latest.iloc[-1]["余额"])
        else:
            last_balance = 0.0
        
        st.info(f"💵 当前系统账面结余：**${last_balance:,.2f}**")

        # 收支类型选择
        trans_type = st.radio("收支类型", ["收入", "支出"], horizontal=True)

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
            with col2:
                amount = st.number_input(f"请输入【{trans_type}】金额 (USD)", min_value=0.0, step=0.01, format="%.2f")
                st.text_input("当前结余 (系统自动计算)", value=f"${last_balance:,.2f}", disabled=True)

            col3, col4 = st.columns(2)
            with col3:
                handler = st.text_input("经手人")
            with col4:
                ref_no = st.text_input("审批/发票编号")
            
            summary = st.text_input("摘要 (必填)")
            note = st.text_area("备注")

            if st.form_submit_button("🚀 提交并同步至云端"):
                if not summary or not handler:
                    st.error("❌ 请填写摘要和经手人！")
                else:
                    try:
                        inc = amount if trans_type == "收入" else 0.0
                        exp = amount if trans_type == "支出" else 0.0
                        new_balance = last_balance + inc - exp
                        
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
                        
                        st.success(f"✅ 录入成功！结余已更新：${new_balance:,.2f}")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"同步失败: {e}")

    elif password == "":
        st.info("💡 请输入录入密码以开启表单")
    else:
        st.error("❌ 密码错误")

# 2. 管理看板模块
elif role == "管理看板":
    if password == ADMIN_PWD:
        st.title("📊 财务决策看板 (USD)")
        
        try:
            df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
            
            if not df_sum.empty:
                # 数据清洗
                for col in ["收入", "支出", "余额"]:
                    df_sum[col] = pd.to_numeric(df_sum[col], errors='coerce').fillna(0)
                
                df_sum['日期'] = pd.to_datetime(df_sum['日期'])
                df_sum = df_sum.sort_values('日期')
                
                now = pd.Timestamp.now()
                df_month = df_sum[(df_sum['日期'].dt.month == now.month) & (df_sum['日期'].dt.year == now.year)]

                # 计算本月指标
                if not df_month.empty:
                    first_row_m = df_month.iloc[0]
                    # ✅ 修复关键公式：期初 = 第一笔余额 - 第一笔收入 + 第一笔支出
                    opening_bal = float(first_row_m["余额"]) - float(first_row_m["收入"]) + float(first_row_m["支出"])
                    m_income = df_month["收入"].sum()
                    m_expense = df_month["支出"].sum()
                    curr_bal = df_month.iloc[-1]["余额"]
                else:
                    opening_bal = float(df_sum.iloc[-1]["余额"]) if not df_sum.empty else 0.0
                    m_income, m_expense = 0.0, 0.0
                    curr_bal = opening_bal

                # 显示指标卡片
                st.subheader(f"📅 {now.year}年{now.month}月 财务概况")
                c1, c2, c3 = st.columns(3)
                c1.metric("本月期初余额", f"${opening_bal:,.2f}")
                c2.metric("本月累计收入", f"${m_income:,.2f}")
                c3.metric("本月累计支出", f"${m_expense:,.2f}", delta=f"-${m_expense:,.2f}", delta_color="inverse")

                st.markdown("---")
                c4, c5 = st.columns(2)
                net_cash = m_income - m_expense
                c4.metric("本月收支净额", f"${net_cash:,.2f}", delta=f"{net_cash:,.2f}")
                c5.metric("当前动态总余额", f"${curr_bal:,.2f}")

                # 流水表展示
                st.markdown("---")
                st.subheader("📋 详细收支流水 (USD)")
                df_display = df_sum.copy()
                df_display['日期'] = df_display['日期'].dt.strftime('%Y-%m-%d')
                
                styled_df = df_display.sort_index(ascending=False).style.format({
                    "收入": "{:.2f}", "支出": "{:.2f}", "余额": "{:.2f}"
                })
                st.dataframe(styled_df, use_container_width=True)

                # 数据管理
                with st.expander("🛠️ 数据管理（误填删除）"):
                    st.warning("⚠️ 删除操作不可撤销。请输入左侧灰色数字索引。")
                    del_idx = st.number_input("行索引", min_value=0, max_value=len(df_sum)-1, step=1)
                    if st.button("确认删除"):
                        df_final = df_sum.drop(del_idx)
                        conn.update(worksheet="Summary", data=df_final)
                        st.success(f"✅ 记录已删除")
                        st.rerun()
            else:
                st.info("📊 暂无数据")

        except Exception as e:
            st.error(f"看板异常: {e}")

    elif password == "":
        st.info("💡 请输入管理密码以查看看板")
    else:
        st.error("❌ 密码错误")
