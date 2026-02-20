import streamlit as st

# --- 1. 初始化登录状态 ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    """验证用户名和密码"""
    if st.session_state.username == "admin" and st.session_state.password == "123456":
        st.session_state.logged_in = True
        st.rerun() # 登录成功后刷新页面
    else:
        st.error("❌ 用户名或密码错误")

# --- 2. 页面显示逻辑 ---
if not st.session_state.logged_in:
    # --- 登录界面：正中间布局 ---
    # 创建三列，比例为 1:2:1，中间那列最宽
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # 往下挪一点，看起来在正中
        with st.container(border=True):
            st.title("🔒 富邦流水账")
            st.text_input("用户名", key="username")
            st.text_input("密码", type="password", key="password")
            st.button("登录", type="primary", use_container_width=True, on_click=login)
            st.caption("提示：请输入管理员授权的账号访问")

else:
    # --- 3. 登录成功后的流水账模块 ---
    # 这里放你之前写的所有代码（时间看板、余额排行、流水明细等）
    st.sidebar.success("✅ 已登录：管理员")
    if st.sidebar.button("登出"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 下面接你原本的财务模块代码 ---
    # st.title("💰 现金流水账模块")
    # ... 原有逻辑 ...
