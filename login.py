import streamlit as st

def show_login_page():
    # 注入 CSS 样式
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3rem !important;
            border: none !important;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
        }
        div[data-testid="stTextInput"] input {
            border-bottom: 2px solid #1F883D !important;
            border-top: none !important;
            border-left: none !important;
            border-right: none !important;
            border-radius: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. 页面居中布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        st.write("###") 
        
        with st.container(border=True):
            st.markdown("# 📒 富邦日记账")
            st.caption("请输入管理员授权的凭证以继续")

            # 2. 获取输入值
            username = st.text_input("用户名", placeholder="请输入账号", key="user")
            password = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd")
            
            # 3. 登录验证
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载...")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码不正确")

            st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
