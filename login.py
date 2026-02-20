import streamlit as st

def show_login_page():
    # 注入 CSS
    st.markdown("""
        <style>
        /* 1. 整个卡片上移 */
        div.stColumn > div > div > div.stVerticalBlock:has(div.login-box) {
            margin-top: -120px !important; 
        }

        /* 2. 按钮样式：保持深绿 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3rem !important;
            border: none !important;
            margin-top: 20px;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
        }

        /* 3. 居中容器 */
        .title-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 页面布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        with st.container(border=True):
            # --- 核心改动点：在这里修改标题颜色 ---
            st.markdown("""
                <div class="title-container">
                    <h2 style='margin: 0; color: #1F883D; font-weight: bold;'>📒 富邦日记账</h2>
                    <p style='color: gray; margin-top: 5px; font-size: 0.9rem;'>请输入管理员授权的凭证以继续</p>
                </div>
            """, unsafe_allow_html=True)

            # 输入区域
            username = st.text_input("用户名", placeholder="👤 请输入账号", key="user", label_visibility="collapsed")
            password = st.text_input("密码", placeholder="🔒 请输入密码", type="password", key="pwd", label_visibility="collapsed")
            
            # 登录验证
            if st.button("立即登录", use_container_width=True):
                if username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载...")
                    st.rerun() 
                else:
                    st.error("❌ 账号或密码不正确")

            st.divider()
            st.caption("💡 忘记密码请联系系统管理员")
            
        st.markdown('</div>', unsafe_allow_html=True)
