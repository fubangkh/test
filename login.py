import streamlit as st

def show_login_page():
    # 灰色 SVG 图标编码 (#64748b)
    user_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_icon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        /* 1. 全局环境 */
        .stApp {{ background-color: #f8fafc !important; }}
        header {{visibility: hidden;}}
        .block-container {{ max-width: 480px !important; padding-top: 5rem !important; }}
        
        /* 2. 登录卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 28px !important; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06) !important;
            border: 1px solid #f1f5f9 !important;
            padding: 3rem 2.2rem !important;
        }}

        /* 3. 输入框盒子模型重构 - 解决截断与眼睛图标问题 */
        /* 这一层是总容器，我们在这里设置背景和圆角 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            height: 3.5rem !important; /* 稍微加高，防止文字拥挤 */
            padding-left: 1rem !important;
            transition: all 0.2s;
        }}

        /* 移除内部所有层级的背景，防止“叠罗汉”和截断 */
        div[data-testid="stTextInput"] div[data-baseweb="base-input"],
        div[data-testid="stTextInput"] [role="presentation"],
        div[data-testid="stTextInput"] input {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            height: 100% !important;
        }}

        /* 注入图标：改用容器的 padding-left 配合 background-position */
        div[data-testid="stTextInput"] input {{
            padding-left: 2.2rem !important; /* 图标后的文字间距 */
            color: #1e293b !important;
            font-size: 1rem !important;
            line-height: 3.5rem !important;
        }}

        /* 账号图标 */
        div[data-testid="stTextInput"]:nth-of-type(1) div[data-baseweb="input"] {{
            background-image: url("{user_icon}") !important;
            background-repeat: no-repeat !important;
            background-position: 1rem center !important;
            background-size: 1.25rem !important;
        }}
        
        /* 密码图标 */
        div[data-testid="stTextInput"]:nth-of-type(2) div[data-baseweb="input"] {{
            background-image: url("{lock_icon}") !important;
            background-repeat: no-repeat !important;
            background-position: 1rem center !important;
            background-size: 1.25rem !important;
        }}

        /* 让密码框的眼睛图标完美融合 */
        div[data-testid="stTextInput"] button {{
            background-color: transparent !important;
            border: none !important;
            margin-right: 8px !important;
        }}

        /* 4. 其他组件优化 */
        .brand-logo {{
            background: #1f7a3f; color: white; width: 60px; height: 60px; 
            border-radius: 18px; display: flex; align-items: center; 
            justify-content: center; font-weight: 800; font-size: 1.6rem; 
            margin: 0 auto 15px;
        }}
        .brand-title {{ color: #064e3b; font-size: 2.2rem; font-weight: 800; text-align: center; margin-bottom: 30px; }}

        div.stButton > button {{
            background-color: #1f7a3f !important;
            color: white !important;
            border-radius: 14px !important;
            height: 3.5rem !important;
            width: 100% !important;
            font-weight: 700 !important;
            border: none !important;
            margin-top: 10px;
        }}

        div[data-testid="stTextInput"] label {{
            font-weight: 700 !important; color: #334155 !important;
            margin-bottom: 10px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="brand-logo">FB</div>', unsafe_allow_html=True)
        st.markdown('<h1 class="brand-title">富邦日记账</h1>', unsafe_allow_html=True)

        u = st.text_input("账号", placeholder="请输入您的账号", key="user")
        p = st.text_input("密码", placeholder="请输入您的密码", type="password", key="pwd")

        c1, c2 = st.columns([1, 1])
        with c1: st.checkbox("记住我", value=True)
        with c2: st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.success("登录成功")
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)

show_login_page()
