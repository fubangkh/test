import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置与时区 ---
st.set_page_config(page_title="富邦日记账管理系统", layout="wide")
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 2. 视觉样式增强 (CSS) ---
st.markdown("""
    <style>
    /* 1. 蓝色渐变按钮与动态缩放字体 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0056b3 0%, #007bff 100%) !important;
        color: white !important;
        border: None !important;
        padding: 0.6em 1.2em !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0,123,255,0.3) !important;
        transition: all 0.3s ease !important;
        /* 响应式字体：随窗口宽度缩放，最小14px，最大24px */
        font-size: clamp(14px, 1.2vw, 24px) !important; 
        font-weight: 600 !important;
        width: auto !important;
        min-width: 140px !important;
    }
    
    /* 鼠标悬停动画 */
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,123,255,0.4) !important;
        background: linear-gradient(135deg, #004494 0%, #0069d9 100%) !important;
    }

    /* 2. 调整选择框标签样式 */
    .stSelectbox label {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #31333F !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 辅助函数 ---
def get_now_local():
    return datetime.now(LOCAL_TZ)

def get_now_str():
    return get_now_local().strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=1)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        for c in ["收入", "支出", "余额"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).round(2)
        if "修正时间" not in df.columns:
            df["修正时间"] = ""
        return df
    except:
        return pd.DataFrame()

def get_reference_rate(currency):
    if currency == "USD": return 1.0
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1)
        if res.status_code == 200:
            api = res.json().get("rates", {})
            rates = {"RMB": api.get("CNY", 7.23), "VND": api.get("VND", 25450.0), "HKD": api.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and "🔍" not in str(x)])

# --- 4. 核心：数据录入弹窗 (Dialog) ---
@st.dialog("📝 新增账目录入", width="large")
def entry_dialog():
    df_current = load_all_data()
    last_bal = df_current["余额"].iloc[-1] if not df_current.empty else 0.0
    st.markdown(f"**💡 当前结余：${last_bal:,.2f}**")
    
    # 录入字段布局
    c1, c2 = st.columns([2, 1])
    with c1: val_summary = st.text_input("摘要内容", placeholder="例如：支付工程材料费")
    with c2: val_biz_time = st.datetime_input("业务时间", value=get_now_local())
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1: val_raw_amt = st.number_input("录入金额", min_value=0.0, step=0.01)
    with r2_c2: val_curr = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
    with r2_c3: val_rate = st.number_input("记账汇率", value=float(get_reference_rate(val_curr)), format="%.4f")
    
    acc_list = get_unique_list(df_current, "账户")
    a_sel = st.selectbox("结算账户", ["🔍 选择历史账户"] + acc_list + ["➕ 新增账户"])
    val_acc = st.text_input("✍️ 输入新账户名称") if a_sel == "➕ 新增账户" else a_sel
    
    prop_list = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "期初结存", "内部调拨-转入", "内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    val_prop = st.selectbox("资金性质", prop_list)
    
    val_project = ""
    if val_prop in ["工程收入", "施工收入", "产品销售收入", "服务收入", "网络收入", "预收款", "工程成本", "施工成本"]:
        p_list = get_unique_list(df_current, "客户/项目名称")
        p_sel = st.selectbox("归属项目/客户", ["🔍 请选择"] + p_list + ["➕ 新增项目"])
        val_project = st.text_input("✍️ 输入新项目名称") if p_sel == "➕ 新增项目" else (p_sel if p_sel != "🔍 请选择" else "")

    f1, f2 = st.columns(2)
    with f1:
        h_list = get_unique_list(df_current, "经手人")
        h_sel = st.selectbox("经手人", ["🔍 选择历史人员"] + h_list + ["➕ 新增人员"])
        val_handler = st.text_input("✍️ 输入经手人") if h_sel == "➕ 新增人员" else h_sel
    with f2: val_ref = st.text_input("审批/发票编号")
    val_note = st.text_area("备注详情")

    st.markdown("---")
    # 底部三个核心逻辑按钮
    btn_c1, btn_c2, btn_c3 = st.columns(3)
    
    def save_data():
        if not val_summary or not val_acc or "🔍" in str(val_acc):
            st.error("❌ 摘要、账户均不能为空！")
            return False
        final_usd = round(val_raw_amt / val_rate, 2)
        is_inc = val_prop in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
        inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
        today_sn = "R" + get_now_local().strftime("%Y%m%d")
        sn = today_sn + f"{len(df_current[df_current['录入编号'].astype(str).str.contains(today_sn, na=False)]) + 1:03d}"
        
        row = {
            "录入编号": sn, "提交时间": get_now_str(), "日期": val_biz_time.strftime('%Y-%m-%d %H:%M'),
            "摘要": val_summary, "客户/项目名称": val_project, "账户": val_acc, "资金性质": val_prop, 
            "收入": inc_v, "支出": exp_v, "余额": round(last_bal + inc_v - exp_v, 2), 
            "经手人": val_handler, "备注": f"{val_note} 【原币:{val_raw_amt}{val_curr}】", "审批/发票编号": val_ref, "修正时间": ""
        }
        conn.update(worksheet="Summary", data=pd.concat([df_current, pd.DataFrame([row])], ignore_index=True))
        st.toast(f"✅ 编号 {sn} 已保存", icon="🚀")
        st.cache_data.clear()
        return True

    if btn_c1.button("📥 提交并继续录入", use_container_width=True):
        if save_data(): time.sleep(0.5); st.rerun()
    
    if btn_c2.button("✅ 提交并返回", use_container_width=True):
        if save_data(): time.sleep(0.5); st.rerun()
        
    if btn_c3.button("❌ 取消录入", use_container_width=True):
        st.rerun()

# --- 5. 主页面布局 ---
if "edit_iteration" not in st.session_state:
    st.session_state.edit_iteration = 0

pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if pwd == ADMIN_PWD:
    # 顶部标题与数据录入按钮
    header_c1, header_c2 = st.columns([5, 1])
    with header_c1:
        st.title("📊 财务实时汇总统计")
    with header_c2:
        st.write("<div style='height: 18px;'></div>", unsafe_allow_html=True)
        if st.button("➕ 数据录入", type="primary", use_container_width=True):
            entry_dialog()

    df_latest = load_all_data()
    if not df_latest.empty:
        # 1. 指标卡
        today_str = get_now_local().strftime('%Y-%m-%d')
        df_today = df_latest[df_latest['日期'].astype(str).str.startswith(today_str)]
        m1, m2, m3 = st.columns(3)
        m1.metric("今日总收入", f"${df_today['收入'].sum():,.2f}")
        m2.metric("今日总支出", f"${df_today['支出'].sum():,.2f}")
        m3.metric("当前总结余", f"${df_latest['余额'].iloc[-1]:,.2f}")

        st.divider()

        # 2. 明细标题 与 数据修正选择框 并列
        row_c1, row_c2 = st.columns([2, 1])
        with row_c1:
            st.subheader("📑 原始流水明细")
        with row_c2:
            e_itr = st.session_state.edit_iteration
            target = st.selectbox("🛠️ 数据修正：请选择编号", 
                                 ["-- 请选择 --"] + df_latest["录入编号"].tolist()[::-1], 
                                 key=f"edit_target_{e_itr}")

        # 3. 全宽明细表格
        display_cols = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "修正时间"]
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), 
                     hide_index=True, use_container_width=True, 
                     column_order=display_cols, height=500)

        # 4. 弹出式修正表单
        if target != "-- 请选择 --":
            st.markdown(f"--- \n### 📝 正在修正：{target}")
            old_data = df_latest[df_latest["录入编号"] == target].iloc[0]
            with st.form(f"edit_form_{target}"):
                fe_c1, fe_c2 = st.columns(2)
                with fe_c1:
                    u_date = st.text_input("业务日期", value=str(old_data["日期"]))
                    u_sum = st.text_input("摘要", value=str(old_data["摘要"]))
                    u_acc = st.text_input("结算账户", value=str(old_data["账户"]))
                    u_hand = st.text_input("经手人", value=str(old_data["经手人"]))
                with fe_c2:
                    u_inc = st.number_input("收入 (USD)", value=float(old_data["收入"]), step=0.01)
                    u_exp = st.number_input("支出 (USD)", value=float(old_data["支出"]), step=0.01)
                    u_proj = st.text_input("项目名称", value=str(old_data["客户/项目名称"]))
                    u_note = st.text_area("备注", value=str(old_data["备注"]))
                
                # 修正提交按钮
                eb1, eb2 = st.columns(2)
                if eb1.form_submit_button("💾 确认保存修正", use_container_width=True):
                    idx = df_latest[df_latest["录入编号"] == target].index[0]
                    # 更新字段
                    df_latest.at[idx, "日期"] = u_date
                    df_latest.at[idx, "摘要"] = u_sum
                    df_latest.at[idx, "账户"] = u_acc
                    df_latest.at[idx, "收入"] = round(u_inc, 2)
                    df_latest.at[idx, "支出"] = round(u_exp, 2)
                    df_latest.at[idx, "经手人"] = u_hand
                    df_latest.at[idx, "客户/项目名称"] = u_proj
                    df_latest.at[idx, "备注"] = u_note
                    df_latest.at[idx, "修正时间"] = get_now_str()
                    
                    # 自动重算余额
                    temp_bal = 0
                    for i in range(len(df_latest)):
                        temp_bal = round(temp_bal + df_latest.at[i, "收入"] - df_latest.at[i, "支出"], 2)
                        df_latest.at[i, "余额"] = temp_bal
                    
                    conn.update(worksheet="Summary", data=df_latest)
                    st.session_state.edit_iteration += 1
                    st.balloons(); st.cache_data.clear(); st.rerun()
                
                if eb2.form_submit_button("❌ 放弃并返回", use_container_width=True):
                    st.session_state.edit_iteration += 1
                    st.rerun()
else:
    st.info("🔒 请输入正确密码访问系统后台")
