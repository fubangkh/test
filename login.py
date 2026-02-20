import streamlit as st

def login_page():
    # 1. 样式必须放在最前面，确保全局生效
    st.markdown("""
        <style>
        /* 强制覆盖按钮为绿色 */
        div.stButton > button[kind="primary"] {
            background-color: #1F883D !important;
            color: white !important;
            border: none !important;
            height: 3rem !important;
            font-weight: bold !important;
            border-radius: 4px !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #66BB6A !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        }
        /* 输入框横线美化 */
        div[data-testid="stTextInput"] input {
            border-bottom: 2px solid #1F883D !important;
            border-top: none !important;
            border-left: none !important;
            border-right: none !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            padding-bottom: 5px !important;
        }
        div[data-testid="stTextInput"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("## 📒 富邦流水账")
        st.caption("请输入管理员授权的凭证以继续")

        # 2. 获取输入值
        username = st.text_input("用户名", placeholder="👤 请输入账号", key="user")
        password = st.text_input("密码", placeholder="🔒 请输入密码", type="password", key="pwd")

        st.write("") # 留点间距

        # 3. 登录逻辑：确保判断逻辑在按钮点击内
        if st.button("立即登录", type="primary", use_container_width=True):
            if username == "123" and password == "321":
                st.session_state.logged_in = True
                st.success("验证通过，正在加载系统...")
                st.rerun() 
            else:
                st.error("❌ 账号或密码不正确")

        # 4. 脚注（注意缩进要和 button 对齐）
        st.markdown("---")
        st.caption("💡 忘记密码请联系系统管理员")
