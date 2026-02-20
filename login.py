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

        /* 重点：强制 st.container(border=True) 的边框可见 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 2px solid #e2e8f0 !important; /* 明显的灰色外框线 */
            border-radius: 50px !important;       /* 圆角 */
            background-color: white !important;
            padding: 2.5rem 2rem !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03) !important;
        }}

        /* 标题对齐 */
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

        /* 图标+文字 Label */
        .label-with-icon {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: #475569; font-size: 0.95rem; margin-bottom: 8px;
        }}

        /* 输入框优化 */
        div[data-testid="stTextInput"] div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stTextInput"] label {{ display: none !important; }}

        /* 按钮 */
        div.stButton > button {{
            background-color: #1f7a3f !important; color: white !important;
            border-radius: 10px !important; height: 3.2rem !important;
            width: 100% !important; font-weight: 700 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # 使用原生容器并开启边框，CSS 会自动接管它的样式
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
        u = st.text_input("账号", placeholder="请输入账号", key="user", label_visibility="collapsed")
        
        st.write("") 

        # 3. 密码
        st.markdown(f'<div class="label-with-icon"><img src="{lock_svg}"> 密码</div>', unsafe_allow_html=True)
        p = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd", label_visibility="collapsed")

        # 4. 辅助
        c1, c2 = st.columns([1, 1])
        with c1: st.checkbox("记住我", value=True)
        with c2: st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.88rem;'>忘记密码？</div>", unsafe_allow_html=True)

        # 5. 按钮
        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.success("登录成功")
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)

if __name__ == "__main__":
    # 初始化 session 状态，如果没登录，设为 False
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # 显示你辛苦调好的大圆角登录页
        show_login_page()
    else:
        # 这里就是登录成功后看到的内容
        st.title("💰 富邦日记账 - 管理后台")
        st.sidebar.success(f"当前用户：{st.session_state.user if 'user' in st.session_state else '管理员'}")
        
        if st.sidebar.button("退出系统"):
            st.session_state.logged_in = False
            st.rerun()

        # 下面可以开始写你的主功能代码了
        st.write("欢迎进入系统，请开始您的账务操作。")
