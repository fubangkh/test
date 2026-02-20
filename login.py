import streamlit as st

def show_login_page():
    # 颜色变量
    primary_green = "#1f7a3f"
    icon_color = "#64748b" # 灰蓝色图标，更具高级感

    # 1. 深度样式定制
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8fafc !important; }}
        .block-container {{ max-width: 500px !important; padding-top: 5rem !important; }}

        /* 外框卡片 */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border-radius: 24px !important; 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05) !important;
            border: 1px solid #eef2f6 !important;
            padding: 3rem 2.5rem !important;
        }}

        /* FB Logo 徽章 */
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

        /* SVG 图标对齐逻辑 */
        .icon-label {{
            display: flex;
            align-items: center;
            gap: 8px; /* 图标和文字的间距 */
            font-weight: 700;
            color: #334155;
            font-size: 0.95rem;
        }}

        /* 输入框底色与垂直居中 */
        div[data-testid="stTextInput"] > div[data-baseweb="input"] {{
            background-color: #f1f5f9 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
        }}
        div[data-testid="stTextInput"] input {{
            color: #1e293b !important;
            background-color: transparent !important;
            height: 3.2rem !important;
            line-height: 3.2rem !important;
            padding: 0 15px !important;
            display: flex !important;
            align-items: center !important;
        }}

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

    # 2. 定义 SVG 图标代码 (Heroicons)
    user_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    lock_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'

    with st.container(border=True):
        # 顶部品牌区
        st.markdown(f"""
            <div class="brand-header">
                <div class="fb-logo">FB</div>
                <h1 class="brand-text">富邦日记账</h1>
                <p style='color: #64748b; margin-top: 8px; font-size: 0.95rem;'>管理员授权登录</p>
            </div>
        """, unsafe_allow_html=True)

        # 3. 输入区 - 组合 SVG 和 文字
        u = st.text_input(
            label="账号", 
            placeholder="请输入账号", 
            key="user", 
            label_visibility="visible"
        )
        # 通过 hack 方式将 SVG 注入到 label 之前的说明（由于 Streamlit 不直接支持 label HTML）
        # 我们用 markdown 的自定义容器来模拟对齐的效果
        st.markdown(f'<div class="icon-label" style="margin-top:-38px; margin-bottom:8px;">{user_svg} 账号</div>', unsafe_allow_html=True)
        
        st.write("") # 间距

        p = st.text_input(
            label="密码", 
            placeholder="请输入密码", 
            type="password", 
            key="pwd"
        )
        st.markdown(f'<div class="icon-label" style="margin-top:-38px; margin-bottom:8px;">{lock_svg} 密码</div>', unsafe_allow_html=True)

        # 记住我 与 忘记密码
        c1, c2 = st.columns([1, 1])
        with c1:
            st.checkbox("记住我", value=True)
        with c2:
            st.markdown("<div style='text-align:right; padding-top:10px; color:#64748b; font-size:0.9rem;'>忘记密码？</div>", unsafe_allow_html=True)

        if st.button("立即登录", use_container_width=True):
            if u == "123" and p == "123":
                st.session_state.logged_in = True
                st.success("验证成功")
                st.rerun()
            else:
                st.error("账号或密码错误")

        st.markdown("<hr style='margin: 25px 0; border:none; border-top:1px solid #f1f5f9;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.85rem;'>💡 忘记密码请联系系统管理员</div>", unsafe_allow_html=True)
