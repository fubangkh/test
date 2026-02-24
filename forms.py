import streamlit as st
import pandas as pd
import time
from datetime import datetime
from logic import ALL_PROPS, CORE_BIZ, INC_OTHER, EXP_OTHER, prepare_new_data, calculate_full_balance

# --- 4. 录入模块 ---
@st.dialog("📝 新增录入", width="large")
def entry_dialog(conn, load_data, LOCAL_TZ, get_live_rates, get_dynamic_options):
    # 注入全局紧凑样式
    st.markdown("""<style>hr{margin-top:-5px!important;margin-bottom:10px!important;}.stTextArea textarea{height:68px!important;}</style>""", unsafe_allow_html=True)

    df = load_data()
    live_rates = get_live_rates()
    
    # 顶部结余显示
    current_balance = df['余额(USD)'].iloc[-1] if not df.empty else 0
    st.write(f"💡 当前总结余: **${current_balance:,.2f}**")
    
    # 1. 摘要与时间
    c1, c2 = st.columns(2)
    val_sum = c1.text_input("摘要内容 :red[*]", placeholder="请输入流水说明")
    val_time = c2.date_input("业务时间", value=datetime.now(LOCAL_TZ))
    
    # 2. 金额、币种、汇率
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    val_amt = r2_c1.number_input("原币金额 :red[*]", min_value=0.0, step=100.0)
    val_curr = r2_c2.selectbox("原币币种 :red[*]", list(live_rates.keys()))
    val_rate = r2_c3.number_input("实时汇率", value=float(live_rates[val_curr]), format="%.4f")
    
    # 实时换算显示
    converted_usd = round(val_amt / val_rate, 2) if val_rate != 0 else 0
    st.info(f"💰 换算后金额：$ {converted_usd:,.2f} USD")
    
    st.markdown('<hr style="margin-top: -5px; margin-bottom: 10px; border: 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)

    # 3. 性质与发票
    r4_c1, r4_c2 = st.columns(2)
    val_inv = r4_c1.text_input("📑 审批/发票单号 :red[*]")
    val_prop = r4_c2.selectbox("资金性质 :red[*]", ALL_PROPS)
    
    is_transfer = (val_prop == "资金结转")
    is_req = val_prop in CORE_BIZ

    # 4. 账户与经手人
    r3_c1, r3_c2 = st.columns(2)
    if is_transfer:
        val_acc_from = r3_c1.selectbox("➡️ 转出账户 :red[*]", options=get_dynamic_options(df, "结算账户"))
        val_acc_to = r3_c2.selectbox("⬅️ 转入账户 :red[*]", options=get_dynamic_options(df, "结算账户"))
        val_hand = "系统自动结转"
        val_acc = "资金结转" 
    else:
        sel_acc = r3_c1.selectbox("结算账户 :red[*]", options=get_dynamic_options(df, "结算账户"))
        val_acc = r3_c1.text_input("✍️ 录入新账户") if sel_acc == "➕ 新增..." else sel_acc
        sel_hand = r3_c2.selectbox("经手人 :red[*]", options=get_dynamic_options(df, "经手人"))
        val_hand = r3_c2.text_input("✍️ 录入新姓名") if sel_hand == "➕ 新增..." else sel_hand

    # 5. 客户或项目信息
    proj_label = "📍 客户/项目信息 (必填)" if is_req else "客户/项目信息 (选填)"
    sel_proj = st.selectbox(proj_label, options=get_dynamic_options(df, "客户/项目信息"))

    if sel_proj == "➕ 新增...":
        val_proj = st.text_input("✍️ 录入新客户/项目", key="k_new_proj_input", placeholder="请输入项目名称...")
    else:
        val_proj = sel_proj

    val_note = st.text_area("备注", height=68)

    # 7. 底部提交按钮
    col_sub, col_can = st.columns(2)

    if col_sub.button("🚀 确认提交", type="primary", use_container_width=True):
        if not val_sum.strip(): st.error("⚠️ 请填写摘要内容！"); return
        if val_amt <= 0: st.error("⚠️ 原币金额必须大于 0！"); return
        if not val_inv or val_inv.strip() == "": st.error("⚠️ 请输入【审批/发票单号】！"); return

        if not is_transfer:
            if not val_acc or val_acc.strip() in ["", "-- 请选择 --", "➕ 新增..."]:
                st.error("⚠️ 请选择或输入【结算账户】！"); return
            if not val_hand or val_hand.strip() in ["", "-- 请选择 --", "➕ 新增..."]:
                st.error("⚠️ 请选择或输入【经手人】！"); return
        else:
            if val_acc_from == "-- 请选择 --" or val_acc_to == "-- 请选择 --":
                st.error("⚠️ 资金结转模式下，转出和转入账户均不能为空！"); return
            if val_acc_from == val_acc_to:
                st.error("⚠️ 转出账户和转入账户不能相同！"); return

        if is_req and (not val_proj or val_proj.strip() in ["", "-- 请选择 --", "➕ 新增..."]):
            st.error(f"⚠️ 【{val_prop}】必须关联有效项目！"); return

        with st.spinner("正在同步至云端..."):
            try:
                current_df = load_data(version=st.session_state.table_version + 1)
                
                entry_data = {
                    'sum': val_sum, 'amt': val_amt, 'curr': val_curr, 'inv': val_inv,
                    'prop': val_prop, 'note': val_note, 'hand': val_hand, 'conv_usd': converted_usd,
                    'is_transfer': is_transfer, 'proj': val_proj,
                    'acc': val_acc if not is_transfer else None,
                    'acc_from': val_acc_from if is_transfer else None,
                    'acc_to': val_acc_to if is_transfer else None,
                    'inc_val': converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0,
                    'exp_val': converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0,
                    'converted_usd': converted_usd
                }

                full_df, new_ids = prepare_new_data(current_df, entry_data, LOCAL_TZ)
                conn.update(worksheet="Summary", data=full_df)
                
                ok = False
                for _ in range(6):
                    verify = conn.read(worksheet="Summary", ttl=0)
                    if not verify.empty and verify["录入编号"].astype(str).isin(new_ids).any():
                        ok = True; break
                    time.sleep(0.35)
                
                if ok:
                    st.toast("记账成功！数据已实时同步", icon="💰")
                    st.balloons()
                    st.cache_data.clear()
                    st.session_state.table_version += 1
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 写入失败: {e}")

    if col_can.button("🗑️ 取消返回", use_container_width=True):
        st.rerun()

# --- 5. 数据修正模块 ---
@st.dialog("🛠️ 数据修正", width="large")
def edit_dialog(target_id, full_df, conn, get_live_rates, get_dynamic_options, LOCAL_TZ):
    # 这里的逻辑确保 target_id 存在
    try:
        old = full_df[full_df["录入编号"] == target_id].iloc[0]
    except IndexError:
        st.error("找不到该条记录，可能已被删除或更新。")
        if st.button("关闭"): 
            st.session_state.show_edit_modal = False
            st.rerun()
        return

    live_rates = get_live_rates()
    st.info(f"正在修正记录：`{target_id}`")
    
    c1, c2 = st.columns(2)
    with c1: st.text_input("录入时间 (系统锁定)", value=str(old.get("提交时间", old.get("日期", ""))), disabled=True)
    u_sum = c2.text_input("摘要内容", value=str(old.get("摘要", "")))
    
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    u_ori_amt = r2_c1.number_input("原币金额", value=float(old.get("实际金额", 0.0)), step=100.0)
    curr_list = list(live_rates.keys())
    u_curr = r2_c2.selectbox("原币币种", curr_list, index=curr_list.index(old.get("实际币种", "USD")) if old.get("实际币种") in curr_list else 0)
    u_rate = r2_c3.number_input("汇率", value=float(live_rates.get(u_curr, 1.0)), format="%.4f")
    u_usd_val = round(u_ori_amt / u_rate, 2) if u_rate != 0 else 0
    st.info(f"💰 折算后金额：$ {u_usd_val:,.2f} USD")

    st.markdown('<hr style="margin-top: -5px; margin-bottom: 10px; border: 0; border-top: 1px solid #ddd;">', unsafe_allow_html=True)

    r4_c1, r4_c2 = st.columns(2)
    u_inv = r4_c1.text_input("审批/发票单号", value=str(old.get("审批/发票单号", "")))
    p_idx = ALL_PROPS.index(old.get("资金性质")) if old.get("资金性质") in ALL_PROPS else 0
    u_prop = r4_c2.selectbox("资金性质", ALL_PROPS, index=p_idx)

    r3_c1, r3_c2 = st.columns(2)
    acc_options = get_dynamic_options(full_df, "结算账户")
    curr_acc = old.get("结算账户", "")
    sel_acc = r3_c1.selectbox("结算账户", options=acc_options, index=acc_options.index(curr_acc) if curr_acc in acc_options else 0)
    u_acc = r3_c1.text_input("✍️ 录入新账户", placeholder="新账户名称") if sel_acc == "➕ 新增..." else sel_acc

    hand_options = get_dynamic_options(full_df, "经手人")
    curr_hand = old.get("经手人", "")
    sel_hand = r3_c2.selectbox("经手人", options=hand_options, index=hand_options.index(curr_hand) if curr_hand in hand_options else 0)
    u_hand = r3_c2.text_input("✍️ 录入新姓名", placeholder="经手人姓名") if sel_hand == "➕ 新增..." else sel_hand

    proj_options = get_dynamic_options(full_df, "客户/项目信息")
    curr_proj = old.get("客户/项目信息", "")
    sel_proj = st.selectbox("客户/项目信息", options=proj_options, index=proj_options.index(curr_proj) if curr_proj in proj_options else 0)
    u_proj = st.text_input("✍️ 录入新客户/项目", placeholder="项目名称...") if sel_proj in ["➕ 新增...", "-- 请选择 --"] else sel_proj

    u_note = st.text_area("备注", height=68, value=str(old.get("备注", "")))

    sv, ex = st.columns(2)
    if sv.button("💾 确认保存", type="primary", use_container_width=True):
        if not u_sum.strip(): st.error("摘要不能为空"); return
        try:
            new_df = full_df.copy()
            idx = new_df[new_df["录入编号"] == target_id].index[0]
            new_df.at[idx, "修改时间"] = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
            new_df.at[idx, "摘要"], new_df.at[idx, "客户/项目信息"] = u_sum, u_proj
            new_df.at[idx, "结算账户"], new_df.at[idx, "审批/发票单号"] = u_acc, u_inv
            new_df.at[idx, "资金性质"], new_df.at[idx, "实际金额"] = u_prop, u_ori_amt
            new_df.at[idx, "实际币种"], new_df.at[idx, "经手人"] = u_curr, u_hand
            new_df.at[idx, "备注"] = u_note
            
            is_income = (u_prop in CORE_BIZ[:5] or u_prop in INC_OTHER)
            new_df.at[idx, "收入(USD)"] = u_usd_val if is_income else 0
            new_df.at[idx, "支出(USD)"] = u_usd_val if not is_income else 0
            
            new_df = calculate_full_balance(new_df)
            conn.update(worksheet="Summary", data=new_df)
            
            # 清理状态并重启
            st.session_state.show_edit_modal = False
            st.session_state.edit_target_id = None
            st.session_state.table_version += 1
            st.cache_data.clear()
            st.success("✅ 修正成功！")
            time.sleep(0.8)
            st.rerun()
        except Exception as e: st.error(f"保存错误: {e}")

    if ex.button("放弃", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.edit_target_id = None
        st.rerun()

# --- 🎯 账目操作 (删除确认逻辑) ---
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
            if st.button("🛠️ 修正", use_container_width=True, key=f"edit_btn_{rec_id}"):
                # 🛠️ 关键修复：设置状态并立即 rerun，关闭当前弹窗触发 app.py 的调度
                st.session_state.edit_target_id = rec_id
                st.session_state.show_edit_modal = True
                st.rerun()
        with c2:
            if st.button("🗑️ 删除", type="primary", use_container_width=True, key=f"del_btn_{rec_id}"):
                st.session_state[f"del_confirm_{rec_id}"] = True
                st.rerun()
    else:
        st.error("⚠️ 确定要彻底删除此记录吗？操作不可恢复！")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 确定删除", type="primary", use_container_width=True):
                try:
                    updated_df = full_df[full_df["录入编号"] != rec_id].copy()
                    updated_df = calculate_full_balance(updated_df)
                    conn.update(worksheet="Summary", data=updated_df)
                    st.cache_data.clear()
                    st.success("✅ 删除成功！")
                    st.session_state.table_version += 1
                    time.sleep(0.8)
                    st.rerun()
                except Exception as e: st.error(f"失败: {e}")
        with cc2:
            if st.button("取消", use_container_width=True):
                st.session_state[f"del_confirm_{rec_id}"] = False
                st.rerun()
