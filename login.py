import streamlit as st

def show_login_page():
    # 注入 CSS：利用垂直块选择器将整个容器上移
    st.markdown("""
        <style>
        /* 1. 关键：将包含 login-box 的整个父容器上移 */
        /* 我们通过这个特定的 class 来定位并移动整个卡片 */
        div.stColumn > div > div > div.stVerticalBlock:has(div.login-box) {
            margin-top: -120px !important; 
        }

        /* 2. 按钮样式 */
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

        /* 3. 居中标题的样式优化 */
        .title-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 页面居中布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # 给容器套一个 class 方便 CSS 定位
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        with st.container(border=True):
            # 标题和图标强制整体居中
            st.markdown("""
                <div class="title-container">
                    <h2 style='margin: 0;'>📒 富邦日记账</h2>
                    <p style='color: gray; margin-top: 5px;'>请输入管理员授权的凭证以继续</p>
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
