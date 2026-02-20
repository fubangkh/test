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

        /* 强制 st.container(border=True) 的边框可见 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 2px solid #e2e8f0 !important; 
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
        .title-text {{ color: #166534; font-size: 1.8rem; font-weight: 800; margin: 0; }}

        .label-with-icon {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: #475569; font-size: 0.95rem; margin-bottom: 8px;
        }}

        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        div.stButton > button {{
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 10px !important; height: 3.2rem !important;
            width: 100% !important; font-weight: 700 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"""
            <div class="header-box">
                <div class="logo-circle">FB</div>
                <h1 class="title-text">富邦日记账</h1>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="label-with-icon"><img src="{user_svg}"> 账号</div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号，测试账号123", key="user", label_visibility="collapsed")
        
        st.write("") 

        st.markdown(f'<div class="label-with-icon"><img src="{lock_svg}"> 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码，测试密码123", type="password", key="pwd", label_visibility="collapsed")

        c1, c2 = st.columns([1, 1])
        with c1: st.checkbox("记住我", value=True)
        with c2: st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.88rem;'>忘记密码？</div>", unsafe_allow_html=True)

        # --- 核心修改：统一登录逻辑在这里 ---
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True  # 1. 设置状态
                st.success("验证通过，正在加载系统...")  # 2. 提示
                st.rerun()  # 3. 关键：触发 app.py 刷新并识别新状态
            else:
                st.error("❌ 账号或密码不正确")

# 函数外面不要再放按钮逻辑了
