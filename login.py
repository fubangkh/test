import streamlit as st

def show_login_page():
    # 1. 页面居中布局：[左1, 中2, 右1] 比例，让登录框锁死在屏幕中间
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        # 增加一些顶部间距
        st.write("<br><br><br>", unsafe_allow_html=True)
        
        # 使用带边框的容器，增加“卡片感”
        with st.container(border=True):
            st.markdown("### 🔒 富邦流水账")
            st.caption("请输入管理员授权的凭证以继续")
            st.divider()
            
            # 输入框
            user = st.text_input("用户名", placeholder="请输入账号")
            pw = st.text_input("密码", type="password", placeholder="请输入密码")
            
            # 2. 登录验证按钮
            if st.button("立即登录", type="primary", use_container_width=True):
                # --- 硬编码验证逻辑 ---
                # 你可以在这里修改你想要的用户名和密码
                if user == "123" and pw == "456":
                    st.session_state.logged_in = True
                    st.success("验证通过，正在加载系统...")
                    st.rerun() # 立即刷新，进入主程序
                else:
                    st.error("❌ 账号或密码不正确")
            
            st.markdown("---")
            st.caption("💡 忘记密码请联系系统管理员")
