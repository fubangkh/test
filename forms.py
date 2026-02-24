import streamlit as st
import time
from logic import prepare_new_data

@st.dialog("📝 新增录入", width="large")
def entry_dialog(conn, load_data_func, LOCAL_TZ, CORE_BIZ, INC_OTHER, EXP_OTHER):
    # 注入全局紧凑样式
    st.markdown("""<style>hr{margin-top:-15px!important;margin-bottom:10px!important;}.stTextArea textarea{height:68px!important;}</style>""", unsafe_allow_html=True)
    
    # ... (这里是你之前的输入框 UI 代码，val_sum, val_amt 等) ...

    # 底部提交按钮
    if st.button("🚀 确认提交", type="primary", use_container_width=True):
        # --- 校验逻辑 (UI层拦截) ---
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return
        if not val_inv.strip():
            st.error("⚠️ 请输入【审批/发票单号】！")
            return
        if not is_transfer and (not val_hand or val_hand in ["", "-- 请选择 --"]):
            st.error("⚠️ 请选择经手人！")
            return

        # --- 准备打包给 logic 的数据 ---
        entry_data = {
            'sum': val_sum, 'amt': val_amt, 'curr': val_curr, 'inv': val_inv,
            'prop': val_prop, 'note': val_note, 'hand': val_hand, 'conv_usd': converted_usd,
            'is_transfer': is_transfer,
            'acc': val_acc if not is_transfer else None,
            'acc_from': val_acc_from if is_transfer else None,
            'acc_to': val_acc_to if is_transfer else None,
            'proj': val_proj,
            'inc_val': converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0,
            'exp_val': converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0
        }

        with st.spinner("正在同步至云端..."):
            try:
                current_df = load_data_func(version=st.session_state.table_version + 1)
                full_df, new_ids = prepare_new_data(current_df, entry_data, LOCAL_TZ)
                
                # 执行写入
                conn.update(worksheet="Summary", data=full_df)
                
                # 确认逻辑 (轮询确认)
                ok = False
                for _ in range(6):
                    verify = conn.read(worksheet="Summary", ttl=0)
                    if not verify.empty and verify["录入编号"].astype(str).isin(new_ids).any():
                        ok = True; break
                    time.sleep(0.35)
                
                if ok:
                    st.toast("记账成功！", icon="💰")
                    st.session_state.table_version += 1
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 写入失败: {e}")import streamlit as st
import time
from logic import prepare_new_data

@st.dialog("📝 新增录入", width="large")
def entry_dialog(conn, load_data_func, LOCAL_TZ, CORE_BIZ, INC_OTHER, EXP_OTHER):
    # 注入全局紧凑样式
    st.markdown("""<style>hr{margin-top:-15px!important;margin-bottom:10px!important;}.stTextArea textarea{height:68px!important;}</style>""", unsafe_allow_html=True)
    
    # ... (这里是你之前的输入框 UI 代码，val_sum, val_amt 等) ...

    # 底部提交按钮
    if st.button("🚀 确认提交", type="primary", use_container_width=True):
        # --- 校验逻辑 (UI层拦截) ---
        if not val_sum.strip():
            st.error("⚠️ 请填写摘要内容！")
            return
        if not val_inv.strip():
            st.error("⚠️ 请输入【审批/发票单号】！")
            return
        if not is_transfer and (not val_hand or val_hand in ["", "-- 请选择 --"]):
            st.error("⚠️ 请选择经手人！")
            return

        # --- 准备打包给 logic 的数据 ---
        entry_data = {
            'sum': val_sum, 'amt': val_amt, 'curr': val_curr, 'inv': val_inv,
            'prop': val_prop, 'note': val_note, 'hand': val_hand, 'conv_usd': converted_usd,
            'is_transfer': is_transfer,
            'acc': val_acc if not is_transfer else None,
            'acc_from': val_acc_from if is_transfer else None,
            'acc_to': val_acc_to if is_transfer else None,
            'proj': val_proj,
            'inc_val': converted_usd if (val_prop in CORE_BIZ[:5] or val_prop in INC_OTHER) else 0,
            'exp_val': converted_usd if (val_prop in CORE_BIZ[5:] or val_prop in EXP_OTHER) else 0
        }

        with st.spinner("正在同步至云端..."):
            try:
                current_df = load_data_func(version=st.session_state.table_version + 1)
                full_df, new_ids = prepare_new_data(current_df, entry_data, LOCAL_TZ)
                
                # 执行写入
                conn.update(worksheet="Summary", data=full_df)
                
                # 确认逻辑 (轮询确认)
                ok = False
                for _ in range(6):
                    verify = conn.read(worksheet="Summary", ttl=0)
                    if not verify.empty and verify["录入编号"].astype(str).isin(new_ids).any():
                        ok = True; break
                    time.sleep(0.35)
                
                if ok:
                    st.toast("记账成功！", icon="💰")
                    st.session_state.table_version += 1
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 写入失败: {e}")
