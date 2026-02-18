import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import time
import pytz

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="富邦日记账系统", layout="wide")

# --- 2. 权限与时区配置 ---
STAFF_PWD = "123"
ADMIN_PWD = "123"
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_now_str():
    return datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

# --- 3. 初始化连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. 核心汇率逻辑 (精准还原) ---
def get_reference_rate(df_history, currency):
    """还原之前的逻辑：优先查本月备注汇率，查不到则调API，最后给保底值"""
    if currency == "USD": return 1.0
    now_local = datetime.now(LOCAL_TZ)
    
    # A. 优先从本月历史记录的“备注”中提取汇率
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now_local.strftime('%Y-%m')
        df_this_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_this_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try: 
                    return float(note.split("汇率：")[1].split("】")[0])
                except: continue
                
    # B. 备选方案：实时 API 抓取
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=2)
        if res.status_code == 200:
            api_rates = res.json().get("rates", {})
            rates = {
                "RMB": api_rates.get("CNY", 7.23), 
                "VND": api_rates.get("VND", 25450.0), 
                "HKD": api_rates.get("HKD", 7.82)
            }
    except: pass
    return rates.get(currency, 1.0)

# --- 5. 数据加载与列表安全处理 ---
def load_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        try:
            df_cfg = conn.read(worksheet="Config", ttl=0).dropna(how="all")
            shortcuts = [s for s in df_cfg["快捷摘要"].dropna().tolist() if s]
        except: shortcuts = ["房租支付", "工资发放", "内部调拨"]
        return df, shortcuts
    except:
        return pd.DataFrame(), ["房租支付", "工资发放"]

df_latest, SHORTCUT_SUMMARIES = load_data()

def get_safe_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x).lower() != 'none'])

# --- 6. 资金性质常量 (完全一致) ---
INC_PROPS = ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_PROPS = ["内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPS = INC_PROPS + EXP_PROPS

# --- 7. 功能逻辑 ---
role = st.sidebar.radio("功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    
    with st.form("entry_form"):
        st.subheader("1️⃣ 摘要与日期")
        shortcut = st.radio("⚡ 快捷摘要", ["自定义"] + SHORTCUT_SUMMARIES, horizontal=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            default_s = f"{shortcut} ({datetime.now(LOCAL_TZ).strftime('%m')}月)" if shortcut != "自定义" else ""
            summary = st.text_input("摘要内容 (必填)", value=default_s)
        with c2:
            biz_date = st.date_input("业务日期")

        st.subheader("2️⃣ 金额账户 (精准汇率版)")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            fund_p = st.selectbox("资金性质", ALL_FUND_PROPS)
            currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
        with cc2:
            raw_amt = st.number_input("原币金额", min_value=0.0, step=0.01)
            # 还原之前的汇率自动匹配功能
            ex_rate = st.number_input("实时汇率", value=float(get_reference_rate(df_latest, currency)), format="%.4f")
        with cc3:
            accs = get_safe_list(df_latest, "账户")
            a_sel = st.selectbox("结算账户", ["🔍 选择"] + accs + ["➕ 新增"])
            new_a = st.text_input("新账户名")

        st.subheader("3️⃣ 相关方信息")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            projs = get_safe_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("项目/客户", ["🔍 选择"] + projs + ["➕ 新增"])
            new_p = st.text_input("新项目名")
        with hc2:
            hands = get_safe_list(df_latest, "经手人")
            h_sel = st.selectbox("经手人", ["🔍 选择"] + hands + ["➕ 新增"])
            new_h = st.text_input("新经手人姓名")
        with hc3:
            ref_no = st.text_input("凭证/审批编号")
            note = st.text_area("备注 (汇率会自动记录在此)", height=68)

        if st.form_submit_button("🚀 确认提交录入", use_container_width=True):
            final_a = new_a if a_sel == "➕ 新增" else a_sel
            final_h = new_h if h_sel == "➕ 新增" else h_sel
            final_p = (new_p if p_sel == "➕ 新增" else p_sel) if "选择" not in str(p_sel) else ""
            
            if not summary or "选择" in str(final_a) or "选择" in str(final_h):
                st.error("❌ 摘要、账户和经手人不能为空！")
            else:
                final_usd = raw_amt / ex_rate if ex_rate > 0 else 0.0
                inc = final_usd if fund_p in INC_PROPS else 0.0
                exp = final_usd if fund_p in EXP_PROPS else 0.0
                
                # 记录详细备注以供下次抓取汇率
                rate_note = f"【原币金额：{raw_amt} {currency}，汇率：{ex_rate}】"
                full_note = f"{note} {rate_note}" if note else rate_note
                
                # 生成编号
                today_prefix = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
                sn = today_prefix + f"{len(df_latest[df_latest['录入编号'].str.contains(today_prefix, na=False)]) + 1:03d}"
                
                new_row = {
                    "录入编号": sn, "提交时间": get_now_str(), "修改时间": "--",
                    "日期": biz_date.strftime('%Y-%m-%d'), "摘要": summary, "客户/项目名称": final_p,
                    "账户": final_a, "资金性质": fund_p, "收入": inc, "支出": exp,
                    "余额": last_bal + inc - exp, "经手人": final_h, "备注": full_note, "审批/发票编号": ref_no
                }
                updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Summary", data=updated_df)
                st.balloons(); st.success("✅ 录入完成！汇率已记录"); time.sleep(1); st.rerun()

elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计与明细")
    if not df_latest.empty:
        for c in ["收入", "支出", "余额"]: df_latest[c] = pd.to_numeric(df_latest[c], errors='coerce').fillna(0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("结余 (USD)", f"${df_latest['余额'].iloc[-1]:,.2f}")
        m2.metric("累计收入", f"${df_latest['收入'].sum():,.2f}")
        m3.metric("累计支出", f"${df_latest['支出'].sum():,.2f}")

        with st.expander("🛠️ 快速修改"):
            target = st.selectbox("流水号", ["--"] + df_latest["录入编号"].tolist()[::-1])
            if target != "--":
                idx = df_latest[df_latest["录入编号"] == target].index[0]
                with st.form("edit"):
                    e_sum = st.text_input("摘要", value=df_latest.at[idx, "摘要"])
                    e_inc = st.number_input("收入", value=float(df_latest.at[idx, "收入"]))
                    e_exp = st.number_input("支出", value=float(df_latest.at[idx, "支出"]))
                    if st.form_submit_button("保存"):
                        df_latest.at[idx, "摘要"] = e_sum
                        df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = e_inc, e_exp
                        # 重算余额
                        b = 0.0
                        for i in range(len(df_latest)):
                            b += (df_latest.at[i, "收入"] - df_latest.at[i, "支出"])
                            df_latest.at[i, "余额"] = b
                        conn.update(worksheet="Summary", data=df_latest)
                        st.success("已保存并重算"); time.sleep(1); st.rerun()

        st.divider()
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
