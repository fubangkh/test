import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 数据处理 ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
        return df
    except:
        return pd.DataFrame()

df_latest = load_all_data()

# --- 3. 界面逻辑 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

# --- 4. 页面 A：数据录入 (略，保持上一版代码逻辑) ---
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务数据录入")
    last_bal = df_latest["余额"].iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | {get_now_str()}")
    
    # ... 此处请保留上一版完整的录入 form 代码 ...
    # 为了保持回复简洁，主要展示汇总页面的列宽优化
    st.write("请参照上一版完整代码中的录入逻辑部分。")

# --- 5. 页面 B：汇总统计 (列宽显示优化版) ---
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 财务实时汇总统计")
    
    if not df_latest.empty:
        # --- A. 当日统计 ---
        today_str = datetime.now(LOCAL_TZ).strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str) == today_str]
        
        t_inc = round(df_today["收入"].sum(), 2)
        t_exp = round(df_today["支出"].sum(), 2)
        total_bal = round(df_latest["余额"].iloc[-1], 2)
        
        st.markdown(f"### 📅 今日概览 ({today_str})")
        m1, m2, m3 = st.columns(3)
        m1.metric("今日总收入", f"${t_inc:,.2f}")
        m2.metric("今日总支出", f"${t_exp:,.2f}", delta_color="inverse")
        m3.metric("总结余 (All)", f"${total_bal:,.2f}")
        
        st.divider()

        # --- B. 账户汇总表 ---
        st.subheader("🏦 本月分账户统计 (USD)")
        this_month = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        acc_summary = []
        unique_accs = sorted([x for x in df_latest["账户"].unique() if x])
        
        for acc in unique_accs:
            df_acc = df_latest[df_latest["账户"] == acc]
            df_before = df_acc[df_acc["日期"].astype(str) < f"{this_month}-01"]
            open_bal = round(df_before["余额"].iloc[-1], 2) if not df_before.empty else 0
            df_m = df_acc[df_acc["日期"].astype(str).str.contains(this_month)]
            acc_summary.append({
                "账户": acc, "期初": open_bal, "收入": df_m["收入"].sum(), "支出": df_m["支出"].sum(), "结余": df_acc["余额"].iloc[-1]
            })
        
        df_s = pd.DataFrame(acc_summary)
        if not df_s.empty:
            total_row = pd.DataFrame([{"账户": "✨ 总计 (Total)", "期初": df_s["期初"].sum(), "收入": df_s["收入"].sum(), "支出": df_s["支出"].sum(), "结余": df_s["结余"].sum()}])
            st.table(pd.concat([df_s, total_row], ignore_index=True).style.format({"期初": "${:,.2f}", "收入": "${:,.2f}", "支出": "${:,.2f}", "结余": "${:,.2f}"}))

        st.divider()

        # --- C. 数据明细列宽优化 (重点更新) ---
        st.subheader("📑 全月流水明细")
        
        # 配置列显示属性
        column_configuration = {
            "录入编号": st.column_config.TextColumn("编号", width="small"),
            "日期": st.column_config.DateColumn("业务日期", format="YYYY-MM-DD", width="small"),
            "摘要": st.column_config.TextColumn("摘要描述", width="large"),
            "客户/项目名称": st.column_config.TextColumn("项目名称", width="medium"),
            "资金性质": st.column_config.TextColumn("资金性质", width="medium"),
            "账户": st.column_config.TextColumn("结算账户", width="small"),
            "收入": st.column_config.NumberColumn("收入 ($)", format="$%.2f", width="small"),
            "支出": st.column_config.NumberColumn("支出 ($)", format="$%.2f", width="small"),
            "余额": st.column_config.NumberColumn("余额 ($)", format="$%.2f", width="small"),
            "经手人": st.column_config.TextColumn("经手人", width="small"),
            "审批/发票编号": st.column_config.TextColumn("审批号", width="small"),
            "备注": st.column_config.TextColumn("备注详情", width="medium"),
            "提交时间": None  # 设置为 None 会在表格中隐藏此列
        }

        st.dataframe(
            df_latest.sort_values("录入编号", ascending=False),
            column_config=column_configuration,
            use_container_width=True,
            hide_index=True
        )

        # --- D. 修正模块 ---
        with st.expander("🛠️ 账目数据修正"):
            target_sn = st.selectbox("选择编号修改", options=["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1])
            if target_sn != "-- 请选择 --":
                old = df_latest[df_latest["录入编号"] == target_sn].iloc[0]
                with st.form("edit_f"):
                    e1, e2, e3 = st.columns(3)
                    u_sum = e1.text_input("摘要", value=str(old["摘要"]))
                    u_inc = e2.number_input("收入", value=float(old["收入"]), step=0.01)
                    u_exp = e3.number_input("支出", value=float(old["支出"]), step=0.01)
                    if st.form_submit_button("💾 保存更新"):
                        idx = df_latest[df_latest["录入编号"] == target_sn].index[0]
                        df_latest.at[idx, "摘要"], df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = u_sum, round(u_inc, 2), round(u_exp, 2)
                        conn.update(worksheet="Summary", data=df_latest)
                        st.cache_data.clear(); st.success("已更新"); time.sleep(1); st.rerun()
else:
    st.warning("🔒 权限验证：请输入正确密码。")
