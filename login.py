import streamlit as st

def show_login_page():
    # 1. 样式增强：增加卡片阴影、圆角和居中微调
    st.markdown("""
        <style>
        /* 登录卡片容器 */
        [data-testid="stVerticalBlock"] > div:has(div.login-card) {
            background-color: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            border: 1px solid #f0f2f6;
        }
        /* 输入框底线 */
        div[data-testid="stTextInput"] input {
            border: none !important;
            border-bottom: 2px solid #e0e0e0 !important;
            border-radius: 0px !important;
            background-color: transparent !important;
            transition: border-color 0.3s;
        }
        div[data-testid="stTextInput"] input:focus {
            border-bottom: 2px solid #1F883D !important;
        }
        /* 按钮美化 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.5rem !important;
            font-size: 1.1rem !important;
            border: none !important;
            margin-top: 10px;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
            box-shadow: 0 5px 15px rgba(31, 136, 61, 0.3) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. 居中布局：使用 columns 创造左右留白
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 使用 markdown 容器钩子来应用样式
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        st.markdown("## 📒 富邦日记账")
        st.caption("请输入管理员授权的凭证以继续")
        
        st.write("---") # 精细的分割线
        
        # 输入区
        username = st.text_input("用户名", placeholder="👤 账号", key="user", label_visibility="collapsed")
        st.write("") # 增加间距
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
        
        st.write("")
        st.caption("💡 忘记密码请联系管理员")
        
        st.markdown('</div>', unsafe_allow_html=True)
