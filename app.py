import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(page_title="富邦现金日记账", layout="wide")

# --- 权限配置 ---
STAFF_PWD = "123"      
ADMIN_PWD = "123"      

# --- 初始化连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 核心函数：获取参考汇率 ---
def get_reference_rate(df_history, currency):
    now = datetime.now()
    if not df_history.empty and "备注" in df_history.columns:
        this_month_str = now.strftime('%Y-%m')
        df_this_month = df_history[df_history['日期'].astype(str).str.contains(this_month_str)]
        for note in df_this_month['备注'].iloc[::-1]:
            if "【原币" in str(note) and f"{currency}" in str(note):
                try:
                    return float(note.split("汇率：")[1].split("】")[0])
                except:
                    continue
    rates = {"RMB": 7.23, "VND": 25450.0, "HKD": 7.82}
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=3)
        if res.status_code == 200:
            data = res.json().get("rates", {})
            rates = {"RMB": data.get("CNY", 7.23), "VND": data.get("VND", 25450.0), "HKD": data.get("HKD", 7.82)}
    except:
        pass
    return rates.get(currency, 1.0)

# --- 常量定义 ---
# 增加了“期初结转”选项
CORE_BUSINESS_TYPES = ["期初结转", "工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本"]
OTHER_INC = ["网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
OTHER_EXP = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
ALL_FUND_PROPERTIES = (CORE_BUSINESS_TYPES[:6] + OTHER_INC) + (CORE_BUSINESS_TYPES[6:] + OTHER_EXP)

# --- 侧边栏 ---
st.sidebar.title("💰 富邦现金日记账")
role = st.sidebar.radio("功能选择", ["数据录入", "数据修改", "管理看板"])
password = st.sidebar.text_input("请输入访问密码", type="password")

# 读取最新数据
df_latest = conn.read(worksheet="Summary", ttl=0).dropna(how="all")

# --- 功能 1：数据录入 ---
if role == "数据录入" and password == STAFF_PWD:
    st.title("📝 日记账录入")
    last_balance = float(df_latest.iloc[-1]["余额"]) if not df_latest.empty else 0.0
    st.info(f"💵 当前账户总余额：**${last_balance:,.2f}** (USD)")

    c_top1, c_top2 = st.columns([1, 2])
    with c_top1:
        report_date = st.date_input("日期")
    with c_top2:
        summary = st.text_input("摘要 (必填)", placeholder="例如：1月期初余额结转 或 某项目货款")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fund_property = st.selectbox("资金性质", ALL_FUND_PROPERTIES)
        currency = st.selectbox("录入币种", ["USD", "RMB", "VND", "HKD"])
        ref_rate = 1.0 if currency == "USD" else get_reference_rate(df_latest, currency)
        exchange_rate = st.number_input(f"记账汇率", value=float(ref_rate), format="%.4f")
        raw_amount = st.number_input(f"录入金额 ({currency})", min_value=0.0, step=0.01)
        final_usd = raw_amount / exchange_rate if exchange_rate > 0 else 0.0
        st.markdown(f"📊 **折合预估：${final_usd:,.2f} USD**")

    with col2:
        account_type = st.selectbox("结算账户", ["ABA_924_个人户", "ABA_403_个人户", "ABA_313_FB公司户","ICBC_215_AF公司户", "BOC_052_FB公司户", "BOC_063_FB公司户", "BOC_892_瑞尔_FB公司户", "ICBC_854_FB公司户", "CCB_762_人民币_个人户", "BOC_865_人民币_亚堡公司户", "CCB_825_美元_昆仑公司户", "CCB_825_港币_昆仑公司户", "CCB_825_人民币_昆仑公司户", "CMB_002_人民币_科吉公司户", "CMB_032_美元_科吉公司户", "ABA_357_定期", "HUONE_USD", "HUONE_USDT", "现金"])
        project_name = st.text_input("💎 客户/项目名称") if fund_property in CORE_BUSINESS_TYPES else ""
        ref_no = st.text_input("📑 审批/发票编号")
        handlers = sorted([h for h in df_latest["经手人"].unique().tolist() if h]) if not df_latest.empty else []
        h_select = st.selectbox("经手人", ["🔍 选择"] + handlers + ["➕ 新增"])
        new_h = st.text_input("👤 输入新名字") if h_select == "➕ 新增" else ""

    note = st.text_area("备注")

    if st.button("🚀 确认提交"):
        handler = new_h if h_select == "➕ 新增" else h_select
        if not summary or handler in ["🔍 选择", ""]:
            st.error("❌ 摘要和经手人不能为空！")
        else:
            try:
                # 逻辑：期初结转或收入性质 计入 收入列
                inc = final_usd if fund_property in (CORE_BUSINESS_TYPES[:6] + OTHER_INC) else 0.0
                exp = final_usd if fund_property in (CORE_BUSINESS_TYPES[6:] + OTHER_EXP) else 0.0
                auto_note = f"【原币：{raw_amount} {currency}，汇率：{exchange_rate}】 " + (note if note else "")
                
                new_row = {
                    "日期": report_date.strftime('%Y-%m-%d'), 
                    "摘要": summary, 
                    "客户/项目名称": project_name, 
                    "账户": account_type, 
                    "审批/发票编号": ref_no, 
                    "资金性质": fund_property, 
                    "收入": inc, 
                    "支出": exp, 
                    "余额": last_balance + inc - exp, 
                    "经手人": handler, 
                    "备注": auto_note
                }
                updated_df = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True).fillna("")
                conn.update(worksheet="Summary", data=updated_df)
                st.success("✅ 数据已同步至云端！")
                st.rerun()
            except Exception as e:
                st.error(f"失败: {e}")

# --- 功能 2：数据修改 ---
elif role == "数据修改" and password == ADMIN_PWD:
    st.title("🛠️ 数据修正模式")
    if df_latest.empty:
        st.warning("暂无数据")
    else:
        df_with_id = df_latest.copy()
        df_with_id.insert(0, "序号ID", range(len(df_with_id)))
        edit_id = st.number_input("输入要修改的记录序号ID", min_value=0, max_value=len(df_latest)-1, step=1)
        row_to_edit = df_latest.iloc[edit_id]
        
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_date = st.date_input("日期", value=pd.to_datetime(row_to_edit["日期"]))
                new_summary = st.text_input("摘要", value=row_to_edit["摘要"])
                new_prop = st.selectbox("资金性质", ALL_FUND_PROPERTIES, index=ALL_FUND_PROPERTIES.index(row_to_edit["资金性质"]) if row_to_edit["资金性质"] in ALL_FUND_PROPERTIES else 0)
                new_inc = st.number_input("收入 (USD)", value=float(row_to_edit["收入"]))
            with c2:
                new_exp = st.number_input("支出 (USD)", value=float(row_to_edit["支出"]))
                new_acc = st.text_input("账户", value=row_to_edit["账户"])
                new_proj = st.text_input("客户/项目名称", value=row_to_edit["客户/项目名称"])
                new_hand = st.text_input("经手人", value=row_to_edit["经手人"])
                new_note = st.text_area("备注", value=row_to_edit["备注"])
            
            if st.form_submit_button("💾 保存并重算余额"):
                df_latest.at[edit_id, "日期"] = new_date.strftime('%Y-%m-%d')
                df_latest.at[edit_id, "摘要"] = new_summary
                df_latest.at[edit_id, "资金性质"] = new_prop
                df_latest.at[edit_id, "收入"] = new_inc
                df_latest.at[edit_id, "支出"] = new_exp
                df_latest.at[edit_id, "账户"] = new_acc
                df_latest.at[edit_id, "客户/项目名称"] = new_proj
                df_latest.at[edit_id, "经手人"] = new_hand
                df_latest.at[edit_id, "备注"] = new_note
                
                # 全表余额重算逻辑
                cur_bal = 0.0
                for i in range(len(df_latest)):
                    cur_bal += (float(df_latest.at[i, "收入"]) - float(df_latest.at[i, "支出"]))
                    df_latest.at[i, "余额"] = cur_bal
                conn.update(worksheet="Summary", data=df_latest)
                st.success("✅ 修改成功！")
                st.rerun()
        st.dataframe(df_with_id.sort_index(ascending=False), use_container_width=True)

# --- 功能 3：管理看板 ---
elif role == "管理看板" and password == ADMIN_PWD:
    st.title("📊 财务管理看板")
    if not df_latest.empty:
        df_vis = df_latest.copy()
        df_vis['日期'] = pd.to_datetime(df_vis['日期'])
        for col in ["收入", "支出", "余额"]:
            df_vis[col] = pd.to_numeric(df_vis[col], errors='coerce').fillna(0)
        
        # 指标计算
        today = datetime.now()
        first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0)
        
        # 1. 期初结转 (本月1号之前的所有结余)
        df_before = df_vis[df_vis['日期'] < first_day_this_month]
        opening_bal = df_before.iloc[-1]['余额'] if not df_before.empty else 0.0
        
        # 2. 本月收支 (不含期初结转性质的收入，仅统计业务增量)
        df_month = df_vis[df_vis['日期'] >= first_day_this_month]
        # 排除“期初结转”性质，避免月度收入虚高
        month_inc = df_month[df_month['资金性质'] != "期初结转"]['收入'].sum()
        month_exp = df_month['支出'].sum()
        
        # 3. 总结余
        total_bal = df_vis.iloc[-1]['余额']

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📅 本月期初 (USD)", f"${opening_bal:,.2f}")
        m2.metric("📈 本月新增收入", f"${month_inc:,.2f}")
        m3.metric("📉 本月累计支出", f"${month_exp:,.2f}")
        m4.metric("💰 账户当前总余额", f"${total_bal:,.2f}")

        st.divider()
        st.subheader("📝 全历史账目明细")
        df_vis.insert(0, "ID", range(len(df_vis)))
        st.dataframe(df_vis.sort_index(ascending=False), use_container_width=True)
