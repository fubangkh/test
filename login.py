import streamlit as st

def show_login_page():
    # 1. 样式增强（保留你的核心绿色调，增加微调）
    st.markdown("""
        <style>
        /* 强制覆盖按钮为绿色 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border: none !important;
            height: 3.2rem !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            transition: all 0.3s !important;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
            box-shadow: 0 4px 12px rgba(31, 136, 61, 0.2) !important;
        }
        /* 输入框下划线风格 */
        div[data-testid="stTextInput"] input {
            border: none !important;
            border-bottom: 2px solid #1F883D !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            padding-bottom: 5px !important;
            font-size: 1.1rem !important;
        }
        /* 隐藏输入框上方的标签 */
        div[data-testid="stTextInput"] label { display: none !important; }
        
        /* 调整容器内边距 */
        .login-box {
            padding: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 居中布局逻辑
    # 顶部留出一点空间
    st.write("#")
    st.write("#")
    
    # 使用 [1, 2, 1] 比例让 col2 居中
    empty_l, col2, empty_r = st.columns([1, 2, 1])

    with col2:
        # 使用官方最稳定的 border 容器
        with st.container(border=True):
            st.markdown("## 📒 富邦流水账")
            st.caption("请输入管理员授权的凭证以继续")
            
            st.write("") # 间距

            # 3. 获取输入值
            username = st.text_input("用户名", placeholder="👤 账号", key="user")
            st.write("") 
            password = st.text_input("密码", placeholder="🔒 密码", type="password", key="pwd")

            st.write("") # 留点间距

            # 4. 登录逻辑
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "321":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载系统...")
                    st.rerun() 
                else:
                    st.error("❌ 账号或密码不正确")

            # 5. 脚注
            st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
