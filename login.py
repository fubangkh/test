import streamlit as st

def show_login_page():
    # 1. 灰色 SVG 图标
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8fafc !important; }}
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 500px !important; padding-top: 5rem !important; }}

        /* 外框容器 */
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

        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
        }}
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        /* 强制辅助行在手机端也不换行 */
        .helper-row {{
            display: flex !important;
            flex-direction: row !important;
            justify-content: space-between !important;
            align-items: center !important;
            width: 100% !important;
            margin-bottom: 15px !important;
        }}
        /* 移除 checkbox 下方的默认间距，防止报错时挤压 */
        div[data-testid="stCheckbox"] {{ margin-bottom: 0 !important; }}

        /* --- 按钮样式：对齐高度 2.8rem --- */
        div.stButton > button {{
            background-color: white !important;
            color: #64748b !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 12px !important; 
            height: 2.8rem !important; 
            min-height: 2.8rem !important;
            line-height: 2.8rem !important;
            padding: 0 !important;
            width: 100% !important; 
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}

        div.stButton > button:hover {{
            background-color: #1f7a3f !important; 
            color: white !important;              
            border: 1.5px solid #1f7a3f !important;
            box-shadow: 0 4px 12px rgba(31, 122, 63, 0.15) !important;
        }}
        
        div.stButton > button:active {{
            transform: scale(0.99) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        # 1. 头部
        st.markdown(f"""
            <div class="header-box">
                <div class="logo-circle">FB</div>
                <h1 class="title-text">富邦日记账</h1>
            </div>
        """, unsafe_allow_html=True)

        # 2. 账号
        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> 账号</div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号，测试账号123", key="user", label_visibility="collapsed")
        
        st.write("") 

        # 3. 密码
        st.markdown(f'<div class="label-with-icon"><img src="{lock_svg}"> 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码，测试密码123", type="password", key="pwd", label_visibility="collapsed")

        # 4. 辅助项：通过 HTML 强制锁定横向布局
        st.markdown('<div class="helper-row">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1: 
            st.checkbox("记住我", value=True)
        with c2: 
            st.markdown("<div style='text-align:right; color:#64748b; font-size:0.88rem; cursor:pointer;'>忘记密码？</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 5. 按钮逻辑
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证通过，正在加载系统...")
                st.rerun()
            else:
                st.error("❌ 账号或密码不正确")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    show_login_page()
