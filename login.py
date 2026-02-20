import streamlit as st

def show_login_page():
    # 1. 定义灰色 SVG 图标 (确保变量名与下方调用一致)
    # 账号图标：人像
    user_icon_svg = """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E"""
    # 密码图标：锁头
    lock_icon_svg = """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='11' width='18' height='11' rx='2' ry='2'/%3E%3Cpath d='M7 11V7a5 5 0 0 1 10 0v4'/%3E%3C/svg%3E"""

    st.markdown(f"""
        <style>
        /* 全局及容器 */
        .stApp {{ background-color: #f8fafc !important; }}
        header {{ visibility: hidden; }}
        .block-container {{ max-width: 550px !important; padding-top: 5rem !important; }}

        /* 登录大卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 28px !important; 
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05) !important;
            border: 1px solid #f1f5f9 !important;
            padding: 3rem 2.5rem !important;
        }}

        /* 头部：Logo 和标题齐平 */
        .header-container {{
            display: flex; align-items: center; justify-content: center;
            gap: 15px; margin-bottom: 40px;
        }}
        .logo-circle {{
            background-color: #1f7a3f; color: white;
            width: 50px; height: 50px; border-radius: 50%; /* 圆形Logo */
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.3rem; flex-shrink: 0;
        }}
        .header-title {{
            color: #166534; font-size: 2rem; font-weight: 800; margin: 0;
            line-height: 50px;
        }}

        /* 输入框外部图标对齐逻辑 */
        .icon-outer-wrapper {{
            display: flex; align-items: center; justify-content: center;
            height: 3.5rem; /* 与输入框高度一致 */
            margin-top: 28px; /* 补偿 Label 的垂直空间 */
        }}

        /* 输入框容器样式 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
        }}
        
        /* 内部输入对齐 */
        div[data-testid="stTextInput"] input {{
            background-color: transparent !important;
            color: #1e293b !important;
            height: 100% !important;
        }}

        /* Label 样式 */
        div[data-testid="stTextInput"] label {{
            font-weight: 700 !important; color: #475569 !important; margin-bottom: 8px !important;
        }}

        /* 按钮样式 */
        div.stButton > button {{
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 12px !important; height: 3.5rem !important;
            width: 100% !important; font-weight: 700 !important; border: none !important;
            margin-top: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        # 1. 标题与圆形 Logo 齐平
        st.markdown(f"""
            <div class="header-container">
                <div class="logo-circle">FB</div>
                <h1 class="header-title">富邦日记账</h1>
            </div>
        """, unsafe_allow_html=True)

        # 2. 账号行 (图标在左 col1，输入框在右 col2)
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.markdown(f'<div class="icon-outer-wrapper"><img src="{user_icon_svg}" width="24"></div>', unsafe_allow_html=True)
        with col2:
            u = st.text_input("账号", placeholder="请输入账号", key="user")

        # 3. 密码行
        col3, col4 = st.columns([0.1, 0.9])
        with col3:
            st.markdown(f'<div class="icon-outer-wrapper"><img src="{lock_icon_svg}" width="24"></div>', unsafe_allow_html=True)
        with col4:
            p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd")

        # 4. 提交区 (对齐输入框宽度)
        _, col_btn = st.columns([0.1, 0.9])
        with col_btn:
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

# 确保直接运行或被调用时正常
if __name__ == "__main__":
    show_login_page()
