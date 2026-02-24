import streamlit as st
import pandas as pd
import time
from datetime import datetime
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER, prepare_new_data, calculate_full_balance

# --- 4. 录入模块 ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options):
    st.markdown("""<style>hr{margin-top:-5px!important;margin-bottom:10px!important;}.stTextArea textarea{height:68px!important;}</style>""", unsafe_allow_html=True)
    df = load_data()
    live_rates = get_live_rates()
    
    # ... (此处省略中间重复的输入框代码，与之前完全一致) ...
    # 假设输入框代码在这里
    val_sum = st.text_input("摘要内容 :red[*]")
    # ...

    col_sub, col_can = st.columns(2)
    if col_sub.button("🚀 确认提交", type="primary", use_container_width=True):
        # ... (提交逻辑不变) ...
        # 成功后：
        st.session_state.table_version += 1 # 强制刷新表格
        st.rerun()

    if col_can.button("🗑️ 取消返回", use_container_width=True):
        st.rerun()

# --- 5. 数据修正模块 ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(target_id, full_df, conn, get_live_rates, get_dynamic_options, LOCAL_TZ):
    try:
        old = full_df[full_df["录入编号"] == target_id].iloc[0]
    except:
        st.error("记录不存在"); st.session_state.show_edit_modal = False; st.rerun(); return

    # ... (此处省略中间重复的修改框代码，与之前完全一致) ...
    u_sum = st.text_input("摘要内容", value=str(old.get("摘要", "")))
    # ...

    sv, ex = st.columns(2)
    if sv.button("💾 确认保存", type="primary", use_container_width=True):
        # 执行保存逻辑...
        # 成功后：
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        st.session_state.table_version += 1 # 强制刷新
        st.cache_data.clear()
        st.rerun()

    if ex.button("放弃", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        # 【核心修复】: 放弃时也要增加版本号，彻底洗掉表格的选中状态
        st.session_state.table_version += 1 
        st.rerun()

# --- 🎯 账目操作模块 ---
@st.dialog("🎯 账目操作", width="small")
def row_action_dialog(row_data, full_df, conn):
    rec_id = row_data["录入编号"]
    if f"del_confirm_{rec_id}" not in st.session_state: 
        st.session_state[f"del_confirm_{rec_id}"] = False

    st.write(f"**记录编号：** `{rec_id}`")
    st.divider()

    if not st.session_state[f"del_confirm_{rec_id}"]:
        c1, c2 = st.columns(2)
        if c1.button("🛠️ 修正", use_container_width=True):
            st.session_state.edit_target_id = rec_id
            st.session_state.show_edit_modal = True
            st.rerun()
        if c2.button("🗑️ 删除", type="primary", use_container_width=True):
            st.session_state[f"del_confirm_{rec_id}"] = True
            st.rerun()
        
        # 新增一个明确的退出按钮，确保清空选择
        if st.button("✖️ 关闭菜单", use_container_width=True):
            st.session_state.table_version += 1 # 增加版本号强制重置表格选择
            st.rerun()
    else:
        st.error("确定删除吗？")
        cc1, cc2 = st.columns(2)
        if cc1.button("确定", type="primary", use_container_width=True):
            # 删除逻辑...
            st.session_state.table_version += 1
            st.rerun()
        if cc2.button("取消", use_container_width=True):
            st.session_state[f"del_confirm_{rec_id}"] = False
            # 【核心修复】: 取消删除时，也要强制刷新表格版本，否则弹窗会反复出现
            st.session_state.table_version += 1 
            st.rerun()
