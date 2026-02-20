import streamlit as st

def login_page():
    # 1. 极简样式（只美化按钮和底线，不触碰全局容器）
    st.markdown("""
        <style>
        /* 只针对输入框底线 */
        div[data-testid="stTextInput"] input {
            border: none !important;
            border-bottom: 2px solid #1F883D !important;
            border-radius: 0px !important;
        }
        /* 只针对按钮 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            height: 3.5rem !important;
            font-weight: bold !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 居中布局
    # 增加上下留白，防止内容贴顶
    st.write("#") 
    st.write("#") 

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 使用原生带边框的容器，这是最安全的做法
        with st.container(border=True):
            st.markdown("## 📒 富邦日记账")
            st.caption("请输入管理员授权的凭证以继续")
            
            # 输入区
            username = st.text_input("用户名", placeholder="👤 账号", key="user", label_visibility="collapsed")
            password = st.text_input("密码", placeholder="🔒 密码", type="password", key="pwd", label_visibility="collapsed")
            
            st.write("") 
            
            # 登录逻辑
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "321":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在登录...")
                    st.rerun()
                else:
                    st.error("❌ 账号或密码不正确")
            
            st.divider() # 官方分割线
            st.caption("💡 忘记密码请联系管理员")
