def show_login_page():
    # 注入 CSS
    st.markdown("""
        <style>
        div.stColumn > div > div > div.stVerticalBlock:has(div.login-box) {
            margin-top: -120px !important; 
        }
        /* 统一输入框外观 */
        div[data-testid="stTextInput"] input {
            border: 1px solid #dcdfe6 !important;
            border-radius: 8px !important;
            height: 3rem !important;
        }
        /* 解决图标大小差异：强制第二个输入框(密码)的图标放大 */
        div[data-testid="stTextInput"]:nth-of-type(2) input::placeholder {
            font-size: 1.25rem !important;
        }
        /* 第一个输入框(账号)图标保持适中 */
        div[data-testid="stTextInput"]:nth-of-type(1) input::placeholder {
            font-size: 1.1rem !important;
        }
        /* 按钮样式 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            height: 3rem !important;
            font-weight: bold !important;
            border: none !important;
        }
        div[data-testid="stTextInput"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        with st.container(border=True):
            # 标题居中且变绿
            st.markdown("""
                <div style='display: flex; flex-direction: column; align-items: center; margin-bottom: 20px;'>
                    <h2 style='color: #1F883D; margin: 0; display: flex; align-items: center; gap: 8px;'>
                        <span>📒</span> 富邦日记账
                    </h2>
                    <p style='color: gray; margin-top: 5px; font-size: 0.9rem;'>请输入管理员授权的凭证以继续</p>
                </div>
            """, unsafe_allow_html=True)

            # 输入区域
            username = st.text_input("用户名", placeholder="👤  请输入账号，测试账号123", key="user")
            password = st.text_input("密码", placeholder="🔒  请输入密码，测试密码123", type="password", key="pwd")
            
            if st.button("立即登录", use_container_width=True):
                # 你的校验逻辑...
                pass

            st.divider()
            st.caption("💡 忘记密码请联系系统管理员")
        st.markdown('</div>', unsafe_allow_html=True)
