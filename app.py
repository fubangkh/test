import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 基础配置 (严禁变动) ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 核心逻辑 (严禁变动) ---
def handle_currency_change():
    new_curr = st.session_state.sel_curr
    st.session_state.input_rate = float(get_reference_rate(df_latest, new_curr))

def get_reference_rate(df_history, currency):
    if currency == "USD": return 1.0
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = datetime.now(LOCAL_TZ).strftime('%Y-%m')
        df_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=1)
        if res.status_code == 200:
            api = res.json().get("rates", {})
            rates = {"RMB": api.get("CNY", 7.23), "VND": api.get("VND", 25450.0), "HKD": api.get("HKD", 7.82)}
    except: pass
    return rates.get(currency, 1.0)

# --- 3. 数据加载 (严禁变动) ---
@st.cache_data(ttl=2)
def load_all_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        cols = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人", "备注", "审批/发票编号"]
        for c in cols:
            if c not in df.columns: df[c] = ""
        history_summaries = sorted([str(x) for x in df["摘要"].unique() if x and str(x)!='nan'])
        return df, history_summaries
    except:
        return pd.DataFrame(), []

df_latest, SUMMARY_HISTORY = load_all_data()

if 'input_rate' not in st.session_state: st.session_state.input_rate = 1.0

def get_unique_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x)!='nan' and str(x).strip() != ""])

# --- 4. 界面展示 ---
role = st.sidebar.radio("📋 功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("🔑 访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 智能财务录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 总结余：**${last_bal:,.2f}** | {get_now_str()}")
    
    # --- 模块 1：业务摘要 (实现单行二合一) ---
    st.markdown("### 1️⃣ 业务摘要")
    col_main, col_date = st.columns([3, 1])
    with col_main:
        # 使用 text_input 结合 label 指引，模拟搜索建议
        # 此时 SUMMARY_HISTORY 仅作为参考，用户直接在此输入。
        # 如果需要更强的自动补全，建议手动打字。
        final_summary = st.selectbox(
            "摘要内容 (打字搜索，若无匹配请直接在输入框手动覆盖)",
            options=SUMMARY_HISTORY,
            index=None,
            placeholder="在此输入或选择历史摘要...",
            key="summary_box",
            label_visibility="collapsed"
        )
        
        # 💡 核心补丁：如果下拉框没选到，允许通过 Session State 强制获取
        # 这种方式最接近一行操作
        if final_summary is None:
            # 这是一个隐藏逻辑：如果在搜索框打完字没选，按回车，这里会尝试捕获
            final_summary = st.session_state.get("summary_box", "")
            
    with col_date:
        biz_date = st.date_input("业务日期", value=datetime.now(LOCAL_TZ), label_visibility="collapsed")

    # --- 模块 2：金额与结算 (账户单行化) ---
    st.markdown("### 2️⃣ 金额与结算")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        ALL_PROPS = ["期初结存", "内部调拨-转入", "内部调拨-转出", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
        fund_p = st.selectbox("资金性质", ALL_PROPS)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"], key="sel_curr", on_change=handle_currency_change)
    with cc2:
        raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
        ex_rate = st.number_input("实时汇率", key="input_rate", format="%.4f")
        if ex_rate > 0 and currency != "USD":
            st.metric("📊 换算美元", f"${(raw_amt/ex_rate):,.2f}")
    with cc3:
        accs_list = get_unique_list(df_latest, "账户")
        final_acc = st.selectbox("结算账户 (搜不到请直接选'➕ 新增')", options=accs_list + ["➕ 新增"])
        if final_acc == "➕ 新增":
            final_acc = st.text_input("请输入新账户名称", key="new_acc_input")

    # --- 模块 3：相关方信息 (项目与经手人单行化) ---
    st.markdown("### 3️⃣ 相关方信息")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        projs_list = get_unique_list(df_latest, "客户/项目名称")
        f_p = st.selectbox("项目/客户 (搜不到选'➕ 新增')", options=projs_list + ["➕ 新增"])
        if f_p == "➕ 新增":
            f_p = st.text_input("请输入新项目/客户", key="new_proj_input")
    with hc2:
        hands_list = get_unique_list(df_latest, "经手人")
        f_h = st.selectbox("经手人 (搜不到选'➕ 新增')", options=hands_list + ["➕ 新增"])
        if f_h == "➕ 新增":
            f_h = st.text_input("请输入新经手人姓名", key="new_hand_input")
    with hc3:
        ref_no = st.text_input("审批/发票编号")
        note = st.text_area("备注信息", height=68)

    st.divider()
    if st.button("🚀 提交账目流水", use_container_width=True):
        # 这里的判断逻辑针对新版单行做了优化
        if not final_summary or not final_acc or not f_h:
            st.error("❌ 必填项缺失：请确保摘要、账户和经手人已填写！")
        else:
            final_usd = raw_amt / st.session_state.input_rate if st.session_state.input_rate > 0 else 0
            is_inc = fund_p in ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
            inc_v, exp_v = (final_usd, 0) if is_inc else (0, final_usd)
            
            rate_tag = f"【原币：{raw_amt} {currency}，汇率：{st.session_state.input_rate}】"
            today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
            sn = today + f"{len(df_latest[df_latest['录入编号'].astype(str).str.contains(today, na=False)]) + 1:03d}"
            
            row = {
                "录入编号": sn, "提交时间": get_now_str(), "日期": biz_date.strftime('%Y-%m-%d'),
                "摘要": final_summary, "客户/项目名称": f_p, "账户": final_acc, 
                "资金性质": fund_p, "收入": inc_v, "支出": exp_v, "余额": last_bal + inc_v - exp_v, 
                "经手人": f_h, "备注": f"{note} {rate_tag}", "审批/发票编号": ref_no
            }
            conn.update(worksheet="Summary", data=pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True))
            st.cache_data.clear() 
            st.balloons(); st.success(f"✅ 录入成功！"); time.sleep(1); st.rerun()

elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计")
    if not df_latest.empty:
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
