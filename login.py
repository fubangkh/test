import streamlit as st

def show_login_page():
    # 颜色变量统一
    primary_green = "#1f7a3f"
    icon_gray = "#64748b" # 统一灰色图标颜色

    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8fafc !important; }}
        .block-container {{ max-width: 500px !important; padding-top: 5rem !important; }}

        /* 外框卡片 - 加大圆滑度 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 24px !important; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 3rem 2.5rem !important;
        }}

        /* 标题区 */
        .brand-header {{ display: flex; flex-direction: column; align-items: center; margin-bottom: 30px; }}
        .fb-logo {{
            background-color: {primary_green}; color: white;
            width: 60px; height: 60px; border-radius: 18px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.6rem;
            box-shadow: 0 6px 15px rgba(31, 122, 63, 0.25);
            margin-bottom: 15px;
        }}
        .brand-text {{ color: #064e3b; font-size: 2.2rem; font-weight: 800; letter-spacing: -1px; margin: 0; }}

        /* 自定义 Label 容器 */
        .custom-label {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: #334155; font-size: 0.95rem;
            margin-bottom: 8px;
        }}

        /* 输入框底色与对齐 */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
        }}
        div[data-testid="stTextInput"] input {{
            color: #1e293b !important;
            background-color: transparent !important;
            height: 3.2rem !important;
            line-height: 3.2rem !important;
            padding: 0 15px !important;
            display: flex !important; align-items: center !important;
        }}
        
        /* 隐藏原生 Label */
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        /* 登录按钮 */
        div.stButton > button {{
            background-color: {primary_green} !important;
            color: white !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
            width: 100% !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 10px;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 统一色系、统一尺寸、统一粗细的 SVG
    user_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_gray}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    lock_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_gray}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'

    with st.container():
        st.markdown(f"""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
                <p style='color: #64748b; margin-top: 8px; font-size: 0.95rem;'>管理员授权登录</p>
            </div>
        """, unsafe_allow_html=True)

        # 账号
        st.markdown(f'<div class="custom-label">{user_svg} 账号</div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")
        
        st.write("") # 间距

        # 密码
        st.markdown(f'<div class="custom-label">{lock_svg} 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

        # 辅助功能
        c1, c2 = st.columns([1, 1])
        with c1: st.checkbox("记住我", value=True)
        with c2: st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>", unsafe_allow_html=True)

        # 提交
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)
