import streamlit as st
import pandas as pd
import pytz
import time
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 全局配置 (必须放在最前面) ---
st.set_page_config(page_title="富邦日记账", layout="wide")

# --- 2. 核心定义 (时区定义，全局可用) ---
LOCAL_TZ = pytz.timezone('Asia/Phnom_Penh')

# --- 3. 登录拦截系统 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    from login import show_login_page
    show_login_page()
    st.stop()

# --- 4. 登录成功后的主程序逻辑 ---
st.title("💰 富邦日记账")
if st.sidebar.button("安全退出"):
    st.session_state.logged_in = False
    st.rerun()

# 数据库连接
conn = st.connection("gsheets", type=GSheetsConnection)

st.markdown("""
    <style>
    /* 1. 确认提交按钮：默认是清爽的浅绿灰色 */
    div.stButton > button[kind="primary"] {
        background-color: #1F883D; /* 默认：清爽绿 */
        color: white;
        border: none;
        border-radius: 8px;        /* 圆角稍微圆润一点，更现代 */
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    /* 2. 悬停状态：变成明亮的绿色，并有一点点阴影 */
    div.stButton > button[kind="primary"]:hover {
        background-color: #66BB6A; /* 悬停：亮绿 */
        color: white;
        border-color: #66BB6A;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* 增加一点点悬浮阴影感 */
    }

    /* 3. 取消返回按钮：极简浅灰色 */
    div.stButton > button[kind="secondary"] {
        background-color: #F8F9FA; 
        color: #444;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }

    /* 4. 取消按钮悬停：稍微深一点的灰 */
    div.stButton > button[kind="secondary"]:hover {
        background-color: #EEEEEE;
        border-color: #CCCCCC;
        color: #000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 核心功能：实时汇率 ---
@st.cache_data(ttl=3600)
def get_live_rates():
    default_rates = {"USD": 1.0, "CNY": 6.91, "VND": 26000.0, "HKD": 7.82, "IDR": 16848.0}
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if response.status_code == 200:
            rates = response.json().get("rates", {})
            return {"USD": 1.0, "CNY": rates.get("CNY", 6.91), "VND": rates.get("VND", 26000), "HKD": rates.get("HKD", 7.82), "IDR": rates.get("IDR", 16848.0)}
    except: pass
    return default_rates

# --- 3. 数据连接 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/1AC572Eq96yIF9it1xCJQAOrxjEEnskProsLmifK3DAs/export?format=csv&gid=0"
    try:
        df = pd.read_csv(csv_url)
        df = df.dropna(how="all")
        
        # 强制将这些涉及计算的列转为数字，空值填 0
        numeric_cols = ['实际金额','收入', '支出', '余额'] # 根据你表格的实际列名添加
        for col in numeric_cols:
            if col in df.columns:
                # 转换前先去掉逗号（Google Sheets 导出的 CSV 有时会带 379,167.21 里的逗号）
                if df[col].dtype == 'object':
                    df[col] = df[col].str.replace(',', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        df = df.fillna("")
        pd.options.display.float_format = '{:,.2f}'.format
        
        return df
    except Exception as e:
        st.error(f"加载失败: {e}")
        return pd.DataFrame()

# get_dynamic_options 函数保持不变，它现在可以完美兼容上面返回的 df
def get_dynamic_options(df, column_name):
    try:
        if not df.empty and column_name in df.columns:
            # 这里的 x 已经是字符串了，因为上面做了 fillna("")
            raw_list = [str(x).strip() for x in df[column_name].unique() if x]
            clean_options = sorted([
                x for x in raw_list 
                if x and x not in ["--", "-", "nan", "None", "0", "0.0"] and "➕" not in x
            ])
            return ["-- 请选择 --"] + clean_options + ["➕ 新增..."]
    except:
        pass
    return ["-- 请选择 --", "➕ 新增..."]
    
   # --- 4. 录入模块 (回归稳定版) ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog():
    # --- A. 内部常量定义 ---
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
    INC_OTHER = ["期初调整","网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]

    df = load_data()
    live_rates = get_live_rates()
    
    # 顶部结余显示
    current_balance = df['余额'].iloc[-1] if not df.empty else 0
    st.write(f"💡 当前总结余: **${current_balance:,.2f}**")
    
    # 1. 摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容", placeholder="请输入流水说明")
    val_time = c2.date_input("业务时间", value=datetime.now(LOCAL_TZ)) # 建议用 date_input 更稳
    
    # 2. 金额、币种、汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("原币金额", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("原币币种", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f")
    
    # 实时换算显示
    converted_usd = round(val_amt / val_rate, 2) if val_rate != 0 else 0
    st.info(f"💰 换算后金额：$ {converted_usd:,.2f} USD")
    
    st.divider() 

    # 3. 性质与发票
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("📑 审批/发票单号 (必填)")
    val_prop = r4_c2.selectbox("资金性质", ALL_PROPS)
    
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BIZ

    # 4. 账户与经手人
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户", options=get_dynamic_options(df, "结算账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户", options=get_dynamic_options(df, "结算账户"))
        val_hand = "系统自动结转"
        val_acc = "资金结转" # 预设值避免变量缺失
    else:
        sel_acc = r3_c1.selectbox("结算账户", options=get_dynamic_options(df, "结算账户"))
        val_acc = r3_c1.text_input("✍️ 录入新账户") if sel_acc == "➕ 新增..." else sel_acc
        sel_hand = r3_c2.selectbox("经手人", options=get_dynamic_options(df, "经手人"))
        val_hand = r3_c2.text_input("✍️ 录入新姓名") if sel_hand == "➕ 新增..." else sel_hand

    # --- 5. 客户或项目信息 (回归稳定逻辑) ---
    proj_label = "📍 客户/项目信息 (必填)" if is_req else "客户/项目信息 (选填)"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目信息"))

    # 如果选了新增，或者还没选，显示输入框。
    # 提交时 val_proj 将获取输入框中的最终文字。
    if sel_proj == "➕ 新增..." or sel_proj == "-- 请选择 --":
        val_proj = st.text_input("✍️ 录入新客户/项目", key="k_new_proj_input", placeholder="请输入项目名称...")
    else:
        val_proj = sel_proj

    val_note = st.text_area("备注")

    # --- 6. 核心提交逻辑函数 ---
    def validate_and_submit():
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return False
        if val_amt <= 0:
            st.error("⚠️ 金婚必须大于 0！")
            return False
        if not val_inv or val_inv.strip() == "":
            st.error("⚠️ 请输入【审批/发票单号】！")
            return False
        
        # 项目校验
        if is_req and (not val_proj or val_proj.strip() in ["", "-- 请选择 --"]):
            st.error(f"⚠️ 【{val_prop}】必须关联有效项目！")
            return False

        try:
            # 重新加载最新数据，防止 full_df 未定义
            current_df = load_data() 
            now_dt = datetime.now(LOCAL_TZ)
            now_ts = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            today_str = now_dt.strftime("%Y%m%d")

            # 编号生成
            today_mask = current_df['录入编号'].astype(str).str.contains(f"R{today_str}", na=False)
            today_records = current_df[today_mask]
            start_num = (int(str(today_records['录入编号'].iloc[-1])[-3:]) + 1) if not today_records.empty else 1

            new_rows = []
            def create_row(offset, s, p, a, i, pr, raw_v, raw_c, inc, exp, h, n):
                sn = f"R{today_str}{(start_num + offset):03d}"
                return [sn, now_ts, now_ts, s, p, a, i, pr, round(float(raw_v), 2), raw_c, round(float(inc), 2), round(float(exp), 2), 0, h, n]

            if is_transfer:
                new_rows.append(create_row(0, f"【转出】{val_sum}", "内部调拨", val_acc_from, val_inv, val_prop, val_amt, val_curr, 0, converted_usd, val_hand, val_note))
                new_rows.append(create_row(1, f"【转入】{val_sum}", "内部调拨", val_acc_to, val_inv, val_prop, val_amt, val_curr, converted_usd, 0, val_hand, val_note))
            else:
                inc_val = converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0
                exp_val = converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0
                new_rows.append(create_row(0, val_sum, val_proj, val_acc, val_inv, val_prop, val_amt, val_curr, inc_val, exp_val, val_hand, val_note))

            new_df = pd.DataFrame(new_rows, columns=current_df.columns)
            full_df = pd.concat([current_df, new_df], ignore_index=True)
            
            # 数值计算
            for col in ['收入', '支出']:
                full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

            full_df['余额'] = (full_df['收入'].cumsum() - full_df['支出'].cumsum())

            # 格式化存入
            for col in ['收入', '支出', '余额']:
                full_df[col] = full_df[col].apply(lambda x: "{:.2f}".format(float(x)))
            
            conn.update(worksheet="Summary", data=full_df)
            return True
        except Exception as e:
            st.error(f"❌ 写入失败: {e}")
            return False

    # --- 7. 底部按钮区域 ---
    st.divider()
    col_sub, col_can = st.columns(2)

    if col_sub.button("🚀 确认提交", type="primary", use_container_width=True):
        with st.spinner("正在同步至云端..."):
            if validate_and_submit():
                st.toast("记账成功！数据已实时同步", icon="💰")
                st.balloons()
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

    if col_can.button("🗑️ 取消返回", use_container_width=True):
        st.rerun()

# --- 5. 数据修正模块 (升级版) ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(target_id, full_df, conn):
    # 1. 准备常量与原始数据
    CORE_BIZ = ["工程收入", "施工收入", "产品销售收入", "服务收入", "预收款", "工程成本", "施工成本", "产品销售支出"]
    INC_OTHER = ["期初调整","网络收入", "其他收入", "借款", "往来款收回", "押金收回"]
    EXP_OTHER = ["网络成本", "管理费用", "差旅费", "工资福利", "往来款支付", "押金支付", "归还借款"]
    ALL_PROPS = CORE_BIZ[:5] + INC_OTHER + CORE_BIZ[5:] + EXP_OTHER + ["资金结转"]
    
    # 锁定当前行
    old = full_df[full_df["录入编号"] == target_id].iloc[0]
    live_rates = get_live_rates()
    
    st.info(f"正在修正记录：`{target_id}`")
    
    # --- 第一部分：基础信息 ---
    c1, c2 = st.columns(2)
    with c1:
        # 💡 修正：兼容多种可能的日期列名，确保显示
        raw_date = old.get("提交时间") or old.get("日期") or "无日期"
        st.text_input("业务日期 (系统锁定)", value=str(raw_date)[:10], disabled=True)
    u_sum = c2.text_input("摘要内容", value=str(old.get("摘要", "")))
    
    # --- 第二部分：金额与币种 ---
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    u_ori_amt = r2_c1.number_input("原币金额", value=float(old.get("实际金额", 0.0)), step=100.0)
    
    curr_list = list(live_rates.keys())
    curr_val = old.get("实际币种", "USD")
    u_curr = r2_c2.selectbox("原币币种", curr_list, index=curr_list.index(curr_val) if curr_val in curr_list else 0)
    
    default_rate = float(live_rates.get(u_curr, 1.0))
    u_rate = r2_c3.number_input("汇率", value=default_rate, format="%.4f")
    
    u_usd_val = round(u_ori_amt / u_rate, 2) if u_rate != 0 else 0
    st.info(f"💰 折算后金额：$ {u_usd_val:,.2f} USD")

    st.divider()

    # --- 第三部分：性质与发票 ---
    r4_c1, r4_c2 = st.columns(2)
    u_inv = r4_c1.text_input("审批/发票单号", value=str(old.get("审批/发票单号", "")))
    
    prop_val = old.get("资金性质", "")
    p_idx = ALL_PROPS.index(prop_val) if prop_val in ALL_PROPS else 0
    u_prop = r4_c2.selectbox("资金性质", ALL_PROPS, index=p_idx)

    # --- 第四部分：账户与经手人 (修正为下拉模式) ---
    r3_c1, r3_c2 = st.columns(2)
    
    # 账户
    acc_options = get_dynamic_options(full_df, "结算账户")
    curr_acc = old.get("结算账户", "")
    sel_acc = r3_c1.selectbox("结算账户", options=acc_options, index=acc_options.index(curr_acc) if curr_acc in acc_options else 0)
    u_acc = r3_c1.text_input("✍️ 录入新账户") if sel_acc == "➕ 新增..." else sel_acc

    # 经手人
    hand_options = get_dynamic_options(full_df, "经手人")
    curr_hand = old.get("经手人", "")
    sel_hand = r3_c2.selectbox("经手人", options=hand_options, index=hand_options.index(curr_hand) if curr_hand in hand_options else 0)
    u_hand = r3_c2.text_input("✍️ 录入新姓名") if sel_hand == "➕ 新增..." else sel_hand

    # --- 第五部分：项目信息 (修正为下拉模式) ---
    proj_options = get_dynamic_options(full_df, "客户/项目信息")
    curr_proj = old.get("客户/项目信息", "")
    sel_proj = st.selectbox("客户/项目信息", options=proj_options, index=proj_options.index(curr_proj) if curr_proj in proj_options else 0)
    
    if sel_proj == "➕ 新增..." or sel_proj == "-- 请选择 --":
        u_proj = st.text_input("✍️ 录入新客户/项目", placeholder="项目名称...")
    else:
        u_proj = sel_proj

    u_note = st.text_area("备注详情", value=str(old.get("备注", "")))

    st.divider()
    sv, ex = st.columns(2)
    if sv.button("💾 确认保存修正", type="primary", use_container_width=True):
        if not u_sum.strip():
            st.error("摘要不能为空")
        else:
            try:
                new_df = full_df.copy()
                idx = new_df[new_df["录入编号"] == target_id].index[0]
                new_df.at[idx, "修改时间"] = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
                new_df.at[idx, "摘要"] = u_sum
                new_df.at[idx, "客户/项目信息"] = u_proj
                new_df.at[idx, "结算账户"] = u_acc
                new_df.at[idx, "审批/发票单号"] = u_inv
                new_df.at[idx, "资金性质"] = u_prop
                new_df.at[idx, "实际金额"] = u_ori_amt
                new_df.at[idx, "实际币种"] = u_curr
                new_df.at[idx, "经手人"] = u_hand
                new_df.at[idx, "备注"] = u_note
                is_income = (u_prop in CORE_BIZ[:5] or u_prop in INC_OTHER)
                new_df.at[idx, "收入"] = u_usd_val if is_income else 0
                new_df.at[idx, "支出"] = u_usd_val if not is_income else 0
                new_df["收入"] = pd.to_numeric(new_df["收入"].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                new_df["支出"] = pd.to_numeric(new_df["支出"].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                new_df["余额"] = new_df["收入"].cumsum() - new_df["支出"].cumsum()
                for col in ['收入', '支出', '余额']:
                    new_df[col] = new_df[col].apply(lambda x: "{:.2f}".format(float(x)))
                conn.update(worksheet="Summary", data=new_df)
                st.success("✅ 修正成功！")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"保存错误: {e}")

    if ex.button("放弃", use_container_width=True):
        st.rerun()

# --- 💡 关键：将操作对话框定义提前，解决 NameError ---
@st.dialog("🎯 账目操作", width="small")
def row_action_dialog(row_data, full_df, conn):
    rec_id = row_data["录入编号"]
    if f"del_confirm_{rec_id}" not in st.session_state:
        st.session_state[f"del_confirm_{rec_id}"] = False

    st.write(f"**记录编号：** `{rec_id}`")
    st.write(f"**摘要详情：** {row_data.get('摘要','')}")
    st.write(f"**金额：** {row_data.get('实际币种','')} {row_data.get('实际金额','')}")
    st.divider()

    if not st.session_state[f"del_confirm_{rec_id}"]:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🛠️ 修改", use_container_width=True, key=



