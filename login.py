import streamlit as st

def show_login_page():
    # 1. 图标定义
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8fafc !important; }}
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 500px !important; padding-top: 5rem !important; }}

        /* 外框 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 1.5px solid #e2e8f0 !important; 
            border-radius: 50px !important;       
            background-color: white !important;
            padding: 2.5rem 2rem !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03) !important;
        }}

        .header-box {{
            display: flex; align-items: center; justify-content: center;
            gap: 15px; margin-bottom: 35px;
        }}
        .logo-circle {{
            background-color: #1f7a3f; color: white;
            width: 46px; height: 46px; border-radius: 50% !important;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.2rem;
        }}
        .title-text {{ color: #1f7a3f; font-size: 1.8rem; font-weight: 800; margin: 0; }}

        .label-with-icon {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: #475569; font-size: 0.95rem; margin-bottom: 8px;
        }}

        /* 输入框 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
        }}
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        /* 辅助行强制对齐容器 */
        .helper-container {{
            position: relative;
            height: 40px;
            margin-bottom: 10px;
        }}
        .forgot-password-link {{
            position: absolute;
            right: 0;
            top: 2px;
            color: #64748b;
            font-size: 0.88rem;
            cursor: pointer;
        }}

        /* 登录按钮 */
        div.stButton > button {{
            background-color: white !important;
            color: #64748b !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 12px !important; 
            height: 2.5rem !important; 
            width: 100% !important; 
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}
        div.stButton > button:hover {{
            background-color: #1f7a3f !important; 
            color: white !important;              
            border: 1.5px solid #1f7a3f !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # 1. 标题
        st.markdown(f'<div class="header-box"><div class="logo-circle">FB</div><h1 class="title-text">富邦日记账</h1></div>', unsafe_allow_html=True)

        # 2. 账号
        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> 账号</div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号", key="user")
        
        st.write("") 

        # 3. 密码
        st.markdown(f'<div class="label-with-icon"><img src="{lock_svg}"> 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd")

        # 4. 辅助行：通过绝对定位强行把文字“吸”在勾选框右侧
        st.markdown('<div class="helper-container">', unsafe_allow_html=True)
        # 这里只放勾选框
        st.checkbox("记住我", value=True)
        # 这里用绝对定位放文字
        st.markdown('<div class="forgot-password-link">忘记密码？</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 5. 按钮
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("❌ 账号或密码错误")

        st.markdown("<hr style='margin: 15px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    show_login_page()
