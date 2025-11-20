import streamlit as st

def show_header():
    if st.session_state.user:
        display_name = st.session_state.user.get('name') or st.session_state.user.get('email', '')
        st.markdown(f"""
            <div style='text-align: center; padding: 1rem; color: #64B5F6; font-size: 1.1em;'>
                👋 很高兴见到您，{display_name}
            </div>
        """, unsafe_allow_html=True)
