import streamlit as st

def show_login_page():
    # 1. 定义灰色 SVG 图标 (高级灰 #64748b)
    user_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"
    lock_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        /* 基础环境 */
        .stApp {{ background-color: #f8fafc !important; }}
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 500px !important; padding-top: 4rem !important; }}

        /* 登录卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 28px !important; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05) !important;
            border: 1px solid #f1f5f9 !important;
            padding: 2.5rem 2rem !important;
        }}

        /* 头部对齐：圆形Logo + 标题 */
        .header-box {{
            display: flex; align-items: center; justify-content: center;
            gap: 15px; margin-bottom: 35px;
        }}
        .logo-circle {{
            background-color: #1f7a3f; color: white;
            width: 48px; height: 48px; border-radius: 50% !important;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.2rem; flex-shrink: 0;
            box-shadow: 0 4px 10px rgba(31,122,63,0.2);
        }}
        .title-text {{
            color: #166534; font-size: 1.8rem; font-weight: 800; margin: 0;
        }}

        /* 自定义 Label：文字左 图标右 */
        .label-with-icon {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: #475569; font-size: 0.95rem;
            margin-bottom: 8px;
        }}

        /* 输入框样式修复 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
        }}
        div[data-testid="stTextInput"] input {{
            background-color: transparent !important;
            color: #1e293b !important;
        }}
        
        /* 隐藏原生 Label 以便展示自定义 Label */
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        /* 按钮与提示 */
        div.stButton > button {{
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 12px !important; height: 3.2rem !important;
            width: 100% !important; font-weight: 700 !important; border: none !important;
            margin-top: 10px;
        }}
        div[data-testid="stNotification"] {{ border-radius: 12px !important; }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        # 1. 顶部齐平布局
        st.markdown(f"""
            <div class="header-box">
                <div class="logo-circle">FB</div>
                <h1 class="title-text">富邦日记账</h1>
            </div>
        """, unsafe_allow_html=True)

        # 2. 账号部分
        st.markdown(f'<div class="label-with-icon">账号 <img src="{user_svg}" width="18"></div>', unsafe_allow_html=True)
        u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")
        
        st.write("") # 增加间距

        # 3. 密码部分
        st.markdown(f'<div class="label-with-icon">密码 <img src="{lock_svg}" width="18"></div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

        # 4. 记住我 & 忘记密码
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.88rem; cursor:pointer;'>忘记密码？</div>", unsafe_allow_html=True)

        # 5. 登录按钮
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.success("验证成功")
            else:
                st.error("账号或密码错误")

        # 底部提示
        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    show_login_page()
