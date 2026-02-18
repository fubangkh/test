import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import pytz
import time

# --- 基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. 数据安全加载 (解决 KeyError 报错) ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # 强制检查并补齐缺失列，防止图片中的 KeyError
        target_cols = ["录入编号", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "日期"]
        for col in target_cols:
            if col not in df.columns:
                df[col] = ""
        
        # 提取历史摘要 (去重排序)
        history = sorted([str(x) for x in df["摘要"].unique() if x and str(x)!='nan'])
        return df, history
    except:
        return pd.DataFrame(), []

df_latest, SUMMARY_HISTORY = load_all_data()

# --- 2. 界面展示 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 财务录入")
    
    # 获取余额
    try:
        last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1]
    except:
        last_bal = 0.0

    st.info(f"💵 当前结余：**${last_bal:,.2f}**")

    # --- 模块 1：业务摘要 (二合一精简版) ---
    st.markdown("### 1️⃣ 业务摘要")
    col1, col2 = st.columns([3, 1])
    with col1:
        # 这一行就是你想要的：既能输入又能搜
        # 注意：如果输入新词，直接在框里打完字，不要选列表即可
        summary_input = st.selectbox(
            "摘要内容 (打字可搜索历史，输入新内容请直接打字)",
            options=SUMMARY_HISTORY,
            index=None,
            placeholder="输入关键词如 '正道'...",
            help="输入完新摘要后请确保光标移开或按回车确认",
            label_visibility="collapsed" # 隐藏标签让界面更紧凑
        )
    with col2:
        biz_date = st.date_input("业务日期", label_visibility="collapsed")

    # --- 模块 2 & 3 简化合并 ---
    st.markdown("### 2️⃣ 财务明细")
    c1, c2, c3 = st.columns(3)
    with c1:
        fund_p = st.selectbox("资金性质", ["施工收入", "管理费用", "往来款", "期初结存"])
        currency = st.selectbox("币种", ["USD", "RMB", "VND"])
    with c2:
        raw_amt = st.number_input("原币金额", min_value=0.0)
        rate = st.number_input("实时汇率", value=1.0, format="%.4f")
    with c3:
        accs = sorted([str(x) for x in df_latest["账户"].unique() if x and str(x)!='nan'])
        final_acc = st.selectbox("结算账户", options=accs + ["➕ 新增"])
        if final_acc == "➕ 新增":
            final_acc = st.text_input("输入新账户名")

    # 提交逻辑
    if st.button("🚀 确认提交", use_container_width=True):
        if not summary_input:
            st.error("❌ 摘要不能为空！")
        else:
            # 计算金额
            usd_amt = raw_amt / rate if rate > 0 else 0
            is_inc = "收入" in fund_p or "结存" in fund_p
            inc, exp = (usd_amt, 0) if is_inc else (0, usd_amt)
            
            # 生成编号
            sn = datetime.now(LOCAL_TZ).strftime("R%Y%m%d%H%M%S")
            
            new_row = {
                "录入编号": sn, "日期": biz_date.strftime("%Y-%m-%d"),
                "摘要": summary_input, "余额": last_bal + inc - exp,
                "收入": inc, "支出": exp, "账户": final_acc, "资金性质": fund_p
            }
            
            # 更新数据
            new_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(worksheet="Summary", data=new_df)
            st.cache_data.clear()
            st.success("✅ 提交成功！")
            time.sleep(1)
            st.rerun()

elif role == "汇总统计":
    st.dataframe(df_latest)
