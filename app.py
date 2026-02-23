import streamlit as st
import pandas as pd
import pytz
import time
import requests
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 全局配置 (必须放在最前面) ---
st.set_page_config(page_title="富邦日记账", layout="wide")
if "table_version" not in st.session_state:
    st.session_state.table_version = 0
    
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

# --- 5. 数据修正模块 (升级版：直接根据点击的 ID 填表) ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(target_id, full_df, conn):
    # 1. 准备常量与原始数据 (同步录入模块逻辑)
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
        # 修正：确保 value 传值正确，显示置灰日期
        st.text_input("录入时间 (系统锁定)", value=str(old.get("提交时间", old.get("日期", ""))), disabled=True)
    u_sum = c2.text_input("摘要内容", value=str(old.get("摘要", "")))
    
    # --- 第二部分：金额与币种 (同步录入换算逻辑) ---
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    u_ori_amt = r2_c1.number_input("原币金额", value=float(old.get("实际金额", 0.0)), step=100.0)
    
    curr_list = list(live_rates.keys())
    u_curr = r2_c2.selectbox("原币币种", curr_list, index=curr_list.index(old.get("实际币种", "USD")) if old.get("实际币种") in curr_list else 0)
    
    # 汇率逻辑：优先显示实时，但允许用户手动改
    default_rate = float(live_rates.get(u_curr, 1.0))
    u_rate = r2_c3.number_input("汇率", value=default_rate, format="%.4f")
    
    u_usd_val = round(u_ori_amt / u_rate, 2) if u_rate != 0 else 0
    st.info(f"💰 折算后金额：$ {u_usd_val:,.2f} USD")

    st.divider()

    # --- 第三部分：性质与发票 ---
    r4_c1, r4_c2 = st.columns(2)
    u_inv = r4_c1.text_input("审批/发票单号", value=str(old.get("审批/发票单号", "")))
    
    # 资金性质自动定位
    p_idx = ALL_PROPS.index(old.get("资金性质")) if old.get("资金性质") in ALL_PROPS else 0
    u_prop = r4_c2.selectbox("资金性质", ALL_PROPS, index=p_idx)

    # --- 第四部分：账户与经手人 (带下拉+新增模式) ---
    r3_c1, r3_c2 = st.columns(2)
    
    # 账户选择
    acc_options = get_dynamic_options(full_df, "结算账户")
    curr_acc = old.get("结算账户", "")
    sel_acc = r3_c1.selectbox("结算账户", options=acc_options, 
                             index=acc_options.index(curr_acc) if curr_acc in acc_options else 0)
    u_acc = r3_c1.text_input("✍️ 录入新账户", placeholder="新账户名称") if sel_acc == "➕ 新增..." else sel_acc

    # 经手人选择
    hand_options = get_dynamic_options(full_df, "经手人")
    curr_hand = old.get("经手人", "")
    sel_hand = r3_c2.selectbox("经手人", options=hand_options, 
                              index=hand_options.index(curr_hand) if curr_hand in hand_options else 0)
    u_hand = r3_c2.text_input("✍️ 录入新姓名", placeholder="经手人姓名") if sel_hand == "➕ 新增..." else sel_hand

    # --- 第五部分：项目信息 (带下拉+新增模式) ---
    proj_options = get_dynamic_options(full_df, "客户/项目信息")
    curr_proj = old.get("客户/项目信息", "")
    sel_proj = st.selectbox("客户/项目信息", options=proj_options, 
                           index=proj_options.index(curr_proj) if curr_proj in proj_options else 0)
    
    if sel_proj == "➕ 新增..." or sel_proj == "-- 请选择 --":
        u_proj = st.text_input("✍️ 录入新客户/项目", placeholder="项目名称...")
    else:
        u_proj = sel_proj

    u_note = st.text_area("备注", value=str(old.get("备注", "")))

    # --- 提交保存逻辑 ---
    st.divider()
    sv, ex = st.columns(2)
    
    if sv.button("💾 确认保存", type="primary", use_container_width=True):
        if not u_sum.strip():
            st.error("摘要不能为空")
            return
            
        try:
            # 数据切片更新
            new_df = full_df.copy()
            idx = new_df[new_df["录入编号"] == target_id].index[0]
            
            # 更新字段
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
            
            # 自动重新归类收入/支出 (根据资金性质判断)
            is_income = (u_prop in CORE_BIZ[:5] or u_prop in INC_OTHER)
            new_df.at[idx, "收入"] = u_usd_val if is_income else 0
            new_df.at[idx, "支出"] = u_usd_val if not is_income else 0
            
            # 重新计算整表流水余额
            new_df["收入"] = pd.to_numeric(new_df["收入"].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            new_df["支出"] = pd.to_numeric(new_df["支出"].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            new_df["余额"] = new_df["收入"].cumsum() - new_df["支出"].cumsum()
            
            # 格式化
            for col in ['收入', '支出', '余额']:
                new_df[col] = new_df[col].apply(lambda x: "{:.2f}".format(float(x)))

            # 写入
            conn.update(worksheet="Summary", data=new_df)
            st.success("✅ 修正并重算成功！")
            st.cache_data.clear()
            time.sleep(1)
            st.session_state.show_edit_modal = False
            st.session_state.last_processed_id = None
            st.session_state.table_version += 1
            st.rerun()
        except Exception as e:
            st.error(f"保存错误: {e}")

    if ex.button("放弃", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.show_action_menu = False
        st.session_state.last_processed_id = None
        
        # 💡 让表格强制重置（清空勾选）
        st.session_state.table_version += 1
        st.rerun()

# =========================================================
# 1. 操作枢纽：行点击后的对话框 (包含 修改 + 删除确认)
# =========================================================
@st.dialog("🎯 账目操作", width="small")
def row_action_dialog(row_data, full_df, conn):
    rec_id = row_data["录入编号"]
    
    # 内部状态：控制是否显示“删除确认”界面
    if f"del_confirm_{rec_id}" not in st.session_state:
        st.session_state[f"del_confirm_{rec_id}"] = False

    st.write(f"**记录编号：** `{rec_id}`")
    st.write(f"**摘要详情：** {row_data.get('摘要','')}")
    st.write(f"**金额：** {row_data.get('实际币种','')} {row_data.get('实际金额','')}")
    st.divider()

    # --- 逻辑 A：初始选择界面 ---
    if not st.session_state[f"del_confirm_{rec_id}"]:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🛠️ 修正", use_container_width=True, key=f"edit_{rec_id}"):
                st.session_state.show_action_menu = False
                st.session_state.edit_target_id = rec_id
                st.session_state.show_edit_modal = True
                st.rerun()  # 关闭当前 Dialog 并触发主程序的监听器
        with c2:
            if st.button("🗑️ 删除", type="primary", use_container_width=True, key=f"pre_del_{rec_id}"):
                st.session_state[f"del_confirm_{rec_id}"] = True
                st.session_state.is_deleting = True 
                st.rerun()

    # --- 逻辑 B：弹窗内的删除确认界面 (解决 Nested Dialog 报错) ---
    else:
        st.error("⚠️ 确定要彻底删除此记录吗？操作不可恢复！")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 确定删除", type="primary", use_container_width=True, key=f"real_del_{rec_id}"):
                try:
                    # 1. 执行删除并重算
                    updated_df = full_df[full_df["录入编号"] != rec_id].copy()
                    for col in ["收入", "支出"]:
                        updated_df[col] = pd.to_numeric(
                            updated_df[col].astype(str).str.replace(",", "", regex=False),
                            errors="coerce"
                        ).fillna(0)
                    updated_df["余额"] = updated_df["收入"].cumsum() - updated_df["支出"].cumsum()
                    for col in ["收入", "支出", "余额"]:
                        updated_df[col] = updated_df[col].apply(lambda x: "{:.2f}".format(float(x)))

                    # 2. 同步数据库
                    conn.update(worksheet="Summary", data=updated_df)
                    # 💡 关键：成功后，手动关闭弹窗信号，清除缓存，然后刷新
                    st.session_state.show_action_menu = False
                    st.cache_data.clear()
                    st.success("✅ 删除成功！")
                    time.sleep(0.8)
                    st.session_state.last_processed_id = None
                    st.session_state.table_version += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"失败: {e}")
        with cc2:
            if st.button("取消", use_container_width=True, key=f"cancel_del_{rec_id}"):
                st.session_state.show_action_menu = False
                st.session_state.last_processed_id = None
                st.session_state.table_version += 1
                
                st.rerun()

# --- 6. 主页面 ---
st.header("📊 汇总统计")
df_main = load_data()

# 💡 插入下面这段：弹窗中转调度器
if st.session_state.get("show_action_menu", False):
    target_id = st.session_state.get("action_target_id")
    # 立即关掉开关，防止死循环
    #st.session_state.show_action_menu = False 
    
    if target_id:
        hit = df_main[df_main["录入编号"] == target_id]
        if not hit.empty:
            row_action_dialog(hit.iloc[0], df_main, conn)

if df_main.empty:
    st.warning("⚠️ 数据库目前没有数据，请点击下方按钮开始录入第一笔账单。")
    if st.button("➕ 立即录入", key="empty_add"):
        entry_dialog()

# --- 第一步：数据预处理 ---
# 1. 币种归一化（这是最优先的，确保后续所有逻辑看到的都是统一币种）
df_main['实际币种'] = df_main['实际币种'].replace(['RMB', '人民币'], 'CNY')

# 2. 时间格式转换
df_main['提交时间'] = pd.to_datetime(df_main['提交时间'], errors='coerce')

# 3. 剔除无效时间行
df_main = df_main.dropna(subset=['提交时间'])

# 4. 数值预清洗（建议加上，确保计算不崩溃）
for col in ['收入', '支出', '余额', '实际金额']:
    if col in df_main.columns:
        df_main[col] = pd.to_numeric(df_main[col], errors='coerce').fillna(0)

# 5. 生成筛选列表（此时 df_main 已经完全干净了）
year_list = sorted(df_main['提交时间'].dt.year.unique().tolist(), reverse=True)
month_list = list(range(1, 13))

# --- 第二步：时间维度看板 ---
with st.container(border=True):
    st.markdown("### 📅 时间维度看板") 
    
    c1, c2, c3 = st.columns([2, 2, 5]) 
    with c1:
        sel_year = st.selectbox("年份", year_list, index=0, label_visibility="collapsed")
    with c2:
        sel_month = st.selectbox("月份", month_list, index=datetime.now().month - 1, label_visibility="collapsed")
    
    # 计算月份数值
    df_this_month = df_main[(df_main['提交时间'].dt.month == sel_month) & (df_main['提交时间'].dt.year == sel_year)]
    
    lm = 12 if sel_month == 1 else sel_month - 1
    ly = sel_year - 1 if sel_month == 1 else sel_year
    df_last_month = df_main[(df_main['提交时间'].dt.month == lm) & (df_main['提交时间'].dt.year == ly)]
    
    # 使用 pd.to_numeric 确保这一列全是数字，无法转换的（如空字符串）会变成 NaN
    # 然后用 .sum() 求和，NaN 会被自动忽略
    tm_inc = pd.to_numeric(df_this_month['收入'], errors='coerce').sum()
    tm_exp = pd.to_numeric(df_this_month['支出'], errors='coerce').sum()
    lm_inc = pd.to_numeric(df_last_month['收入'], errors='coerce').sum()
    lm_exp = pd.to_numeric(df_last_month['支出'], errors='coerce').sum()
    inc_delta = tm_inc - lm_inc
    exp_delta = tm_exp - lm_exp
    t_balance = df_main['收入'].sum() - df_main['支出'].sum()

    with c3:
        st.markdown(f"""
            <div style="margin-top: 7px; padding-left: 5px;">
                <span style="font-size: 1.2rem; font-weight: bold; color: #31333F;">
                    💡 当前统计周期：<span style="color: #4CAF50;">{sel_year}年{sel_month}月</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"💰 {sel_month}月收入", f"${tm_inc:,.2f}", delta=f"{inc_delta:,.2f}")
    m2.metric(f"📉 {sel_month}月支出", f"${tm_exp:,.2f}", delta=f"{exp_delta:,.2f}", delta_color="inverse")
    m3.metric("🏦 累计总结余", f"${t_balance:,.2f}")

st.divider()

# --- 账户余额与排行 ---
col_l, col_r = st.columns(2)
with col_l:
    st.write("🏦 **各账户当前余额 (原币对账)**")
        
    def calc_bank_balance(group):
        # 1. 统一转为数值
        inc_clean = pd.to_numeric(group['收入'], errors='coerce').fillna(0)
        exp_clean = pd.to_numeric(group['支出'], errors='coerce').fillna(0)
        amt_clean = pd.to_numeric(group['实际金额'], errors='coerce').fillna(0)
        
        # 2. 定义内部计算逻辑
        def get_raw_val(idx):
            current_val = amt_clean.loc[idx]
            if current_val == 0 or pd.isna(current_val):
                if inc_clean.loc[idx] > 0:
                    current_val = inc_clean.loc[idx]
                elif exp_clean.loc[idx] > 0:
                    current_val = exp_clean.loc[idx]
                else:
                    current_val = 0
            is_expense = exp_clean.loc[idx] > 0
            return -current_val if is_expense else current_val

        # --- 核心修复区：确保这些变量在 return 之前被定义 ---
        # 3. 计算 USD 总余额
        usd_bal = inc_clean.sum() - exp_clean.sum()
        
        # 4. 计算原币总余额 (这里定义了 raw_bal)
        raw_bal = sum(get_raw_val(idx) for idx in group.index)
        
        # 5. 获取币种
        valid_currencies = group['实际币种'][group['实际币种'] != ""].tolist()
        cur_name = valid_currencies[-1] if valid_currencies else "USD"
        
        # 6. 返回结果
        return pd.Series([usd_bal, raw_bal, cur_name], index=['USD', 'RAW', 'CUR'])

    try:
        acc_stats = df_main.groupby('结算账户').apply(calc_bank_balance).reset_index()
        
        # 1. 物理对齐映射：在代码前后手动加空格
        # 这里用 center(10) 表示占据 10 个字符宽度并居中
        iso_map = {
            "人民币": "CNY", "CNY": "CNY", 
            "港币": "HKD", "HKD": "HKD", 
            "印尼盾": "IDR", "IDR": "IDR", 
            "越南盾": "VND", "VND": "VND", 
            "美元": "USD", "USD": "USD"
        }

        # 核心改动：使用 .center() 函数给字符串强行加空格实现“伪居中”
        # 如果想要右对齐，就用 .rjust(10)
        acc_stats['原币种'] = acc_stats['CUR'].map(lambda x: iso_map.get(x, x).rjust(12))
        
        display_acc = acc_stats[['结算账户', '原币种', 'RAW', 'USD']].copy()

        # 2. Styler 逻辑（保持不变）
        styled_acc = display_acc.style.format({
            'RAW': '{:,.2f}',
            'USD': '${:,.2f}'
        }).map(
            lambda x: 'color: #d32f2f;' if x < -0.01 else 'color: #31333F;',
            subset=['RAW', 'USD']
        )
        
        # 3. 渲染
        st.dataframe(
            styled_acc,
            use_container_width=True, 
            hide_index=True,
            column_config={
                "结算账户": st.column_config.TextColumn("结算账户", width="medium"),
                # 这里原币种是带空格的字符串，TextColumn 会把空格也渲染出来
                "原币种": st.column_config.TextColumn("原币种", width="small"),
                "RAW": st.column_config.NumberColumn("原币金额", width="small"),
                "USD": st.column_config.NumberColumn("折合美元 (USD)", width="small")
            }
        )
        
    except Exception as e:
        st.error(f"余额计算异常: {e}")

with col_r:
    st.write(f"🏷️ **{sel_month}月支出排行**")
    # 1. 筛选本月支出数据并按性质分组
    exp_stats = df_this_month[df_this_month['支出'] > 0].groupby('资金性质')['支出'].sum().sort_values(ascending=False).reset_index()
    
    if not exp_stats.empty:
        # 2. 应用 Styler：控制千分位 + 颜色（支出通常统一为红色或默认黑色）+ 右对齐
        styled_exp = exp_stats.style.format({
            "支出": "${:,.2f}"
        }).map(
            # 统一支出颜色为红色，并注入右对齐 CSS
            lambda x: 'color: #d32f2f; text-align: right;', 
            subset=['支出']
        )
        
        # 3. 渲染表格
        st.dataframe(
            styled_exp, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "资金性质": st.column_config.TextColumn("资金性质", width="medium"),
                "支出": st.column_config.NumberColumn("支出金额", width="medium")
            }
        )
    else:
        st.caption("该月暂无支出记录")

st.divider()

# --- 第四步：流水明细表 (含搜索和格式化) ---
h_col, b_dl, b_add, b_edit = st.columns([4, 1.2, 1, 1])
h_col.subheader("📑 流水明细表")
with b_add:
    if st.button("➕ 录入", type="primary", use_container_width=True, key="main_add"): entry_dialog()

# 筛选数据
df_display = df_main.copy()
df_display = df_display[
(df_display['提交时间'].dt.year == sel_year) & 
(df_display['提交时间'].dt.month == sel_month)
]
df_display = df_display.sort_values("录入编号", ascending=False)

# 搜索框
search_query = st.text_input("🔍 搜索本月流水", placeholder="🔍 输入关键词...", label_visibility="collapsed")
if search_query:
    q = search_query.lower()
    mask = (
        df_display['摘要'].astype(str).str.lower().str.contains(q, na=False) |
        df_display['客户/项目信息'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['结算账户'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['审批/发票单号'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['经手人'].astype(str).str.lower().str.contains(q, na=False)|
        df_display['资金性质'].astype(str).str.lower().str.contains(q, na=False)
    )
    df_display = df_display[mask]

# --- 第三步：核心优化： Styler 全权接管展示层 ---
# --- 数据预清洗：统一币种并强制数值化 ---
df_display['实际币种'] = df_display['实际币种'].replace(['RMB', '人民币'], 'CNY')

# 必须先转为数字，Styler 的千分位指令 {:,.2f} 才能生效
for col in ['收入', '支出', '余额', '实际金额']:
    df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0)

# =========================================================
# 2. 监听器：放置在主程序中 (解决修改无反应)
# =========================================================
if st.session_state.get("show_edit_modal", False):
    target_id = st.session_state.get("edit_target_id")
    st.session_state.show_edit_modal = False # 立即复位
    # 💡 只有在有 ID 的情况下才弹窗
    if target_id:
        st.session_state.show_action_menu = False
        edit_dialog(target_id, df_main, conn)
# =========================================================
# 3. 渲染层：明细表显示 (移除顶部冗余按钮)
# =========================================================

if not df_display.empty:
    # 1. 定义一个针对“行”的智能格式化函数
    def format_original_price(row):
        curr = str(row['实际币种']).strip().upper()
        amt = row['实际金额']
        
        # 定义不同币种的符号
        symbols = {
            'CNY': '¥', '人民币': '¥',
            'USD': '$', '美元': '$',
            'IDR': 'Rp', '印尼盾': 'Rp',
            'VND': '₫', '越南盾': '₫',
            'HKD': 'HK$'
        }
        s = symbols.get(curr, '') 
        
        # 针对 IDR 和 VND 不显示小数位，其他保留两位
        if curr in ['IDR', 'VND']:
            return f"{s}{amt:,.0f}"
        else:
            return f"{s}{amt:,.2f}"

    # 2. 创建一个临时的显示列（这不会改动原始数据，只用于展示）
    df_display['原币显示'] = df_display.apply(format_original_price, axis=1)

    # 3. 核心：由 Pandas Styler 处理其他固定列
    styled_display = df_display.style.format({
        "收入": "${:,.2f}",
        "支出": "${:,.2f}",
        "余额": "${:,.2f}"
    })

    # 4. 渲染表格
    event = st.dataframe(
        styled_display,
        use_container_width=True,
        hide_index=True,
        height=500,
        on_select="rerun",
        selection_mode="single-row",
        key=f"data_table_{st.session_state.table_version}",
        column_config={
            # 💡 这里是关键：
            # 显示我们新造的“原币显示”列，并起名为“原币金额”
            "原币显示": st.column_config.TextColumn("原币金额", width="small"),
            # 隐藏原本那个纯数字的“实际金额”列，防止重复
            "实际金额": None, 
            
            "收入": st.column_config.NumberColumn("收入(USD)", width="small"),
            "支出": st.column_config.NumberColumn("支出(USD)", width="small"),
            "余额": st.column_config.NumberColumn("余额(USD)", width="small"),
            "提交时间": st.column_config.DatetimeColumn("提交时间", format="YYYY-MM-DD HH:mm", width="small"),
            "修改时间": st.column_config.DatetimeColumn("修改时间", format="YYYY-MM-DD HH:mm", width="small"),
            "录入编号": st.column_config.TextColumn("录入编号", width="small"),
            "摘要": st.column_config.TextColumn("摘要", width="medium"),
            "客户/项目信息": st.column_config.TextColumn("客户/项目信息", width="medium"),
            "结算账户": st.column_config.TextColumn("结算账户", width="small"),
            "资金性质": st.column_config.TextColumn("资金性质", width="small"),
            "实际币种": st.column_config.TextColumn("原币种", width="small"),
            "经手人": st.column_config.TextColumn("经手人", width="small"),
            "备注": st.column_config.TextColumn("备注", width="small"),
        }
    )

    # 捕获点击 (防抖 + 安全跳转版)
    if event and event.selection and event.selection.rows:
        row_idx = event.selection.rows[0]
        sel_id = df_display.iloc[row_idx]["录入编号"]
        
        # 💡 如果现在已经有弹窗在显示了，就不要再触发 rerun 了
        if not st.session_state.get("show_action_menu", False):
            # 只有当点击的是新行时才触发
            if st.session_state.get("last_processed_id") != sel_id:
                st.session_state.action_target_id = sel_id
                st.session_state.show_action_menu = True
                st.session_state.last_processed_id = sel_id
                st.rerun() 
    else:
        st.session_state.last_processed_id = None
        st.session_state.is_deleting = False
else:
    st.info("💡 暂无数据。")












