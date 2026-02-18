import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(page_title="富邦现金日记账", layout="wide")

# --- 权限/连接 ---
STAFF_PWD = "123"
ADMIN_PWD = "123"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 核心函数：获取参考汇率 ---
def get_rate(df, cur):
    if cur == "USD": return 1.0
    # 尝试从历史备注中寻找本月汇率快照
    if not df.empty and "备注" in df.columns:
        this_month = datetime.now().strftime('%Y-%m')
        df_m = df[df['日期'].astype(str).str.contains(this_month)]
        for note in df_m['备注'].iloc[::-1]:
            if "汇率：" in str(note) and cur in str(note):
                try: return float(note.split("汇率：")[1].split("】")[0])
                except: continue
    # 备选即时汇率
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    return rates.get(cur, 1.0)

# --- 常量定义 ---
CORE_TYPES = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
OTHER_INC = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
OTHER_EXP = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_TYPES = (CORE_TYPES[:5] + OTHER_INC) + (CORE_TYPES[5:] + OTHER_EXP)

# --- 侧边栏 ---
st.sidebar.title("💰 富邦现金日记账")
role = st.sidebar.radio("选择模块", ["数据录入", "管理看板"])
pwd = st.sidebar.text_input("请输入访问密码", type="password")

if role == "数据录入" and pwd == STAFF_PWD:
    st.title("📝 日记账录入")
    df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    last_bal = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
    st.info(f"💵 当前结余：**${last_bal:,.2f}** (USD)")

    # --- 1. 实时互动区 (移出 Form 以支持秒级联动) ---
    c1, c2 = st.columns(2)
    with c1:
        dt = st.date_input("日期")
        prop = st.selectbox("资金性质", ALL_TYPES)
        cur = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
        # 联动汇率
        r_rate = get_rate(df_latest, cur)
        ex_rate = st.number_input(f"记账汇率", value=float(r_rate), format="%.4f")
        # 联动标签：这里直接显示当前币种
        amt = st.number_input(f"录入金额 ({cur})", min_value=0.0, step=0.01)
        # 实时计算预估值
        final_usd = amt / ex_rate if ex_rate > 0 else 0.0
        st.write(f"📊 **当前折合预估：${final_usd:,.2f} USD**")

    with c2:
        acc = st.selectbox("结算账户", ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"])
        proj = st.text_input("💎 客户/项目名称 (必填)") if prop in CORE_TYPES else ""
        ref = st.text_input("📑 审批/发票编号")
        
        hands = sorted([h for h in df_latest["经手人"].unique().tolist() if h]) if not df_latest.empty else []
        h_sel = st.selectbox("经手人", ["🔍 选择"] + hands + ["➕ 新增"])
        new_h = st.text_input("👤 输入新名字") if h_sel == "➕ 新增" else ""

    # --- 2. 提交区 (使用小的 Form 承载提交动作) ---
    with st.form("submit_area", clear_on_submit=True):
        summary = st.text_input("摘要 (必填)")
        note = st.text_area("备注")
        if st.form_submit_button("🚀 提交并同步"):
            h_final = new_h if h_sel == "➕ 新增" else h_sel
            if not summary or h_final in ["🔍 选择", ""]:
                st.error("❌ 摘要和经手人不能为空！")
            elif prop in CORE_TYPES and not proj:
                st.error("❌ 此性质下必须填写客户/项目名称！")
            elif final_usd <= 0:
                st.error("❌ 金额必须大于 0！")
            else:
                try:
                    inc = final_usd if prop in (CORE_TYPES[:5] + OTHER_INC) else 0.0
                    exp = final_usd if prop in (CORE_TYPES[5:] + OTHER_EXP) else 0.0
                    a_note = f"【原币：{amt} {cur}，汇率：{ex_rate}】 " + (note if note else "")
                    
                    new_row = {
                        "日期": dt.strftime('%Y-%m-%d'), "摘要": summary, "客户/项目名称": proj,
                        "账户": acc, "审批/发票编号": ref, "资金性质": prop,
                        "收入": inc, "支出": exp, "余额": last_bal + inc - exp,
                        "经手人": h_final, "备注": a_note
                    }
                    updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                    conn.update(worksheet="Summary", data=updated_df)
                    st.success("✅ 提交成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"失败: {e}")

elif role == "管理看板" and pwd == ADMIN_PWD:
    st.title("📊 财务看板 (USD)")
    df_sum = conn.read(worksheet="Summary", ttl=0).dropna(how="all")
    if not df_sum.empty:
        for c in ["收入", "支出", "余额"]: 
            df_sum[c] = pd.to_numeric(df_sum[c], errors='coerce').fillna(0)
        st.dataframe(df_sum.sort_index(ascending=False), use_container_width=True)
