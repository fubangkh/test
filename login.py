import streamlit as st

def show_login_page():
    # 1. SVG 图标
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        /* --- 1. 基础布局 --- */
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 480px !important; padding-top: 5rem !important; margin: 0 auto !important; }}
        
        /* --- 2. 界面样式 --- */
        .stApp {{ background-color: #f8fafc; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 28px !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
            padding: 2.5rem 2rem !important;
        }}

        /* 统一标题字体大小 */
        .title-text {{ 
            color: #1f7a3f; 
            font-size: 2.0rem !important; 
            font-weight: 800; 
            margin: 0; 
            white-space: nowrap !important;
        }}

        .label-with-icon {{ color: #475569; display: flex; align-items: center; gap: 8px; font-weight: 700; margin-bottom: 8px; }}
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{ background-color: #f1f5f9; border-radius: 12px !important; }}
        input {{ color: #1e293b; }}

        /* --- 3. 深色模式适配 --- */
        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-color: #0f172a !important; }}
            div[data-testid="stVerticalBlockBorderWrapper"] {{
                background-color: #1e293b !important;
                border: 1px solid #334155 !important;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
            }}
            .title-text {{ color: #4ade80 !important; }}
            .label-with-icon {{ color: #94a3b8 !important; }}
            div[data-testid="stTextInput"] div[data-baseweb="input"] {{
                background-color: #0f172a !important;
                border: 1px solid #334155 !important;
            }}
            input {{ color: #f8fafc !important; -webkit-text-fill-color: #f8fafc !important; }}
            .stCheckbox label p {{ color: #94a3b8 !important; }}
        }}

        /* --- 4. 按钮与 Logo 样式 --- */
        .header-box {{ 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 12px; 
            margin-bottom: 35px; 
            flex-wrap: nowrap !important;
        }}

        .logo-circle {{
            background-color: #1f7a3f; 
            color: white; 
            width: 45px !important; 
            height: 45px !important; 
            border-radius: 50% !important;
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 28px !important; /* FB 字母大号 */
            font-weight: 600 !important; 
            flex-shrink: 0 !important; 
        }}

        div.stButton > button {{
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 12px !important; height: 3rem !important; width: 100% !important; border: none !important;
        }}
        
        .custom-error-box {{
            background-color: #fee2e2; color: #b91c1c; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;
        }}
        @media (prefers-color-scheme: dark) {{
            .custom-error-box {{ background-color: #450a0a; color: #fca5a5; }}
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f'<div class="header-box"><div class="logo-circle">FB</div><h1 class="title-text">富邦日记账</h1></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> 账号</div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号，测试账号123", key="user", label_visibility="collapsed")
        
        st.markdown(f'<div class="label-with-icon" style="margin-top:10px;"><img src="{lock_svg}"> 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码，测试密码123", type="password", key="pwd", label_visibility="collapsed")

        st.checkbox("记住我", value=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.markdown('<div class="custom-error-box">⚠️ 账号或密码不正确</div>', unsafe_allow_html=True)
