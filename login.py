import streamlit as st

def show_login_page():
    # 1. 样式注入：保持 ChatGPT 给你的高颜值，但移除包裹标签
    st.markdown("""
    <style>
    /* 页面背景与容器控制 */
    .stApp { background: #f5f7fb; }
    .block-container { 
        padding-top: 5rem !important; 
        max-width: 500px !important; 
    }

    /* 模拟卡片效果 (不使用 HTML 包裹组件，直接修改 Streamlit 容器样式) */
    div[data-testid="stVerticalBlock"] > div:has(div.brand-box) {
        background: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 12px 32px rgba(16, 24, 40, 0.12);
        border: 1px solid rgba(17, 24, 39, 0.08);
    }

    /* 按钮美化 */
    .stButton > button {
        width: 100% !important;
        height: 48px !important;
        background-color: #1f7a3f !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #166534 !important;
        transform: translateY(-1px);
    }

    /* 标题颜色与间距 */
    .brand-title { color: #1f7a3f; font-weight: 800; margin: 0; }
    .brand-sub { color: #6b7280; font-size: 14px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    # 2. 标题区 (使用一个带有 class 的 div 方便 CSS 定位)
    st.markdown("""
    <div class="brand-box">
        <h2 class="brand-title">📒 富邦日记账</h2>
        <p class="brand-sub">请输入管理员授权的凭证以继续</p>
    </div>
    """, unsafe_allow_html=True)

    # 3. 输入组件 (直接在 Python 逻辑中，不被外部 HTML div 包裹)
    username = st.text_input("账号", placeholder="请输入账号", key="user")
    password = st.text_input("密码", placeholder="请输入密码", type="password", key="pwd")
    
    st.write("") # 留空

    # 4. 登录逻辑
    if st.button("立即登录"):
        if username == "123" and password == "123":
            st.session_state.logged_in = True
            st.success("登录成功 ✅")
            st.rerun() # 立即触发页面刷新进入主程序
        else:
            st.error("❌ 账号或密码错误")

    st.markdown("---")
    st.caption("💡 忘记密码请联系系统管理员")
