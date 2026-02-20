import streamlit as st

def show_login_page():
    # 1. 样式注入：直接作用于全局，不包裹 HTML 标签
    st.markdown("""
        <style>
        /* 强制整体页面上移 */
        .block-container {
            padding-top: 2rem !important;
        }
        
        /* 按钮样式：深绿 */
        div.stButton > button {
            background-color: #1F883D !important;
            color: white !important;
            border-radius: 8px !important;
            height: 3.2rem !important;
            border: none !important;
            font-weight: bold !important;
        }
        div.stButton > button:hover {
            background-color: #66BB6A !important;
            box-shadow: 0 4px 12px rgba(31, 136, 61, 0.2) !important;
        }

        /* 修复图标大小差异 */
        div[data-testid="stTextInput"]:nth-of-type(2) input::placeholder {
            font-size: 1.25rem !important;
        }
        div[data-testid="stTextInput"]:nth-of-type(1) input::placeholder {
            font-size: 1.1rem !important;
        }

        /* 隐藏输入框标签 */
        div[data-testid="stTextInput"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    # 2. 页面居中布局
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # 顶部留白由 padding-top 控制，这里可以微调位置
        st.write("") 
        
        with st.container(border=True):
            # 标题居中且变绿
            st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <h2 style='color: #1F883D; margin: 0; display: flex; align-items: center; justify-content: center; gap: 10px;'>
                        <span style='font-size: 1.5rem;'>📒</span> 富邦日记账
                    </h2>
                    <p style='color: gray; margin-top: 5px; font-size: 0.9rem;'>请输入管理员授权的凭证以继续</p>
                </div>
            """, unsafe_allow_html=True)

            # 3. 输入区域 (移除所有可能导致冲突的 HTML 包裹)
            username = st.text_input("用户名", placeholder="👤请输入账号，测试账号123", key="user")
            password = st.text_input("密码", placeholder="🔒   请输入密码，测试密码123", type="password", key="pwd")
            
            st.write("") 

            # 4. 登录验证：这是最核心的点击触发区
            if st.button("立即登录", use_container_width=True):
                # 显式检查输入，增加反馈感
                if not username or not password:
                    st.warning("⚠️ 请先输入账号和密码")
                elif username == "123" and password == "123":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载...")
                    st.rerun() 
                else:
                    st.error("❌ 账号或密码不正确")

            st.divider()
            st.caption("💡 忘记密码请联系系统管理员")
