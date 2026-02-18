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

# --- 4. 数据加载 (核心修复点) ---
@st.cache_data(ttl=5) # 缓存5秒，防止频繁刷新导致KeyError
def load_all_data():
    try:
        # 加载主体表
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        
        # 加载词库表
        try:
            df_cfg = conn.read(worksheet="Config", ttl=0).dropna(how="all")
            shortcuts = df_cfg["快捷摘要"].dropna().tolist()
        except:
            shortcuts = ["房租支付", "工资发放", "内部调拨"]
            
        return df, shortcuts
    except Exception as e:
        return pd.DataFrame(), ["房租支付", "工资发放"]

df_latest, SHORTCUT_SUMMARIES = load_all_data()

# 确保必要列存在，防止报错
required_cols = ["录入编号", "提交时间", "修改时间", "日期", "摘要", "客户/项目名称", "账户", "审批/发票编号", "资金性质", "收入", "支出", "余额", "经手人", "备注"]
for col in required_cols:
    if col not in df_latest.columns:
        df_latest[col] = ""

# --- 5. 辅助函数 ---
def get_reference_rate(currency):
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if res.status_code == 200:
            data = res.json().get("rates", {})
            rates.update({"RMB": data.get("CNY", 7.23), "VND": data.get("VND", 25450.0), "HKD": data.get("HKD", 7.82)})
    except: pass
    return rates.get(currency, 1.0)

def generate_serial_no(df):
    today = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
    ids = df["录入编号"].astype(str).str.strip()
    today_records = ids[ids.str.startswith(today)]
    if today_records.empty: return today + "001"
    next_num = int(today_records.max()[-3:]) + 1
    return today + f"{next_num:03d}"

# --- 6. 侧边栏 ---
st.sidebar.title("🏮 富邦日记账系统")
role = st.sidebar.radio("功能选择", ["数据录入", "汇总统计"])
password = st.sidebar.text_input("请输入密码访问", type="password")

# --- 7. 功能逻辑 ---

# A. 数据录入
if role == "数据录入" and password == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 账户结余：**${last_bal:,.2f}** | 柬埔寨：{get_now_str()}")

    with st.form("entry_form", clear_on_submit=True):
        st.markdown("### 1️⃣ 摘要信息")
        shortcut = st.radio("⚡ 快捷摘要词库", ["自定义"] + SHORTCUT_SUMMARIES, horizontal=True)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            default_val = f"{shortcut} ({datetime.now(LOCAL_TZ).strftime('%m')}月份)" if shortcut != "自定义" else ""
            summary = st.text_input("摘要内容 (必填)", value=default_val)
        with c2:
            report_date = st.date_input("业务日期")

        st.markdown("---")
        st.markdown("### 2️⃣ 金额与账户")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            fund_prop = st.selectbox("资金性质", ["收入", "支出", "内部调拨-转入", "内部调拨-转出", "工程收入", "管理费用"]) # 示例，可补全
            currency = st.selectbox("币种", ["USD", "RMB", "VND", "HKD"])
        with cc2:
            raw_amt = st.number_input("金额", min_value=0.0, step=0.01)
            ex_rate = st.number_input("实时汇率", value=float(get_reference_rate(currency)), format="%.4f")
        with cc3:
            hist_acc = sorted(df_latest["账户"].unique().tolist())
            a_choice = st.selectbox("结算账户", ["🔍 选择"] + hist_acc + ["➕ 新增"])
            new_a = st.text_input("新增账户名")

        st.markdown("---")
        st.markdown("### 3️⃣ 相关方信息")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            projects = sorted(df_latest["客户/项目名称"].unique().tolist())
            p_choice = st.selectbox("项目/客户", ["🔍 选择"] + projects + ["➕ 新增"])
            new_p = st.text_input("新项目名")
        with hc2:
            handlers = sorted(df_latest["经手人"].unique().tolist())
            h_choice = st.selectbox("经手人", ["🔍 选择"] + handlers + ["➕ 新增"])
            new_h = st.text_input("新经手人姓名")
        with hc3:
            ref_no = st.text_input("凭证编号")
            note = st.text_area("备注", height=68)

        if st.form_submit_button("🚀 确认提交录入", use_container_width=True):
            final_a = new_a if a_choice == "➕ 新增" else a_choice
            final_h = new_h if h_choice == "➕ 新增" else h_choice
            final_p = (new_p if p_choice == "➕ 新增" else p_choice) if "选择" not in p_choice else ""
            
            if not summary or "选择" in str(final_a) or "选择" in str(final_h):
                st.error("❌ 摘要、账户和经手人不能为空")
            else:
                final_usd = raw_amt / ex_rate if ex_rate > 0 else 0.0
                serial = generate_serial_no(df_latest)
                # 判定收入支出逻辑（简化版）
                inc = final_usd if "收入" in fund_prop or "转入" in fund_prop else 0.0
                exp = final_usd if "支出" in fund_prop or "转出" in fund_prop else 0.0
                
                row = {
                    "录入编号": serial, "提交时间": get_now_str(), "修改时间": "--",
                    "日期": report_date.strftime('%Y-%m-%d'), "摘要": summary, 
                    "客户/项目名称": final_p, "账户": final_a, "资金性质": fund_prop, 
                    "审批/发票编号": ref_no, "收入": inc, "支出": exp, 
                    "余额": last_bal + inc - exp, "经手人": final_h, "备注": note
                }
                new_df = pd.concat([df_latest, pd.DataFrame([row])], ignore_index=True)
                conn.update(worksheet="Summary", data=new_df)
                st.balloons()
                st.success("✅ 提交成功！")
                time.sleep(1); st.rerun()

# B. 汇总统计 (恢复表格显示)
elif role == "汇总统计" and password == ADMIN_PWD:
    st.title("📊 汇总统计与快速维护")
    
    if not df_latest.empty:
        # 数据整理
        df_v = df_latest.copy()
        for c in ["收入", "支出", "余额"]:
            df_v[c] = pd.to_numeric(df_v[c], errors='coerce').fillna(0)
        
        # 指标看板
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 当前总结余", f"${df_v.iloc[-1]['余额']:,.2f}")
        c2.metric("📥 总收入", f"${df_v['收入'].sum():,.2f}")
        c3.metric("📤 总支出", f"${df_v['支出'].sum():,.2f}")

        # 修改区
        with st.expander("🛠️ 快速维护 (修改选定行)"):
            ids = df_v["录入编号"].astype(str).tolist()[::-1]
            target_id = st.selectbox("选择流水号", ["--请选择--"] + ids)
            if target_id != "--请选择--":
                idx = df_latest[df_latest["录入编号"].astype(str) == target_id].index[0]
                with st.form("edit_box"):
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        new_sum = st.text_input("摘要", value=df_latest.at[idx, "摘要"])
                        new_date = st.date_input("日期", value=pd.to_datetime(df_latest.at[idx, "日期"]))
                    with e2:
                        new_inc = st.number_input("收入", value=float(df_latest.at[idx, "收入"]))
                        new_exp = st.number_input("支出", value=float(df_latest.at[idx, "支出"]))
                    with e3:
                        new_acc = st.text_input("账户", value=df_latest.at[idx, "账户"])
                        new_h = st.text_input("经手人", value=df_latest.at[idx, "经手人"])
                    
                    if st.form_submit_button("保存修改"):
                        df_latest.at[idx, "摘要"], df_latest.at[idx, "日期"] = new_sum, new_date.strftime('%Y-%m-%d')
                        df_latest.at[idx, "收入"], df_latest.at[idx, "支出"] = new_inc, new_exp
                        df_latest.at[idx, "账户"], df_latest.at[idx, "经手人"] = new_acc, new_h
                        df_latest.at[idx, "修改时间"] = get_now_str()
                        # 重算余额
                        bal = 0.0
                        for i in range(len(df_latest)):
                            bal += (float(df_latest.at[i, "收入"]) - float(df_latest.at[i, "支出"]))
                            df_latest.at[i, "余额"] = bal
                        conn.update(worksheet="Summary", data=df_latest)
                        st.success("修改已保存！"); time.sleep(1); st.rerun()

        # 核心：显示数据表格
        st.divider()
        st.markdown("### 📑 全量流水明细")
        # 按编号倒序排，最新的在上面
        st.dataframe(df_v.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("查无数据，请先前往录入模块。")
