import streamlit as st

def show_login_page():
    # 注入 CSS 样式
    st.markdown("""
        <style>
        /* 1. 登录框整体上移 */
        [data-testid="stVerticalBlock"] > div:has(div.login-container) {
            margin-top: -50px !important; 
        }
        
        /* 2. 按钮样式 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3rem !important;
            border: none !important;
            margin-top: 10px;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
        }
        
        /* 3. 输入框风格 */
        div[data-testid="stTextInput"] input {
            border: 1px solid #dcdfe6 !important;
            border-radius: 4px !important;
        }
        div[data-testid="stTextInput"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    # 页面居中布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # 减少顶部间距，只留一个很小的位置
        st.write("#") 
        
        # 给容器包一层，方便 CSS 识别并整体上移
        with st.container(border=True):
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            # 1. 图标与文字水平居中
            st.markdown(
                "<h2 style='text-align: center;'>📒 富邦日记账</h2>", 
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>请输入管理员授权的凭证以继续</p>", 
                unsafe_allow_html=True
            )

            # 2. 输入区域
            username = st.text_input("用户名", placeholder="👤 请输入账号", key="user")
            password = st.text_input("密码", placeholder="🔒 请输入密码", type="password", key="pwd")
            
            st.write("") 
            
            # 3. 登录验证
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
