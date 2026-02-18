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

# --- 4. 数据加载与容错处理 ---
def load_data():
    try:
        df = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
        df.columns = df.columns.str.strip()
        # 补全缺失列
        required = ["录入编号", "日期", "摘要", "客户/项目名称", "账户", "资金性质", "收入", "支出", "余额", "经手人"]
        for col in required:
            if col not in df.columns: df[col] = ""
        
        # 加载配置词库
        try:
            df_cfg = conn.read(worksheet="Config", ttl=0).dropna(how="all")
            shortcuts = [s for s in df_cfg["快捷摘要"].dropna().tolist() if s]
        except:
            shortcuts = ["房租支付", "工资发放", "内部调拨"]
        return df, shortcuts
    except:
        return pd.DataFrame(), ["房租支付", "工资发放"]

df_latest, SHORTCUT_SUMMARIES = load_data()

# 安全提取唯一列表函数 (修复排序崩溃问题)
def get_safe_list(df, col_name):
    if df.empty or col_name not in df.columns: return []
    return sorted([str(x) for x in df[col_name].unique() if x and str(x).lower() != 'none'])

# --- 5. 核心常量：资金性质 (已恢复并对齐) ---
INC_PROPS = ["期初结存", "内部调拨-转入", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
EXP_PROPS = ["内部调拨-转出", "工程成本", "施工成本", "网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPS = INC_PROPS + EXP_PROPS

# --- 6. 辅助功能 ---
def get_rate(curr):
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=2)
        if res.status_code == 200: rates.update(res.json().get("rates", {}))
    except: pass
    return rates.get(curr, 1.0)

# --- 7. 侧边栏 ---
st.sidebar.title("🏮 富邦日记账系统")
role = st.sidebar.radio("功能选择", ["数据录入", "汇总统计"])
pwd = st.sidebar.text_input("访问密码", type="password")

# --- 8. 业务逻辑 ---

# A. 数据录入
if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 数据录入")
    last_bal = pd.to_numeric(df_latest["余额"], errors='coerce').iloc[-1] if not df_latest.empty else 0.0
    st.info(f"💵 账户总结余：**${last_bal:,.2f}** | 柬埔寨时间：{get_now_str()}")
    
    with st.form("entry_form"):
        st.subheader("1️⃣ 摘要信息")
        shortcut = st.radio("⚡ 快捷摘要词库", ["自定义"] + SHORTCUT_SUMMARIES, horizontal=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            default_s = f"{shortcut} ({datetime.now(LOCAL_TZ).strftime('%m')}月)" if shortcut != "自定义" else ""
            summary = st.text_input("摘要内容 (必填)", value=default_s)
        with c2:
            biz_date = st.date_input("业务日期")

        st.subheader("2️⃣ 金额账户")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            fund_p = st.selectbox("资金性质", ALL_FUND_PROPS)
            curr = st.selectbox("币种", ["USD", "RMB", "VND", "HKD"])
        with cc2:
            amt = st.number_input("原币金额", min_value=0.0, step=0.01)
            rate = st.number_input("实时汇率", value=float(get_rate(curr)), format="%.4f")
        with cc3:
            accs = get_safe_list(df_latest, "账户")
            a_sel = st.selectbox("结算账户", ["🔍 请选择"] + accs + ["➕ 新增"])
            new_a = st.text_input("新账户名 (仅在选新增时填写)")

        st.subheader("3️⃣ 相关方信息")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            projs = get_safe_list(df_latest, "客户/项目名称")
            p_sel = st.selectbox("项目名称", ["🔍 请选择历史"] + projs + ["➕ 新增项目"])
            new_p = st.text_input("新项目名")
        with hc2:
            hands = get_safe_list(df_latest, "经手人")
            h_sel = st.selectbox("经手人", ["🔍 请选择历史"] + hands + ["➕ 新增经手人"])
            new_h = st.text_input("新姓名")
        with hc3:
            ref_no = st.text_input("凭证/审批编号")
            note = st.text_area("备注信息", height=68)

        if st.form_submit_button("🚀 确认提交录入", use_container_width=True):
            final_a = new_a if a_sel == "➕ 新增" else a_sel
            final_h = new_h if h_sel == "➕ 新增经手人" else h_sel
            final_p = (new_p if p_sel == "➕ 新增项目" else p_sel) if "请选择" not in str(p_sel) else ""
            
            if not summary or "请选择" in str(final_a) or "请选择" in str(final_h):
                st.error("❌ 摘要、账户和经手人不能为空！")
            else:
                usd_amt = amt / rate if rate > 0 else 0
                is_inc = fund_p in INC_PROPS
                inc_val = usd_amt if is_inc else 0
                exp_val = usd_amt if not is_inc else 0
                
                # 生成编号
                today_prefix = "R" + datetime.now(LOCAL_TZ).strftime("%Y%m%d")
                sn = today_prefix + f"{len(df_latest[df_latest['录入编号'].str.contains(today_prefix, na=False)]) + 1:03d}"
                
                new_row = {
                    "录入编号": sn, "提交时间": get_now_str(), "修改时间": "--",
                    "日期": biz_date.strftime('%Y-%m-%d'), "摘要": summary, "客户/项目名称": final_p,
                    "账户": final_a, "资金性质": fund_p, "收入": inc_val, "支出": exp_val,
                    "余额": last_bal + inc_val - exp_val, "经手人": final_h, "备注": note, "审批/发票编号": ref_no
                }
                updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Summary", data=updated_df)
                st.balloons(); st.success("✅ 录入成功！"); time.sleep(1); st.rerun()

# B. 汇总统计 (恢复并增强)
elif role == "汇总统计" and pwd == ADMIN_PWD:
    st.title("📊 汇总统计明细")
    if not df_latest.empty:
        # 强制数值化
        for c in ["收入", "支出", "余额"]:
            df_latest[c] = pd.to_numeric(df_latest[c], errors='coerce').fillna(0)
        
        # 指标卡
        m1, m2, m3 = st.columns(3)
        m1.metric("总结余 (USD)", f"${df_latest['余额'].iloc[-1]:,.2f}")
        m2.metric("累计收入", f"${df_latest['收入'].sum():,.2f}")
        m3.metric("累计支出", f"${df_latest['支出'].sum():,.2f}")

        # 修改器
        with st.expander("🛠️ 快速维护 (修改选定行)"):
            target = st.selectbox("请选择要修改的流水号", ["--请选择--"] + df_latest["录入编号"].tolist()[::-1])
            if target != "--请选择--":
                row_idx = df_latest[df_latest["录入编号"] == target].index[0]
                with st.form("quick_edit"):
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        e_sum = st.text_input("摘要", value=df_latest.at[row_idx, "摘要"])
                        e_date = st.date_input("日期", value=pd.to_datetime(df_latest.at[row_idx, "日期"]))
                    with e2:
                        e_inc = st.number_input("收入 (USD)", value=float(df_latest.at[row_idx, "收入"]))
                        e_exp = st.number_input("支出 (USD)", value=float(df_latest.at[row_idx, "支出"]))
                    with e3:
                        e_acc = st.text_input("账户", value=df_latest.at[row_idx, "账户"])
                        e_hand = st.text_input("经手人", value=df_latest.at[row_idx, "经手人"])
                    
                    if st.form_submit_button("💾 保存修改并重算余额"):
                        df_latest.at[row_idx, "摘要"] = e_sum
                        df_latest.at[row_idx, "日期"] = e_date.strftime('%Y-%m-%d')
                        df_latest.at[row_idx, "收入"], df_latest.at[row_idx, "支出"] = e_inc, e_exp
                        df_latest.at[row_idx, "账户"], df_latest.at[row_idx, "经手人"] = e_acc, e_hand
                        df_latest.at[row_idx, "修改时间"] = get_now_str()
                        # 重算全表余额
                        running_bal = 0.0
                        for i in range(len(df_latest)):
                            running_bal += (df_latest.at[i, "收入"] - df_latest.at[i, "支出"])
                            df_latest.at[i, "余额"] = running_bal
                        conn.update(worksheet="Summary", data=df_latest)
                        st.success("✅ 修改已保存！"); time.sleep(1); st.rerun()

        st.divider()
        st.markdown("### 📑 全量流水清单")
        st.dataframe(df_latest.sort_values("录入编号", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("暂无流水数据。")
